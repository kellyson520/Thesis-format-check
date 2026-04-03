"""
Plugin: 题注编号连续性检查（W004）
职责：检查图/表题注编号是否连续递增（不跳号、不重号）。

P0 重构（2026-04-03）：
  - 改用章内计数（context.chapter_figure_num / chapter_table_num）。
  - 章节边界由 ValidatorPipeline 的状态机负责重置，此 Plugin 只负责校验。
  - 同时保留全局兼容字段（last_figure_num / last_table_num）的检查路径，
    通过 use_chapter_numbering 标志切换（默认启用章内模式）。
"""
from __future__ import annotations
import re
from typing import List, TYPE_CHECKING
from pydantic import BaseModel
from domain.models import (
    Issue, IssueCode, IssueSeverity, ParagraphNode, RuleContext
)
from domain.interfaces import BaseRulePlugin
from use_cases.plugins.mixin import DeclarativeConfigMixin

if TYPE_CHECKING:
    from use_cases.rule_config import RuleConfig

# 题注正则：匹配 "图 1-2" / "图 2" / "表 3-1" 等格式
# P0 升级：同时支持 "图1-2"（章节号-序号）和 "图1"（全局序号）两种模式
_CAPTION_CHAPTER_RE = re.compile(r"(图|表)\s*(\d+)-(\d+)")   # 章节号-序号 格式
_CAPTION_GLOBAL_RE  = re.compile(r"(图|表)\s*(\d+)")          # 全局/简单序号 格式

class CaptionSeqConfig(BaseModel):
    """题注校验配置。"""
    enabled: bool = True


class CaptionSeqPlugin(BaseRulePlugin, DeclarativeConfigMixin):
    """
    检查图注和表注编号连续性（W004）。

    支持两种编号模式：
      - 章节号模式（P0 新增）：图 1-1, 图 1-2, ... 图 2-1（跨章时重置）
        使用 context.chapter_figure_num + context.current_chapter 验证
      - 全局模式（向后兼容）：图 1, 图 2, 图 3 ...
        使用 context.last_figure_num 验证

    自动检测：若题注文本含 "X-Y" 格式则走章节模式，否则走全局模式。
    """
    plugin_id = "caption_seq"
    config_model = CaptionSeqConfig

    def __init__(self, config: RuleConfig = None):
        self.config = config

    def check(self, node: ParagraphNode, context: RuleContext) -> List[Issue]:
        issues: List[Issue] = []
        if self.config and not self.config.caption_seq.enabled:
            return issues
        sn = node.style_name

        # 只处理题注样式段落
        if "Caption" not in sn and "题注" not in sn:
            return issues

        # ── 尝试章节号模式（图 X-Y）───────────────────────────────────────
        match_ch = _CAPTION_CHAPTER_RE.search(node.text)
        if match_ch:
            return self._check_chapter_mode(node, context, match_ch)

        # ── 回退到全局序号模式（图 X）────────────────────────────────────
        match_gl = _CAPTION_GLOBAL_RE.search(node.text)
        if match_gl:
            return self._check_global_mode(node, context, match_gl)

        return issues

    def _check_chapter_mode(
        self, node: ParagraphNode, context: RuleContext, match
    ) -> List[Issue]:
        """
        校验 "图 C-N" / "表 C-N" 格式（章节号-序号）。
        验证章节号是否与当前章节一致，以及序号是否连续。
        """
        issues: List[Issue] = []
        c_type  = match.group(1)
        chapter = int(match.group(2))
        seq     = int(match.group(3))

        # 章节号一致性检查
        if context.current_chapter > 0 and chapter != context.current_chapter:
            issues.append(Issue(
                id=node.index, para_index=node.index,
                issue_code=IssueCode.CAPTION_SEQ,
                severity=IssueSeverity.WARN,
                context=node.text,
                message=(
                    f"{c_type}题注章节号错误：当前第 {context.current_chapter} 章，"
                    f"但题注标记为第 {chapter} 章"
                ),
            ))

        # 章内序号连续性检查
        if c_type == "图":
            expected = context.chapter_figure_num + 1
            if seq != expected:
                issues.append(Issue(
                    id=node.index, para_index=node.index,
                    issue_code=IssueCode.CAPTION_SEQ,
                    severity=IssueSeverity.WARN,
                    context=node.text,
                    message=(
                        f"图题注编号不连续：当前为图 {chapter}-{seq}，"
                        f"但预期为 {chapter}-{expected}"
                    ),
                ))
        elif c_type == "表":
            expected = context.chapter_table_num + 1
            if seq != expected:
                issues.append(Issue(
                    id=node.index, para_index=node.index,
                    issue_code=IssueCode.CAPTION_SEQ,
                    severity=IssueSeverity.WARN,
                    context=node.text,
                    message=(
                        f"表题注编号不连续：当前为表 {chapter}-{seq}，"
                        f"但预期为 {chapter}-{expected}"
                    ),
                ))
        return issues

    def _check_global_mode(
        self, node: ParagraphNode, context: RuleContext, match
    ) -> List[Issue]:
        """
        校验全局连续编号（图 1, 图 2, ...）。
        使用 context.last_figure_num / last_table_num 追踪状态。
        """
        issues: List[Issue] = []
        c_type = match.group(1)
        num    = int(match.group(2))

        if c_type == "图":
            expected = context.last_figure_num + 1
            if num != expected:
                issues.append(Issue(
                    id=node.index, para_index=node.index,
                    issue_code=IssueCode.CAPTION_SEQ,
                    severity=IssueSeverity.WARN,
                    context=node.text,
                    message=(
                        f"图题注编号不连续：当前为图 {num}，"
                        f"但上一图为 {context.last_figure_num}"
                    ),
                ))
        elif c_type == "表":
            expected = context.last_table_num + 1
            if num != expected:
                issues.append(Issue(
                    id=node.index, para_index=node.index,
                    issue_code=IssueCode.CAPTION_SEQ,
                    severity=IssueSeverity.WARN,
                    context=node.text,
                    message=(
                        f"表题注编号不连续：当前为表 {num}，"
                        f"但上一表为 {context.last_table_num}"
                    ),
                ))
        return issues
