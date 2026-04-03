import pytest
from src.domain.utils.charset_detector import is_cjk_character, detect_text_charset

def test_is_cjk():
    assert is_cjk_character('中') is True
    assert is_cjk_character('文') is True
    assert is_cjk_character('A') is False
    assert is_cjk_character('1') is False
    assert is_cjk_character(' ') is False
    # '，' (FF0C) 是标点，不应判定为 CJK 统一表意文字 (Ideograph)
    assert is_cjk_character('，') is False

def test_detect_charset():
    assert detect_text_charset("全部中文") == 'cjk'
    assert detect_text_charset("English Only") == 'latin'
    assert detect_text_charset("中英Mixed") == 'mixed'
    assert detect_text_charset("12345") == 'latin' # 含数字但无 CJK
    assert detect_text_charset("") == 'neutral'
    assert detect_text_charset("，。！？") == 'neutral' # 纯标点返回中性，以适用规则回退
