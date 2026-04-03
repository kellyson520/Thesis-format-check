"""
Plugin: 间距与缩进检查（E005/E006/E007/W002/W003）
职责：检查段前间距、段后间距、行距、对齐方式、首行缩进。
"""
from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING
from pydantic import BaseModel
from domain.models import (
    Issue, IssueCode, IssueSeverity, ParagraphNode, RuleContext, Patch
)
from domain.interfaces import BaseRulePlugin
from use_cases.plugins.mixin import DeclarativeConfigMixin

if TYPE_CHECKING:
    from use_cases.rule_config import RuleConfig


def _ctx(text: str, max_len: int = 25) -> str:
    return text[:max_len] + "..." if len(text) > max_len else text


class SpacingConfig(BaseModel):
    """间距与缩进校验所需参数。"""
    enabled: bool = True
    alignment: Optional[str] = None            # "left" / "center" / "right" / "justify"
    first_line_indent: Optional[float] = None  # 单位：字符数
    line_spacing: Optional[float] = None       # 倍数 (e.g. 1.5) 或 pt
    space_before: Optional[float] = None       # 单位：pt
    space_after: Optional[float] = None        # 单位：pt


class SpacingPlugin(BaseRulePlugin, DeclarativeConfigMixin):
    """检查段前/段后间距（E005/E006）、行距（E007）、对齐（W002）、首行缩进（W003）。"""
    plugin_id = "spacing"
    config_model = SpacingConfig

    SPACING_TOL = 0.5   # pt 容差
    LS_TOL      = 0.1   # 行距容差

    def __init__(self, config: RuleConfig):
        self.config = config

    def check(self, node: ParagraphNode, context: RuleContext) -> List[Issue]:
        issues: List[Issue] = []
        if not self.config.spacing.enabled:
            return issues
        rule = self.config.get_paragraph_rule(node.style_name)
        if rule is None:
            return issues

        rule_name = rule.name or "默认正文"
        txt = _ctx(node.text)

        # 段前间距
        if rule.space_before is not None:
            if abs(node.space_before_pt - rule.space_before) > self.SPACING_TOL:
                issues.append(Issue(
                    id=node.index, para_index=node.index,
                    issue_code=IssueCode.SPACE_BEFORE,
                    severity=IssueSeverity.ERROR,
                    context=txt,
                    message=(
                        f"段前间距错误：[{rule_name}] 当前 {node.space_before_pt}pt，"
                        f"规范要求 {rule.space_before}pt"
                    ),
                    suggested_patch=Patch(
                        target_type="paragraph", para_index=node.index,
                        attribute="space_before_pt", value=rule.space_before
                    )
                ))

        # 段后间距
        if rule.space_after is not None:
            if abs(node.space_after_pt - rule.space_after) > self.SPACING_TOL:
                issues.append(Issue(
                    id=node.index, para_index=node.index,
                    issue_code=IssueCode.SPACE_AFTER,
                    severity=IssueSeverity.ERROR,
                    context=txt,
                    message=(
                        f"段后间距错误：[{rule_name}] 当前 {node.space_after_pt}pt，"
                        f"规范要求 {rule.space_after}pt"
                    ),
                    suggested_patch=Patch(
                        target_type="paragraph", para_index=node.index,
                        attribute="space_after_pt", value=rule.space_after
                    )
                ))

        # 行距
        if rule.line_spacing is not None and node.line_spacing is not None:
            if abs(node.line_spacing - rule.line_spacing) > self.LS_TOL:
                issues.append(Issue(
                    id=node.index, para_index=node.index,
                    issue_code=IssueCode.LINE_SPACING,
                    severity=IssueSeverity.ERROR,
                    context=txt,
                    message=(
                        f"行距错误：[{rule_name}] 检测到 {node.line_spacing}，"
                        f"规范要求 {rule.line_spacing}"
                    ),
                    suggested_patch=Patch(
                        target_type="paragraph", para_index=node.index,
                        attribute="line_spacing", value=rule.line_spacing
                    )
                ))

        # 对齐方式
        if rule.alignment and node.alignment:
            if node.alignment != rule.alignment:
                issues.append(Issue(
                    id=node.index, para_index=node.index,
                    issue_code=IssueCode.ALIGNMENT,
                    severity=IssueSeverity.WARN,
                    context=txt,
                    message=(
                        f"段落对齐偏差：排版方向检测为 '{node.alignment}'，"
                        f"应更正为 '{rule.alignment}'"
                    ),
                    suggested_patch=Patch(
                        target_type="paragraph", para_index=node.index,
                        attribute="alignment", value=rule.alignment
                    )
                ))

        # 首行缩进
        if rule.first_line_indent is not None:
            if node.first_line_indent_chars < rule.first_line_indent:
                issues.append(Issue(
                    id=node.index, para_index=node.index,
                    issue_code=IssueCode.INDENT,
                    severity=IssueSeverity.WARN,
                    context=txt,
                    message=(
                        f"首行缩进约束：段首缩进当前约 {node.first_line_indent_chars:.1f} 字符，"
                        f"未能达到 {rule.first_line_indent} 字符缩进阈值"
                    ),
                    suggested_patch=Patch(
                        target_type="paragraph", para_index=node.index,
                        attribute="first_line_indent_chars", value=rule.first_line_indent
                    )
                ))

        return issues
