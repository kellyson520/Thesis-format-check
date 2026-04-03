import docx
from docx.shared import Pt, Length
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

class DocxParser:
    def __init__(self, filepath):
        self.doc = docx.Document(filepath)

    def _get_east_asia_font(self, run):
        """解析 Word XML 获取底层定义的中文字体"""
        try:
            rPr = run._element.rPr
            if rPr is not None:
                rFonts = rPr.find("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rFonts")
                if rFonts is not None:
                    return rFonts.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}eastAsia")
        except AttributeError:
            pass
        return None

    def _get_ascii_font(self, run):
        """解析 Word XML 获取底层定义的英文字体"""
        try:
            rPr = run._element.rPr
            if rPr is not None:
                rFonts = rPr.find("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rFonts")
                if rFonts is not None:
                    return rFonts.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}ascii")
        except AttributeError:
            pass
        return None

    def parse(self):
        elements = []
        for i, para in enumerate(self.doc.paragraphs):
            text = para.text.strip()
            if not text:
                continue

            style_name = para.style.name if para.style else "Normal"
            
            # Paragraph level formats
            alignment = para.alignment
            line_spacing = para.paragraph_format.line_spacing
            first_line_indent = para.paragraph_format.first_line_indent
            space_before = para.paragraph_format.space_before
            space_after = para.paragraph_format.space_after

            # Convert indent Length object to approximate character count (Assumes roughly 12pt per char)
            indent_chars = 0
            if first_line_indent and hasattr(first_line_indent, 'pt'):
                indent_chars = round(first_line_indent.pt / 12)

            runs_data = []
            for run in para.runs:
                if not run.text.strip():
                    continue
                
                # Check directly applied run formatting
                run_ascii_font = run.font.name or self._get_ascii_font(run)
                run_east_asia_font = self._get_east_asia_font(run)
                run_size = run.font.size.pt if run.font.size else None
                run_is_bold = run.bold if run.bold is not None else False

                # Format Inheritance: Fallback to style defaults if run formatting is None
                if run_ascii_font is None and para.style and para.style.font:
                    run_ascii_font = para.style.font.name
                if run_size is None and para.style and para.style.font and para.style.font.size:
                    run_size = para.style.font.size.pt

                runs_data.append({
                    "text": run.text,
                    "ascii_font": run_ascii_font,
                    "east_asia_font": run_east_asia_font,
                    "size": run_size,
                    "bold": run_is_bold
                })

            elements.append({
                "type": "paragraph",
                "text": text,
                "index": i + 1,
                "style_name": style_name,
                "alignment": alignment,
                "line_spacing": line_spacing,
                "first_line_indent_chars": indent_chars,
                "space_before_pt": space_before.pt if space_before else 0,
                "space_after_pt": space_after.pt if space_after else 0,
                "runs": runs_data
            })
        
        sections_data = []
        for s in self.doc.sections:
            sections_data.append({
                "top_margin_cm": s.top_margin.cm if s.top_margin else None,
                "bottom_margin_cm": s.bottom_margin.cm if s.bottom_margin else None,
                "left_margin_cm": s.left_margin.cm if s.left_margin else None,
                "right_margin_cm": s.right_margin.cm if s.right_margin else None,
            })

        return {"elements": elements, "sections": sections_data}
