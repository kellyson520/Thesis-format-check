"""
Plugin: 分页排版控制（E009 孤行控制 / E010 与下段同页）
职责：检查标题是否开启了“与下段同页”，正文是否开启了“孤行控制”。
"""
from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field
from domain.models import (
    Issue, IssueCode, IssueSeverity, ParagraphNode, RuleContext, Patch
)
from domain.interfaces import BaseRulePlugin
from use_cases.plugins.mixin import DeclarativeConfigMixin
from use_cases.rule_config import RuleConfig


class PaginationConfig(BaseModel):
    """高级排版规则 (P2 新增)"""
    enabled: bool = True                   # Master Toggle for the entire plugin
    widow_control: bool = True             # 是否强制开启孤行控制
    keep_with_next_styles: List[str] = Field(default_factory=lambda: ["Heading 1", "Heading 2", "Heading 3", "标题 1", "标题 2", "标题 3"])


class PaginationPlugin(BaseRulePlugin, DeclarativeConfigMixin):
    """
    高级分页排版特性检查器。
    """
    plugin_id = "pagination"
    config_model = PaginationConfig

    def __init__(self, config: RuleConfig):
        self.config = config

    def check(self, node: ParagraphNode, context: RuleContext) -> List[Issue]:
        issues: List[Issue] = []
        pag_rule = self.config.pagination
        if not pag_rule.enabled:
            return issues
        
        # 1. 孤行控制检查 (Widow Control)
        # 通常正文段落应当开启孤行控制以防止出现文字孤岛
        if pag_rule.widow_control and node.widow_control is False:
            # 仅对正文段落进行该项 Warn（标题通常自带有 skip）
            if "Heading" not in node.style_name and "标题" not in node.style_name:
                issues.append(Issue(
                    id=node.index, para_index=node.index,
                    issue_code=IssueCode.PAGINATION_WIDOW,
                    severity=IssueSeverity.WARN,
                    context=node.text[:20],
                    message=f"排版细节：段落未开启“孤行控制”，可能导致页面底部出现孤立行。",
                    suggested_patch=Patch(
                        target_type="paragraph", para_index=node.index,
                        attribute="widow_control", value=True
                    )
                ))

        # 2. 与下段同页检查 (Keep with Next)
        # 论文规范通常要求所有级别的标题必须开启“与下段同页”，禁止标题出现在页末
        is_heading = any(h in node.style_name for h in pag_rule.keep_with_next_styles)
        if is_heading and node.keep_with_next is False:
            issues.append(Issue(
                id=node.index, para_index=node.index,
                issue_code=IssueCode.PAGINATION_KWN,
                severity=IssueSeverity.ERROR,
                context=node.text[:20],
                message=f"标题排版错误：[{node.style_name}] 未开启“与下段同页”，可能导致标题与正文断开。",
                suggested_patch=Patch(
                    target_type="paragraph", para_index=node.index,
                    attribute="keep_with_next", value=True
                )
            ))

        return issues
