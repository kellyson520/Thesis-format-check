import os
import sys
import pytest
from unittest.mock import MagicMock, patch

# Add src to Python Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))



from domain.models import ParagraphNode, RuleContext, DocumentSection
from use_cases.style_mapper import StyleMapper
from use_cases.validator_pipeline import _update_context

def test_style_mapper_heading_detection():
    mapper = StyleMapper()
    assert mapper.get_heading_level("Heading 1") == 1
    assert mapper.get_heading_level("标题 2") == 2
    assert mapper.get_heading_level("Normal") is None
    
    # Custom mapping
    custom_mapper = StyleMapper({"MyCustomTitle": 1})
    assert custom_mapper.get_heading_level("MyCustomTitle") == 1

def test_validator_state_machine_transitions():
    mapper = StyleMapper()
    ctx = RuleContext(current_section=DocumentSection.BODY, current_chapter=1)
    
    # 1. Encounter "参考文献" Heading 1
    ref_para = ParagraphNode(index=1, text="参考文献", style_name="Heading 1")
    new_ctx = _update_context(ctx, ref_para, mapper)
    assert new_ctx.current_section == DocumentSection.REFERENCES
    
    # 2. In REFERENCES, encounter "致谢" Heading 1
    thanks_para = ParagraphNode(index=2, text="致谢", style_name="Heading 1")
    final_ctx = _update_context(new_ctx, thanks_para, mapper)
    assert final_ctx.current_section == DocumentSection.APPENDIX

def test_chapter_aware_caption_reset():
    mapper = StyleMapper()
    ctx = RuleContext(
        current_section=DocumentSection.BODY, 
        current_chapter=1,
        chapter_figure_num=5
    )
    
    # Encounter new Chapter (Heading 1)
    h1_para = ParagraphNode(index=10, text="第二章 系统设计", style_name="Heading 1")
    new_ctx = _update_context(ctx, h1_para, mapper)
    
    assert new_ctx.current_chapter == 2
    assert new_ctx.chapter_figure_num == 0 # Should be reset

if __name__ == "__main__":
    pytest.main([__file__])
