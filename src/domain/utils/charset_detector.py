import unicodedata
import re

def is_cjk_character(char: str) -> bool:
    """
    精确判断一个字符是否属于 CJK (中日韩) 字符集。
    """
    if not char: return False
    code = ord(char)
    # 常用中文字符范围 (CJK Unified Ideographs)
    if 0x4E00 <= code <= 0x9FFF:
        return True
    # 扩展范围 (CJK Extension A-G, Symbols)
    name = unicodedata.name(char, "")
    return "CJK" in name or "IDEOGRAPH" in name

def detect_text_charset(text: str) -> str:
    """
    分析文本的字符集偏向 ('cjk', 'latin', 'mixed', 'neutral')。
    """
    if not text: return 'neutral'
    
    # 移除空白、数字、标点（\W）和下划线
    clean_text = re.sub(r'[\s\d\W_]', '', text)
    if not clean_text:
        # 如果全是数字/标点，看原始串是否有 ascii
        return 'latin' if any(c.isascii() and not c.isspace() for c in text) else 'neutral'
    
    has_cjk = any(is_cjk_character(c) for c in clean_text)
    has_alphabetic = any(c.isalpha() and not is_cjk_character(c) for c in clean_text)

    if has_cjk and has_alphabetic: return 'mixed'
    if has_cjk: return 'cjk'
    return 'latin'

