import os
import sys
import pytest
import io
from unittest.mock import MagicMock, patch

# Add src to Python Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Mock docx dependencies
sys.modules['docx'] = MagicMock()
sys.modules['docx.shared'] = MagicMock()
sys.modules['docx.enum.text'] = MagicMock()
sys.modules['docx.oxml.ns'] = MagicMock()
sys.modules['docx.oxml'] = MagicMock()

from domain.models import Issue, IssueCode, IssueSeverity, Patch
from use_cases.fixer_pipeline import FixerPipeline

def test_fixer_pipeline_filters_patches():
    # Arrange
    # 1. Mock Fixer
    mock_fixer_instance = MagicMock()
    mock_fixer_instance.fix.return_value = b"fixed_content"
    
    def mock_fixer_factory(buffer):
        return mock_fixer_instance
        
    pipeline = FixerPipeline(mock_fixer_factory)
    
    # 2. Issues (one with patch, one without)
    issues = [
        Issue(
            para_index=1, issue_code=IssueCode.FONT_SIZE, 
            severity=IssueSeverity.ERROR, message="Too small",
            suggested_patch=Patch(
                target_type="run", para_index=1, run_index=0, 
                attribute="font_size", value=12.0
            )
        ),
        Issue(
            para_index=2, issue_code=IssueCode.HEADING_SKIP, 
            severity=IssueSeverity.ERROR, message="Jumped H1 to H3"
            # No patch
        )
    ]
    
    # Act
    result = pipeline.apply_fixes(b"original", issues)
    
    # Assert
    assert result == b"fixed_content"
    # Verify fixer was called with ONLY one patch
    called_patches = mock_fixer_instance.fix.call_args[0][0]
    assert len(called_patches) == 1
    assert called_patches[0].attribute == "font_size"

if __name__ == "__main__":
    pytest.main([__file__])
