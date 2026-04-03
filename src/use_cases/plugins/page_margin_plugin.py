"""
Plugin: 页边距检查（Section 级别）
职责：检查文档各节的页边距是否符合配置规范。
"""
from __future__ import annotations
from typing import List
from typing import List, Optional
from pydantic import BaseModel
from domain.models import Issue, IssueCode, IssueSeverity, SectionNode, Patch
from domain.interfaces import ISectionPlugin
from use_cases.plugins.mixin import DeclarativeConfigMixin


class PageSetupConfig(BaseModel):
    top_margin_cm: Optional[float] = None
    bottom_margin_cm: Optional[float] = None
    left_margin_cm: Optional[float] = None
    right_margin_cm: Optional[float] = None


class PageMarginPlugin(ISectionPlugin, DeclarativeConfigMixin):
    """检查页面边距（E001）。"""
    plugin_id = "page_setup"
    config_model = PageSetupConfig

    TOLERANCE_CM = 0.1  # 允许 0.1cm 的浮点误差

    def __init__(self, config: RuleConfig):
        self.config = config

    def check_sections(self, sections: List[SectionNode]) -> List[Issue]:
        issues: List[Issue] = []
        if not sections:
            return issues
        first = sections[0]
        ps = self.config.page_setup
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
                    suggested_patch=Patch(
                        target_type="section", para_index=1,
                        attribute=f"{direction}_margin_cm", value=expected
                    )
                ))
        return issues
