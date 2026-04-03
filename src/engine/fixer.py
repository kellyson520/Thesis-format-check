import io
import docx
from docx.shared import Pt, Cm
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.oxml.ns import qn

class DocumentFixer:
    def __init__(self, filepath, rules):
        self.filepath = filepath
        self.doc = docx.Document(filepath)
        self.rules = rules

    def _determine_rule(self, style_name):
        if style_name.startswith("Heading 1") or style_name.startswith("标题 1"):
            return self.rules.get('headings', {}).get('level_1')
        elif style_name.startswith("Heading 2") or style_name.startswith("标题 2"):
            return self.rules.get('headings', {}).get('level_2')
        elif style_name.startswith("Heading 3") or style_name.startswith("标题 3"):
            return self.rules.get('headings', {}).get('level_3')
        elif "Caption" in style_name or "题注" in style_name:
            if "Figure" in style_name or "图" in style_name:
                return self.rules.get('captions', {}).get('figure_caption')
            else:
                return self.rules.get('captions', {}).get('table_caption')
        else:
            return self.rules.get('paragraphs', {}).get('body_text')

    def _map_alignment_reverse(self, align_str):
        if align_str == "center":
            return WD_PARAGRAPH_ALIGNMENT.CENTER
        if align_str == "left":
            return WD_PARAGRAPH_ALIGNMENT.LEFT
        if align_str == "right":
            return WD_PARAGRAPH_ALIGNMENT.RIGHT
        if align_str == "justify":
            return WD_PARAGRAPH_ALIGNMENT.JUSTIFY
        return WD_PARAGRAPH_ALIGNMENT.LEFT

    def _set_east_asia_font(self, run, font_name):
        """强制设置中文字体（需操作底层 XML）"""
        run.font.name = font_name
        r = run._element
        rPr = r.get_or_add_rPr()
        rFonts = rPr.find(qn('w:rFonts'))
        if rFonts is None:
            rFonts = docx.oxml.OxmlElement('w:rFonts')
            rPr.append(rFonts)
        rFonts.set(qn('w:eastAsia'), font_name)

    def fix(self) -> bytes:
        doc_defaults = self.rules.get('document', {})
        default_ea_font = doc_defaults.get('default_font_east_asia', "宋体")
        default_ascii_font = doc_defaults.get('default_font_ascii', "Times New Roman")
        default_size = doc_defaults.get('default_font_size', 12)
        
        # 0. 修复页面布局 (Page Setup)
        page_setup = self.rules.get('page_setup', {})
        if page_setup:
            for section in self.doc.sections:
                if 'top_margin_cm' in page_setup and page_setup['top_margin_cm']: 
                    section.top_margin = Cm(page_setup['top_margin_cm'])
                if 'bottom_margin_cm' in page_setup and page_setup['bottom_margin_cm']: 
                    section.bottom_margin = Cm(page_setup['bottom_margin_cm'])
                if 'left_margin_cm' in page_setup and page_setup['left_margin_cm']: 
                    section.left_margin = Cm(page_setup['left_margin_cm'])
                if 'right_margin_cm' in page_setup and page_setup['right_margin_cm']: 
                    section.right_margin = Cm(page_setup['right_margin_cm'])

        for para in self.doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            style_name = para.style.name if para.style else "Normal"
            expected_rules = self._determine_rule(style_name)
            if not expected_rules:
                continue

            exp_ea_font = expected_rules.get('font_east_asia', default_ea_font)
            exp_ascii_font = expected_rules.get('font_ascii', default_ascii_font)
            exp_size = expected_rules.get('font_size', default_size)
            exp_bold = expected_rules.get('bold', False)
            exp_alignment = expected_rules.get('alignment')
            exp_indent = expected_rules.get('first_line_indent')
            exp_space_before = expected_rules.get('space_before')
            exp_space_after = expected_rules.get('space_after')
            exp_line_spacing = expected_rules.get('line_spacing', doc_defaults.get('default_line_spacing', 1.5))

            # 1. 修复段落对齐与间距
            if exp_alignment:
                para.alignment = self._map_alignment_reverse(exp_alignment)
            if exp_space_before is not None:
                para.paragraph_format.space_before = Pt(exp_space_before)
            if exp_space_after is not None:
                para.paragraph_format.space_after = Pt(exp_space_after)
            if exp_line_spacing is not None:
                para.paragraph_format.line_spacing = float(exp_line_spacing)
            
            # 2. 修复首行缩进 (近似算法: 缩进字数 * 字号点数)
            if exp_indent is not None and exp_indent > 0:
                # 假设标准的缩进单位可以用 Em 模拟，但 python-docx 常用 Pt/Cm。
                # 简单计算：缩进宽度 = 缩进字符数 * 字号 pt大小
                indent_pt = exp_indent * exp_size
                para.paragraph_format.first_line_indent = Pt(indent_pt)
            elif exp_indent == 0:
                para.paragraph_format.first_line_indent = 0

            # 3. 修复 Runs（字体、字号、字重）
            for run in para.runs:
                if not run.text.strip():
                    continue
                
                run_text = run.text.strip()
                has_chinese = any('\u4e00' <= char <= '\u9fff' for char in run_text)
                has_ascii = any(ord(char) < 128 for char in run_text)

                # 修复英文字体
                if has_ascii:
                    run.font.name = exp_ascii_font
                
                # 修复中文字体
                if has_chinese:
                    self._set_east_asia_font(run, exp_ea_font)
                
                # 修复字号和加粗
                if exp_size:
                    run.font.size = Pt(exp_size)
                if exp_bold is not None:
                    run.bold = exp_bold

        buf = io.BytesIO()
        self.doc.save(buf)
        buf.seek(0)
        return buf.read()
