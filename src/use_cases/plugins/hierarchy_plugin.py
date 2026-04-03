"""
Plugin: 标题层级跳级检查（E008）+ 参考文献格式检查（W005）
职责：追踪标题层级连续性，检测跳级；检测参考文献区域的编号格式。
自带内部状态（通过 context 共享，Plugin 自身不维护全局变量）。
"""
from __future__ import annotations
from typing import List
from domain.models import (
    Issue, IssueCode, IssueSeverity, ParagraphNode, RuleContext,
    DocumentSection
)
from domain.interfaces import BaseRulePlugin
from use_cases.rule_config import ValidatorsConfig


class HierarchyPlugin(BaseRulePlugin):
    """
    检查标题层级是否跳级（E008）。
    不维护自身状态，通过 context.last_heading_level 获取上一层级。
    注意：此 Plugin 还负责更新 context（由 ValidatorPipeline 在调用后同步）。
    """

    def __init__(self, validators_cfg: ValidatorsConfig):
        self.cfg = validators_cfg

    def check(self, node: ParagraphNode, context: RuleContext) -> List[Issue]:
        issues: List[Issue] = []
        if not self.cfg.check_hierarchy:
            return issues

        sn = node.style_name
        if not (sn.startswith("Heading") or sn.startswith("标题")):
            return issues

        level_str = sn.replace("Heading", "").replace("标题", "").strip()
        if not level_str.isdigit():
            return issues

        current = int(level_str)
        last    = context.last_heading_level

        if current > last + 1 and current != 1:
            issues.append(Issue(
                id=node.index, para_index=node.index,
                issue_code=IssueCode.HEADING_SKIP,
                severity=IssueSeverity.ERROR,
                context=node.text,
                message=(
                    f"标题层级错误：从标题 {last} 违规跳级至标题 {current}"
                ),
            ))
        return issues


class ReferencesPlugin(BaseRulePlugin):
    """
    检查参考文献格式（W005）。
    依赖 context.in_references 判断当前是否在参考文献区域。
    """

    def __init__(self, validators_cfg: ValidatorsConfig):
        self.cfg = validators_cfg

    def check(self, node: ParagraphNode, context: RuleContext) -> List[Issue]:
        issues: List[Issue] = []
        if not self.cfg.check_gb7714:
            return issues
        if not context.in_references:
            return issues
        text = node.text.strip()
        if not text:
            return issues
        if not text.startswith("["):
            issues.append(Issue(
                id=node.index, para_index=node.index,
                issue_code=IssueCode.REF_FORMAT,
                severity=IssueSeverity.WARN,
                context=text[:25] + "...",
                message="参考文献格式：检测到正文未使用 [1] 开头的标准 GB/T 7714 格式编号",
            ))
        return issues
