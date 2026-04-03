"""
Infrastructure Layer — DocxParser（纯翻译官）
职责：将 python-docx 的 XML DOM 翻译成 Domain Layer 的抽象文档模型（ADM）。
规则：
  - 不含任何业务逻辑判断（"正确"的概念属于 Plugin 层）。
  - 不调用 FastAPI / WebSocket。
  - 所有单位换算通过 UnitConverter 完成，禁止硬编码。
  - 实现 IParser 接口，use_cases 层对此文件一无所知。
"""
from __future__ import annotations
import docx
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from domain.models import (
    DocumentModel, ParagraphNode, TextRunNode, SectionNode
)
from domain.interfaces import IParser
from infrastructure.parsers.unit_converter import UnitConverter

# Word XML 命名空间
_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_QNAME_RFONTS = f"{{{_W_NS}}}rFonts"
_ATTR_EAST_ASIA = f"{{{_W_NS}}}eastAsia"
_ATTR_ASCII     = f"{{{_W_NS}}}ascii"

# 对齐映射（从 WD_PARAGRAPH_ALIGNMENT 到统一字符串）
_ALIGN_MAP = {
    WD_PARAGRAPH_ALIGNMENT.CENTER:  "center",
    WD_PARAGRAPH_ALIGNMENT.LEFT:    "left",
    WD_PARAGRAPH_ALIGNMENT.RIGHT:   "right",
    WD_PARAGRAPH_ALIGNMENT.JUSTIFY: "justify",
}


def _get_rfonts_attr(run, attr: str):
    """从 Run XML 中提取 rFonts 属性（如 eastAsia / ascii）。"""
    try:
        rPr = run._element.rPr
        if rPr is not None:
            rFonts = rPr.find(_QNAME_RFONTS)
            if rFonts is not None:
                return rFonts.get(attr)
    except AttributeError:
        pass
    return None


class DocxParser(IParser):
    """
    将 .docx 文件翻译为 DocumentModel（ADM）。
    实现 IParser 接口，use_cases 层通过接口调用，不直接依赖此类。
    """

    def __init__(self, filepath: str):
        self._filepath = filepath
        # python-docx 对象只在此类内部存在，不泄露到其他层
        self._doc = docx.Document(filepath)

    def parse(self) -> DocumentModel:
        """执行解析，返回纯 Python 数据模型（无 docx 对象）。"""
        paragraphs = self._parse_paragraphs()
        sections   = self._parse_sections()
        return DocumentModel(paragraphs=paragraphs, sections=sections)

    # ── 段落解析 ────────────────────────────────────────────────────────────

    def _parse_paragraphs(self):
        result = []
        for i, para in enumerate(self._doc.paragraphs):
            text = para.text.strip()
            if not text:
                continue

            style_name = para.style.name if para.style else "Normal"
            pf = para.paragraph_format

            # 单位换算统一交给 UnitConverter
            indent_chars = UnitConverter.pt_to_chars(
                pf.first_line_indent.pt if pf.first_line_indent else 0.0
            )
            line_spacing = UnitConverter.normalize_line_spacing(pf.line_spacing)
            space_before = pf.space_before.pt if pf.space_before else 0.0
            space_after  = pf.space_after.pt  if pf.space_after  else 0.0
            alignment    = _ALIGN_MAP.get(para.alignment)

            runs = self._parse_runs(para)

            result.append(ParagraphNode(
                index=i + 1,
                text=text,
                style_name=style_name,
                alignment=alignment,
                line_spacing=line_spacing,
                first_line_indent_chars=indent_chars,
                space_before_pt=space_before,
                space_after_pt=space_after,
                runs=runs,
            ))
        return result

    def _parse_runs(self, para):
        result = []
        for run in para.runs:
            if not run.text.strip():
                continue

            # 字体：优先读 Run 直接格式，回退到样式继承
            ascii_font = run.font.name or _get_rfonts_attr(run, _ATTR_ASCII)
            ea_font    = _get_rfonts_attr(run, _ATTR_EAST_ASIA)

            if ascii_font is None and para.style and para.style.font:
                ascii_font = para.style.font.name

            size_pt = None
            if run.font.size:
                size_pt = run.font.size.pt
            elif para.style and para.style.font and para.style.font.size:
                size_pt = para.style.font.size.pt

            result.append(TextRunNode(
                text=run.text,
                ascii_font=ascii_font,
                east_asia_font=ea_font,
                size_pt=size_pt,
                bold=run.bold if run.bold is not None else False,
            ))
        return result

    # ── 节解析（页边距）────────────────────────────────────────────────────

    def _parse_sections(self):
        result = []
        for s in self._doc.sections:
            result.append(SectionNode(
                top_margin_cm    = s.top_margin.cm    if s.top_margin    else None,
                bottom_margin_cm = s.bottom_margin.cm if s.bottom_margin else None,
                left_margin_cm   = s.left_margin.cm   if s.left_margin   else None,
                right_margin_cm  = s.right_margin.cm  if s.right_margin  else None,
            ))
        return result
