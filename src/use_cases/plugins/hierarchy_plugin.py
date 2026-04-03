"""
Plugin: 标题层级跳级检查（E008）+ 参考文献格式检查（W005）
职责：追踪标题层级连续性，检测跳级；检测参考文献区域的编号格式。

P0 重构（2026-04-03）：
  - 接受 StyleMapper 注入，消除 sn.startswith("Heading 1") 硬编码。
  - 通过 StyleMapper.get_heading_level(sn) 识别标题层级，支持自定义样式名。
  - 参考文献检查仍依赖 context.in_references（由状态机保证正确）。
"""
from __future__ import annotations
from typing import List, Optional
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

    P0 变更：接受 StyleMapper 注入，消除 startsWith 硬编码。
    """

    def __init__(self, validators_cfg: ValidatorsConfig, style_mapper=None):
        self.cfg = validators_cfg
        # style_mapper 是 ValidatorPipeline.StyleMapper 实例
        # 使用 Any 类型避免循环导入（use_cases 内部互相导入）
        self._mapper = style_mapper

    def _get_level(self, style_name: str) -> Optional[int]:
        """获取样式的标题层级，支持 StyleMapper 和内置规则的双重兜底。"""
        if self._mapper is not None:
            return self._mapper.get_heading_level(style_name)
        # 兜底：直接字符串解析（StyleMapper 未注入时的保护）
        sn = style_name
        if sn.startswith("Heading") or sn.startswith("标题"):
            level_str = sn.replace("Heading", "").replace("标题", "").strip()
            if level_str.isdigit():
                return int(level_str)
        return None

    def check(self, node: ParagraphNode, context: RuleContext) -> List[Issue]:
        issues: List[Issue] = []
        if not self.cfg.check_hierarchy:
            return issues

        current = self._get_level(node.style_name)
        if current is None:
            return issues

        last = context.last_heading_level

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
    （in_references 由 ValidatorPipeline 状态机驱动，已修复跨章节泄露问题）
    """

    def __init__(self, validators_cfg: ValidatorsConfig, style_mapper=None):
        self.cfg = validators_cfg
        self._mapper = style_mapper  # 保留签名一致性，此 Plugin 暂不使用

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
