"""
Plugin: 题注编号连续性检查（W004）
职责：检查图/表题注编号是否连续递增（不跳号、不重号）。
"""
from __future__ import annotations
import re
from typing import List
from domain.models import (
    Issue, IssueCode, IssueSeverity, ParagraphNode, RuleContext
)
from domain.interfaces import BaseRulePlugin

_CAPTION_RE = re.compile(r"(图|表)\s*(\d+)")


class CaptionSeqPlugin(BaseRulePlugin):
    """
    检查图注和表注编号连续性（W004）。
    通过 RuleContext 中的 last_figure_num / last_table_num 追踪状态。
    """

    def check(self, node: ParagraphNode, context: RuleContext) -> List[Issue]:
        issues: List[Issue] = []
        sn = node.style_name
        if "Caption" not in sn and "题注" not in sn:
            return issues

        match = _CAPTION_RE.search(node.text)
        if not match:
            return issues

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
