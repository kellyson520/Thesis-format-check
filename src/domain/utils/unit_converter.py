import math
from typing import Optional

class UnitConverter:
    """
    提供排版单位换算的工具类。
    支持 pt (点), cm (厘米), chars (字符), emu, half_pt, twips 之间的动态换算。
    """
    
    # 中国常用排版字号定义表 (Name to pt)
    CHINA_FONT_SIZES = {
        '初号': 42.0, '小初': 36.0, '一号': 26.0, '小一': 24.0, '二号': 22.0, '小二': 18.0,
        '三号': 16.0, '小三': 15.0, '四号': 14.0, '小四': 12.0, '五号': 10.5, '小五': 9.0,
        '六号': 7.5, '小六': 6.5, '七号': 5.5, '八号': 5.0
    }

    PT_PER_INCH = 72.0
    CM_PER_INCH = 2.54
    PT_PER_CM = PT_PER_INCH / CM_PER_INCH # ≈ 28.35

    @classmethod
    def pt_to_cm(cls, pt: float) -> float:
        return pt / cls.PT_PER_CM

    @classmethod
    def cm_to_pt(cls, cm: float) -> float:
        return cm * cls.PT_PER_CM

    @classmethod
    def pt_to_chars(cls, pt: float, font_size_pt: float = 12.0) -> float:
        """根据字号换算为中文字符宽度 (chars)"""
        if not font_size_pt or font_size_pt <= 0:
            font_size_pt = 12.0
        return round(pt / font_size_pt, 2)

    @classmethod
    def chars_to_pt(cls, chars: float, font_size_pt: float = 12.0) -> float:
        """将字符宽度还原为 pt"""
        if not font_size_pt or font_size_pt <= 0:
            font_size_pt = 12.0
        return chars * font_size_pt

    @classmethod
    def emu_to_cm(cls, emu: int) -> float:
        """EMU -> 厘米"""
        return emu / 914400 * cls.CM_PER_INCH

    @classmethod
    def half_pt_to_pt(cls, half_pt: int) -> float:
        """半磅 -> 磅"""
        return half_pt / 2.0

    @classmethod
    def twips_to_pt(cls, twips: int) -> float:
        """缇 -> 磅 (1pt = 20 twips)"""
        return twips / 20.0

    @classmethod
    def normalize_line_spacing(cls, raw_value: Optional[object]) -> Optional[float]:
        """归一化行距输出：如果是 Length 对象取 pt，否则取倍数 float"""
        if raw_value is None:
            return None
        if hasattr(raw_value, "pt"):
            return float(raw_value.pt)
        try:
            return float(raw_value)
        except (ValueError, TypeError):
            return None

    @classmethod
    def find_nearest_font_name(cls, pt: float) -> str:
        for name, size in cls.CHINA_FONT_SIZES.items():
            if abs(size - pt) < 0.1:
                return name
        return f"{pt}pt"
