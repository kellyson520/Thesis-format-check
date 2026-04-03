"""
Plugin: 字体检查（中文字体 E002 / 英文字体 E003 / 字号 E004 / 字重 W001）
职责：对段落内每个 Run 检查四类字体属性是否符合规则。
"""
from __future__ import annotations
from typing import List
from domain.models import (
    Issue, IssueCode, IssueSeverity, ParagraphNode, RuleContext, Patch
)
from domain.interfaces import BaseRulePlugin
from use_cases.rule_config import RuleConfig, DocumentDefaults
from domain.utils.charset_detector import is_cjk_character, detect_text_charset


class FontPlugin(BaseRulePlugin):
    """
    检查字体族（中文/英文）、字号、字重（E002/E003/E004/W001）。
    每个 Run 独立判断，只对含有对应字符类型的片段报告错误。
    """

    def __init__(self, config: RuleConfig):
        self.config = config

    def check(self, node: ParagraphNode, context: RuleContext) -> List[Issue]:
        issues: List[Issue] = []
        rule = self.config.get_paragraph_rule(node.style_name)
        if rule is None:
            return issues

        doc = self.config.document
        exp_ea   = rule.font_east_asia or doc.default_font_east_asia
        exp_asc  = rule.font_ascii    or doc.default_font_ascii
        exp_size = rule.font_size     or doc.default_font_size
        exp_bold = rule.bold

        rule_name = rule.name or "默认正文"

        for run_idx, run in enumerate(node.runs):
            rt = run.text.strip()
            if not rt:
                continue
            # P1: 高精度字符集检测，过滤数字和空白噪声
            has_zh  = any(is_cjk_character(c) for c in rt)
            has_asc = any(c.isascii() and c.isalpha() for c in rt)

            # 中文字体
            if has_zh and run.east_asia_font and exp_ea not in run.east_asia_font:
                issues.append(Issue(
                    id=node.index, para_index=node.index,
                    issue_code=IssueCode.FONT_EAST_ASIA,
                    severity=IssueSeverity.ERROR,
                    context=rt,
                    message=(
                        f"中文字体不符：[{rule_name}] 使用了 '{run.east_asia_font}'，"
                        f"强制要求 '{exp_ea}'"
                    ),
                    suggested_patch=Patch(
                        target_type="run", para_index=node.index, run_index=run_idx,
                        attribute="east_asia_font", value=exp_ea
                    )
                ))
            # 英文字体
            elif has_asc and run.ascii_font and exp_asc not in run.ascii_font:
                issues.append(Issue(
                    id=node.index, para_index=node.index,
                    issue_code=IssueCode.FONT_ASCII,
                    severity=IssueSeverity.ERROR,
                    context=rt,
                    message=(
                        f"英文字体不符：[{rule_name}] 使用了 '{run.ascii_font}'，"
                        f"强制要求 '{exp_asc}'"
                    ),
                    suggested_patch=Patch(
                        target_type="run", para_index=node.index, run_index=run_idx,
                        attribute="ascii_font", value=exp_asc
                    )
                ))

            # 字号
            if run.size_pt is not None and abs(run.size_pt - exp_size) > 0.1:
                issues.append(Issue(
                    id=node.index, para_index=node.index,
                    issue_code=IssueCode.FONT_SIZE,
                    severity=IssueSeverity.ERROR,
                    context=rt,
                    message=(
                        f"字号越界：[{rule_name}] 为 {run.size_pt}pt，"
                        f"规范指标要求 {exp_size}pt"
                    ),
                    suggested_patch=Patch(
                        target_type="run", para_index=node.index, run_index=run_idx,
                        attribute="font_size", value=exp_size
                    )
                ))

            # 字重
            if exp_bold is not None and run.bold is not None and run.bold != exp_bold:
                issues.append(Issue(
                    id=node.index, para_index=node.index,
                    issue_code=IssueCode.BOLD,
                    severity=IssueSeverity.WARN,
                    context=rt,
                    message=(
                        f"字重粗细不符：当前片段处于违规"
                        f"{'加粗' if run.bold else '未加粗'}状态"
                    ),
                    suggested_patch=Patch(
                        target_type="run", para_index=node.index, run_index=run_idx,
                        attribute="bold", value=exp_bold
                    )
                ))

        return issues
