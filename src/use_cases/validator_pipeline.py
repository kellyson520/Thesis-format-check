"""
Use Cases Layer — ValidatorPipeline（验证执行引擎）
规则：此层不持有任何 Web 框架引用（无 fastapi / websocket）。
进度通过 Generator yield 向上层传递，上层（infrastructure/web）负责消费。
"""
from __future__ import annotations
from typing import Generator, List, Dict, Any, Optional
from domain.models import (
    DocumentModel, Issue, RuleContext, DocumentSection, ParagraphNode
)
from domain.interfaces import BaseRulePlugin, ISectionPlugin
from use_cases.rule_config import RuleConfig
from use_cases.plugins.font_plugin import FontPlugin
from use_cases.plugins.spacing_plugin import SpacingPlugin
from use_cases.plugins.hierarchy_plugin import HierarchyPlugin, ReferencesPlugin
from use_cases.plugins.caption_seq_plugin import CaptionSeqPlugin
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
            "type":     self.event_type,
            "progress": self.progress,
            "issues":   [i.model_dump() for i in self.issues],
            "total":    self.total,
            "current":  self.current,
        }


# ─── 上下文状态机（文档级别的可变状态，Plugin 只读） ─────────────────────────
def _update_context(
    context: RuleContext,
    node: ParagraphNode,
    issues: List[Issue],
) -> RuleContext:
    """
    根据当前段落内容更新共享上下文（由 Pipeline 负责，Plugin 不修改 context）。
    返回新的 RuleContext 对象（immutable-friendly 设计）。
    """
    new = context.model_copy()

    # 检测 "参考文献" 分水岭
    if node.text.replace(" ", "") == "参考文献":
        new.in_references = True
        new.current_section = DocumentSection.REFERENCES
        return new

    # 更新标题层级
    sn = node.style_name
    if sn.startswith("Heading") or sn.startswith("标题"):
        level_str = sn.replace("Heading", "").replace("标题", "").strip()
        if level_str.isdigit():
            new.last_heading_level = int(level_str)

    # 更新题注计数（从 issues 中读 CaptionSeq 结果前，直接扫描文本更稳定）
    import re
    match = re.search(r"(图|表)\s*(\d+)", node.text)
    if match and ("Caption" in sn or "题注" in sn):
        c, num = match.group(1), int(match.group(2))
        if c == "图":
            new.last_figure_num = num
        elif c == "表":
            new.last_table_num = num

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
        # 段落级 Plugin 列表（顺序即执行顺序）
        self._para_plugins: List[BaseRulePlugin] = [
            FontPlugin(config),
            SpacingPlugin(config),
            HierarchyPlugin(config.validators),
            ReferencesPlugin(config.validators),
            CaptionSeqPlugin(),
        ]
        # 节级 Plugin
        self._section_plugin: ISectionPlugin = PageMarginPlugin(config.page_setup)

    def run(
        self,
        doc_model: DocumentModel,
    ) -> Generator[ValidationEvent, None, List[Issue]]:
        """
        主验证 Generator。
        yield ValidationEvent 给上层，最终 return 全量 issues 列表。
        上层示例：
            all_issues = []
            for event in pipeline.run(doc):
                push_to_ws(event.to_dict())
                all_issues.extend(event.issues)
        """
        all_issues: List[Issue] = []

        # ── 0. 节级检查（页边距）────────────────────────────────────────────
        section_issues = self._section_plugin.check_sections(doc_model.sections)
        all_issues.extend(section_issues)
        if section_issues:
            yield ValidationEvent(
                event_type="section_issues",
                progress=0,
                issues=section_issues,
            )

        # ── 1. 段落级 Plugin 流水线 ─────────────────────────────────────────
        total = len(doc_model.paragraphs)
        context = RuleContext()

        for i, para in enumerate(doc_model.paragraphs):
            para_issues: List[Issue] = []
            for plugin in self._para_plugins:
                para_issues.extend(plugin.check(para, context))

            # 更新上下文状态机（只有 Pipeline 才修改 context）
            context = _update_context(context, para, para_issues)

            all_issues.extend(para_issues)
            progress = round((i + 1) / total * 100) if total else 100

            yield ValidationEvent(
                event_type="progress",
                progress=progress,
                issues=para_issues,
                total=total,
                current=i + 1,
            )

        # ── 2. 最终完成事件 ─────────────────────────────────────────────────
        yield ValidationEvent(
            event_type="complete",
            progress=100,
            issues=[],
            total=total,
            current=total,
        )

        return all_issues
