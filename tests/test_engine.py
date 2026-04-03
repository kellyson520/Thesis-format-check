import os
import sys
from unittest.mock import MagicMock, patch

# Add src to Python Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Since we don't have local environments, we mock the `docx` dependency before importing modules
# that heavily rely on it, simulating the objects.
sys.modules['docx'] = MagicMock()
sys.modules['docx.shared'] = MagicMock()
sys.modules['docx.enum.text'] = MagicMock()
sys.modules['docx.oxml.ns'] = MagicMock()

from engine.validator import Validator
from engine.fixer import DocumentFixer
from engine.docx_parser import DocxParser

# ==============================================================================
# Mock Rules Definitions
# ==============================================================================

STRICT_RULES = {
    "page_setup": {
        "top_margin_cm": 2.54,
        "bottom_margin_cm": 2.54,
        "left_margin_cm": 3.18,
        "right_margin_cm": 3.18
    },
    "validators": {
        "check_hierarchy": True,
        "check_gb7714": True
    },
    "document": {
        "default_font_east_asia": "宋体",
        "default_font_ascii": "Times New Roman",
        "default_font_size": 12,
        "default_line_spacing": 1.5
    },
    "headings": {
        "level_1": {"name": "Heading 1", "font_size": 16, "font_east_asia": "黑体", "alignment": "center"},
        "level_3": {"name": "Heading 3", "font_size": 12, "font_east_asia": "黑体", "alignment": "left"}
    },
    "paragraphs": {
        "body_text": {"name": "Normal", "font_size": 12, "font_east_asia": "宋体", "first_line_indent": 2} # approx 24pt
    },
    "captions": {
        "figure_caption": {"name": "Caption", "alignment": "center"}
    }
}

# ==============================================================================
# Mock Helpers
# ==============================================================================

def create_mock_docx():
    """Create a fully mocked python-docx Document tree that simulates anomalies."""
    mock_doc = MagicMock()

    # 1. Mock Sections (for Page Setup rules checking)
    mock_section = MagicMock()
    mock_section.top_margin.cm = 1.0     # Should be 2.54
    mock_section.bottom_margin.cm = 2.54 # OK
    mock_section.left_margin.cm = 1.0    # Should be 3.18
    mock_section.right_margin.cm = 3.18  # OK
    mock_doc.sections = [mock_section]

    def create_para(text, style_name, alignment=None, runs_data=None):
        p = MagicMock()
        p.text = text
        p.style.name = style_name
        p.alignment = alignment
        
        # Paragraph format
        p.paragraph_format.first_line_indent = None
        p.paragraph_format.space_before = None
        p.paragraph_format.space_after = None
        p.paragraph_format.line_spacing = 1.0 # Should be 1.5

        if runs_data:
            mock_runs = []
            for run_text, font_ascii, font_ea, size in runs_data:
                run = MagicMock()
                run.text = run_text
                run.font.name = font_ascii
                run.font.size.pt = size
                # Custom mock for east asia
                run._element.rPr.find.return_value.get.return_value = font_ea
                run.bold = False
                mock_runs.append(run)
            p.runs = mock_runs
        else:
            p.runs = []
        return p

    # 2. Mock Paragraphs (Structure and Styles anomalies)
    mock_doc.paragraphs = [
        # H1
        create_para("第一章 绪论 (Heading 1)", "Heading 1", runs_data=[
            ("第一章", "Arial", "微软雅黑", 14) # Should be Times New Roman, 黑体, 16 
        ]),
        # H3 (Hierarchy Jump Exception!)
        create_para("1.1.1 违规的三级子标题", "Heading 3", runs_data=[
            ("违规", "Times New Roman", "宋体", 12) # Should be 黑体
        ]),
        # Broken Body Text without indent
        create_para("正文毫无缩进且乱排。", "Normal", runs_data=[
            ("正文", "Arial", "黑体", 10)
        ]),
        # Broken sequence Caption
        create_para("图 2 图名跳号", "Caption", runs_data=[("图 2", "SimHei", "黑体", 12)]),
        
        # References Section
        create_para("参考文献", "Heading 1"),
        create_para("作者. 无国标编号的假文献 [J]. Nature, 2026.", "Normal") # Missing [1]
    ]
    return mock_doc

# ==============================================================================
# Tests
# ==============================================================================

def test_validation_detects_all_anomalies():
    mock_doc = create_mock_docx()

    # Pass the mock to parser using monkeypatch or patch
    with patch("engine.docx_parser.docx.Document", return_value=mock_doc):
        parser = DocxParser("fake.docx")
        parsed_data = parser.parse()

    validator = Validator(STRICT_RULES)
    issues = validator.validate(parsed_data)

    msgs = " | ".join(i['message'] for i in issues)

    # Assert Page Setup checks
    assert "页面边界" in msgs, "Should detect bad top/left margins"
    
    # Assert Hierarchy jumper
    assert "跳级" in msgs, "Should detect jump from H1 to H3"

    # Assert Caption sequences
    assert "不连续" in msgs, "Should detect Figure 2 missing Figure 1"

    # Assert GB7714
    assert "GB/T 7714" in msgs, "Should detect missing bracketed numbers in references"

def test_auto_fixer_applies_styles_correctly():
    mock_doc = create_mock_docx()
    # Mock Pt and Cm conversions that Fixer uses
    with patch("engine.fixer.docx.Document", return_value=mock_doc), \
         patch("engine.fixer.Pt", side_effect=lambda x: f"Pt({x})"), \
         patch("engine.fixer.Cm", side_effect=lambda x: f"Cm({x})"):
        
        fixer = DocumentFixer("fake.docx", STRICT_RULES)
        # Prevent actually saving to buffer
        fixer.doc.save = MagicMock()
        
        # Run Fixer
        fixer.fix()
        
        # 1. Verify Page Margins Fixed
        assert mock_doc.sections[0].top_margin == "Cm(2.54)"
        assert mock_doc.sections[0].left_margin == "Cm(3.18)"

        # 2. Verify H1 formatting Fixed
        p_h1 = mock_doc.paragraphs[0]
        assert p_h1.runs[0].font.name == "黑体"
        assert p_h1.runs[0].font.size == "Pt(16)"
        
        # 3. Verify Body Text indent Fixed
        p_normal = mock_doc.paragraphs[2]
        # Body text needs indent=2 chars, approx 24pt if font size 12
        assert str(p_normal.paragraph_format.first_line_indent) == "Pt(24)"
        
        # 4. Verify Document Default Line Spacing Applied
        assert p_h1.paragraph_format.line_spacing == 1.5

def test_loose_rules_ignore_anomalies():
    mock_doc = create_mock_docx()
    with patch("engine.docx_parser.docx.Document", return_value=mock_doc):
        parser = DocxParser("fake.docx")
        parsed_data = parser.parse()
    
    loose_rules = {"validators": {"check_hierarchy": False, "check_gb7714": False}}
    validator = Validator(loose_rules)
    issues = validator.validate(parsed_data)
    
    msgs = " | ".join(i['message'] for i in issues)
    assert "跳级" not in msgs, "Should ignore structure checks"
    assert "GB/T 7714" not in msgs, "Should ignore refs checks"
    assert "页面边界" not in msgs, "Should bypass margin checks"

if __name__ == "__main__":
    # Provides a simple way to run without pytest dependency globally
    test_validation_detects_all_anomalies()
    test_auto_fixer_applies_styles_correctly()
    test_loose_rules_ignore_anomalies()
    print("✅ All mocked Engine unit tests passed successfully!")
