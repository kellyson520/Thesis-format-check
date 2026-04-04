"""
Use Cases Layer — ValidatorPipeline（验证执行引擎）
规则：此层不持有任何 Web 框架引用（无 fastapi / websocket）。
进度通过 Generator yield 向上层传递，上层（infrastructure/web）负责消费。

P0 重构（2026-04-03）：
  - 引入独立 StyleMapper 模块，解耦样式名硬编码。
  - 文档区域状态机完整实现（含参考文献退出边）。
  - ChapterCounter：一级标题推进章节号，章内题注计数器随章重置。
"""
from __future__ import annotations
import re
from typing import Generator, List, Dict, Any, Optional
from domain.models import (
    DocumentModel, Issue, RuleContext, DocumentSection, ParagraphNode
)
from domain.interfaces import BaseRulePlugin, ISectionPlugin
from use_cases.rule_config import RuleConfig
from use_cases.style_mapper import StyleMapper
from use_cases.plugins.font_plugin import FontPlugin
from use_cases.plugins.spacing_plugin import SpacingPlugin
from use_cases.plugins.hierarchy_plugin import HierarchyPlugin, ReferencesPlugin
from use_cases.plugins.caption_seq_plugin import CaptionSeqPlugin
from use_cases.plugins.pagination_plugin import PaginationPlugin
from use_cases.plugins.page_margin_plugin import PageMarginPlugin


# ─── 进度事件类型 ────────────────────────────────────────────────────────────
class ValidationEvent:
    """Pipeline yield 的事件单元，外层通过类型字段区分处理方式。"""
    __slots__ = ("event_type", "progress", "issues", "total", "current")

    def __init__(
        self,
        event_type: str,          # "progress" | "complete" | "section_issues"
        progress: int = 0,
        issues: Optional[List[Issue]] = None,
        total: int = 0,
        current: int = 0,
    ):
        self.event_type = event_type
        self.progress   = progress
        self.issues     = issues or []
        self.total      = total
        self.current    = current

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,  # 兼容前端 event_type 指向 (App.vue:115)
            "type":       self.event_type,  # 原始 type 字段
            "progress":   self.progress,
            "issues":     [self._issue_to_dict(i) for i in self.issues],
            "total":      self.total,
            "current":    self.current,
        }

    def _issue_to_dict(self, issue: Issue) -> Dict[str, Any]:
        """将 Issue 转换为前端兼容的字典格式（含 type 映射）。"""
        d = issue.model_dump()
        d["type"] = issue.severity.value      # 前端预期 iss.type (App.vue:545)
        d["issue_code"] = issue.issue_code.value
        if issue.suggested_patch:
            d["fixable"] = True
        return d


# ─── 文档区域状态机（内部辅助函数） ──────────────────────────────────────────
_CAPTION_RE = re.compile(r"(图|表)\s*(\d+)")


def _update_context(
    context: RuleContext,
    node: ParagraphNode,
    mapper: StyleMapper,
) -> RuleContext:
    """
    根据当前段落内容更新共享上下文（由 Pipeline 负责，Plugin 只读 context）。

    状态机转移规则（P0 完整实现）：
      1. 遇"参考文献"一级标题 → 进入 REFERENCES
      2. 在 REFERENCES 状态遇到下一个一级标题 → 退出到 APPENDIX（消除状态泄露）
      3. 在 BODY 状态遇到一级标题 → 推进章节号，重置章内题注计数器
      4. 更新 last_heading_level（供 HierarchyPlugin 跳级检查）
      5. 更新章内+全局题注计数（供 CaptionSeqPlugin 使用）

    设计原则：返回新 RuleContext 对象（immutable-friendly），原对象不修改。
    """
    new = context.model_copy()
    sn = node.style_name
    heading_level = mapper.get_heading_level(sn)

    # ── 状态机转移 ──────────────────────────────────────────────────────────
    if heading_level == 1:
        if mapper.is_references_heading(sn, node.text):
            # → 进入参考文献区域（清晰的进入边）
            new.current_section = DocumentSection.REFERENCES

        elif context.current_section == DocumentSection.REFERENCES:
            # 在参考文献区域遇到下一个一级标题 → 退出（致谢/附录等）
            # P0 核心修复：原代码永不退出 REFERENCES，造成全篇误报
            new.current_section = DocumentSection.APPENDIX

        elif context.current_section == DocumentSection.BODY:
            # 正文中遇到一级标题 → 推进章节号，重置章内题注计数
            new.current_chapter    = context.current_chapter + 1
            new.chapter_figure_num = 0
            new.chapter_table_num  = 0

    # ── 标题层级追踪（HierarchyPlugin 依赖） ───────────────────────────────
    if heading_level is not None:
        new.last_heading_level = heading_level

    # ── 题注计数更新（章内 + 全局） ──────────────────────────────────────────
    match = _CAPTION_RE.search(node.text)
    if match and ("Caption" in sn or "题注" in sn):
        c_type = match.group(1)
        num = int(match.group(2))
        if c_type == "图":
            new.chapter_figure_num = num      # 章内（CaptionSeqPlugin P0 使用）
            new.last_figure_num    = num      # 全局兼容
        elif c_type == "表":
            new.chapter_table_num  = num
            new.last_table_num     = num

    return new


# ─── ValidatorPipeline ───────────────────────────────────────────────────────
class ValidatorPipeline:
    """
    验证执行引擎（Generator 模式）。
    组装所有 Plugin，逐段产出进度事件。
    外层（FastAPI / PyWebView）通过消费此 Generator 获取实时进度。
    """

    def __init__(self, config: RuleConfig):
        self.config = config

        # StyleMapper：从 rules.yaml 读取自定义映射
        custom_mapping: Optional[Dict[str, int]] = getattr(config, "style_mapping", None)
        self._style_mapper = StyleMapper(custom_mapping)

        # ── 插件生命周期管理（可扩展架构） ────────────────────────────────────
        # 将实例创建逻辑抽象为注册表模式（P3 优化）
        self._para_plugins: List[BaseRulePlugin] = self._init_para_plugins()
        self._section_plugins: List[ISectionPlugin] = self._init_section_plugins()

    def _init_para_plugins(self) -> List[BaseRulePlugin]:
        """初始化段落级插件。"""
        # 后续可通过 entry_points 或动态路径加载
        return [
            FontPlugin(self.config),
            SpacingPlugin(self.config),
            PaginationPlugin(self.config),
            HierarchyPlugin(self.config, self._style_mapper),
            ReferencesPlugin(self.config, self._style_mapper),
            CaptionSeqPlugin(self.config),
        ]

    def _init_section_plugins(self) -> List[ISectionPlugin]:
        """初始化节级插件。"""
        return [
            PageMarginPlugin(self.config)
        ]

    def run(
        self,
        doc_model: DocumentModel,
    ) -> Generator[ValidationEvent, None, List[Issue]]:
        """
        主验证 Generator。
        yield ValidationEvent 给上层，最终 return 全量 issues 列表。

        上层消费示例：
            all_issues = []
            for event in pipeline.run(doc):
                push_to_ws(event.to_dict())
                all_issues.extend(event.issues)
        """
        all_issues: List[Issue] = []

        # ── 0. 节级检查（页边距等）──────────────────────────────────────────
        for plugin in self._section_plugins:
            s_issues = plugin.check_sections(doc_model.sections)
            all_issues.extend(s_issues)
            if s_issues:
                yield ValidationEvent(
                    event_type="section_issues",
                    issues=s_issues,
                )

        # ── 1. 段落级 Plugin 流水线 ─────────────────────────────────────────
        total = len(doc_model.paragraphs)
        context = RuleContext()
        last_progress = -1

        for i, para in enumerate(doc_model.paragraphs):
            para_issues: List[Issue] = []
            for plugin in self._para_plugins:
                para_issues.extend(plugin.check(para, context))

            # 更新上下文状态机
            context = _update_context(context, para, self._style_mapper)
            all_issues.extend(para_issues)
            
            # 性能优化：节流上报（只有进度变化或发现问题时才推送）
            progress = round((i + 1) / total * 100) if total else 100
            if para_issues or progress != last_progress or i == total - 1:
                last_progress = progress
                yield ValidationEvent(
                    event_type="progress",
                    progress=progress,
                    issues=para_issues,
                    total=total,
                    current=i + 1,
                )

        # ── 2. 最终完成事件 ─────────────────────────────────────────────────
        yield ValidationEvent(
            event_type="done",  # 前端预期 done 以便隐藏 loading (App.vue:122)
            progress=100,
            issues=[],
            total=total,
            current=total,
        )

        return all_issues
