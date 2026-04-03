"""
Infrastructure Layer — Word 报告生成器（批注注入 + 格式修复）
职责：
  1. AnnotationReporter — 将 Issue 列表以红色批注形式注入 Word 副本
  2. DocumentFixer      — 一键自动修复格式（覆盖段落样式）
规则：
  - 使用新 RuleConfig（Pydantic 强类型），不再使用裸字典
  - 接受 List[Issue] (domain.models.Issue)，不依赖 FastAPI
"""
from __future__ import annotations
import io
from typing import List

import docx
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.oxml.ns import qn

from domain.models import Issue
from use_cases.rule_config import RuleConfig


# ─── 对齐映射（字符串 → WD_PARAGRAPH_ALIGNMENT） ──────────────────────────────
_ALIGN_REVERSE = {
    "center":  WD_PARAGRAPH_ALIGNMENT.CENTER,
    "left":    WD_PARAGRAPH_ALIGNMENT.LEFT,
    "right":   WD_PARAGRAPH_ALIGNMENT.RIGHT,
    "justify": WD_PARAGRAPH_ALIGNMENT.JUSTIFY,
}


# ─── 1. 批注报告生成器 ────────────────────────────────────────────────────────

class AnnotationReporter:
    """
    将校验 Issue 以红色内联批注形式注入 Word 文档副本，返回字节流。
    接受 domain.models.Issue 列表（非裸字典）。
    """

    def __init__(self, source_path: str):
        self._source_path = source_path

    def generate(self, issues: List[Issue]) -> bytes:
        """
        生成带批注的 Word 文件。
        :param issues: ValidatorPipeline 产出的 Issue 列表
        :return: 修改后的 .docx 字节流
        """
        doc = docx.Document(self._source_path)

        # 按段落索引聚合 issues
        issue_map: dict[int, list[Issue]] = {}
        for issue in issues:
            issue_map.setdefault(issue.para_index, []).append(issue)

        for para_idx, para in enumerate(doc.paragraphs, start=1):
            if para_idx not in issue_map:
                continue
            msgs = " | ".join(
                f"[{i.severity.value}] {i.message}"
                for i in issue_map[para_idx]
            )
            run = para.add_run(f"  ⚠ {msgs}")
            run.font.color.rgb = RGBColor(0xFF, 0x00, 0x00)
            run.font.size = Pt(9)
            run.italic = True

        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        return buf.read()


# ─── 2. 格式修复器 ───────────────────────────────────────────────────────────

class DocumentFixer:
    """
    一键格式修复器（迁移自 engine/fixer.py）。
    使用 RuleConfig 强类型 API，不再依赖裸字典取值。
    """

    def __init__(self, filepath: str, config: RuleConfig):
        self._filepath = filepath
        self._config = config
        self._doc = docx.Document(filepath)

    @staticmethod
    def _set_east_asia_font(run, font_name: str) -> None:
        """强制设置中文字体（操作底层 XML）。"""
        run.font.name = font_name
        rPr = run._element.get_or_add_rPr()
        rFonts = rPr.find(qn("w:rFonts"))
        if rFonts is None:
            rFonts = docx.oxml.OxmlElement("w:rFonts")
            rPr.append(rFonts)
        rFonts.set(qn("w:eastAsia"), font_name)

    def fix(self) -> bytes:
        """执行全量格式修复，返回修复后的字节流。"""
        cfg = self._config
        doc_def = cfg.document

        # 0. 修复页面边距
        ps = cfg.page_setup
        for section in self._doc.sections:
            if ps.top_margin_cm    is not None: section.top_margin    = Cm(ps.top_margin_cm)
            if ps.bottom_margin_cm is not None: section.bottom_margin = Cm(ps.bottom_margin_cm)
            if ps.left_margin_cm   is not None: section.left_margin   = Cm(ps.left_margin_cm)
            if ps.right_margin_cm  is not None: section.right_margin  = Cm(ps.right_margin_cm)

        for para in self._doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            style_name = para.style.name if para.style else "Normal"
            rule = cfg.get_paragraph_rule(style_name)
            if rule is None:
                continue

            exp_ea_font    = rule.font_east_asia or doc_def.default_font_east_asia
            exp_ascii_font = rule.font_ascii     or doc_def.default_font_ascii
            exp_size       = rule.font_size      or doc_def.default_font_size
            exp_bold       = rule.bold
            exp_line_sp    = rule.line_spacing    or doc_def.default_line_spacing

            # 1. 段落级格式
            if rule.alignment:
                para.alignment = _ALIGN_REVERSE.get(rule.alignment, WD_PARAGRAPH_ALIGNMENT.LEFT)
            if rule.space_before is not None:
                para.paragraph_format.space_before = Pt(rule.space_before)
            if rule.space_after is not None:
                para.paragraph_format.space_after = Pt(rule.space_after)
            if exp_line_sp is not None:
                para.paragraph_format.line_spacing = float(exp_line_sp)

            # 2. 首行缩进
            if rule.first_line_indent is not None:
                if rule.first_line_indent > 0:
                    para.paragraph_format.first_line_indent = Pt(rule.first_line_indent * exp_size)
                else:
                    para.paragraph_format.first_line_indent = 0

            # 3. Run 级格式（字体 / 字号 / 字重）
            for run in para.runs:
                rt = run.text.strip()
                if not rt:
                    continue
                has_zh  = any("\u4e00" <= c <= "\u9fff" for c in rt)
                has_asc = any(c.isascii() and c.isalnum() for c in rt)

                if has_asc:
                    run.font.name = exp_ascii_font
                if has_zh:
                    self._set_east_asia_font(run, exp_ea_font)
                if exp_size:
                    run.font.size = Pt(exp_size)
                if exp_bold is not None:
                    run.bold = exp_bold

        buf = io.BytesIO()
        self._doc.save(buf)
        buf.seek(0)
        return buf.read()
