import pytest
from src.domain.utils.unit_converter import UnitConverter

def test_pt_to_chars():
    # 小四 12pt 下，24pt 应该是 2 字符
    assert UnitConverter.pt_to_chars(24.0, 12.0) == 2.0
    # 五号 10.5pt 下，21pt 应该是 2 字符
    assert UnitConverter.pt_to_chars(21.0, 10.5) == 2.0
    # 零分母保护
    assert UnitConverter.pt_to_chars(12.0, 0) == 1.0

def test_cm_to_pt():
    # 2.54 cm = 72 pt
    assert abs(UnitConverter.cm_to_pt(2.54) - 72.0) < 0.1

def test_nearest_font():
    assert UnitConverter.find_nearest_font_name(12.0) == '小四'
    assert UnitConverter.find_nearest_font_name(10.5) == '五号'
