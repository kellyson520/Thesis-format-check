"""
Plugin: 页边距检查（Section 级别）
职责：检查文档各节的页边距是否符合配置规范。
"""
from __future__ import annotations
from typing import List
from domain.models import Issue, IssueCode, IssueSeverity, SectionNode
from domain.interfaces import ISectionPlugin
from use_cases.rule_config import PageSetupConfig


class PageMarginPlugin(ISectionPlugin):
    """检查页面边距（E001）。"""

    TOLERANCE_CM = 0.1  # 允许 0.1cm 的浮点误差

    def __init__(self, page_setup: PageSetupConfig):
        self.page_setup = page_setup

    def check_sections(self, sections: List[SectionNode]) -> List[Issue]:
        issues: List[Issue] = []
        if not sections:
            return issues
        first = sections[0]
        ps = self.page_setup
        checks = [
            ("top",    ps.top_margin_cm,    first.top_margin_cm),
            ("bottom", ps.bottom_margin_cm, first.bottom_margin_cm),
            ("left",   ps.left_margin_cm,   first.left_margin_cm),
            ("right",  ps.right_margin_cm,  first.right_margin_cm),
        ]
        for direction, expected, actual in checks:
            if expected is None or actual is None:
                continue
            if abs(expected - actual) > self.TOLERANCE_CM:
                issues.append(Issue(
                    para_index=-1,
                    issue_code=IssueCode.PAGE_MARGIN,
                    severity=IssueSeverity.ERROR,
                    context="页面边距 (Page Setup)",
                    message=(
                        f"页面边界设定错误：{direction} margin 为 {actual:.2f}cm，"
                        f"规范要求 {expected}cm"
                    ),
                ))
        return issues
