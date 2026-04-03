"""
Infrastructure Layer — 单位换算工具
规则：此工具类只含纯函数，无状态，可被任何层使用（但主因在 infrastructure）。
集中管理所有单位转换，禁止在 Parser 或 Plugin 中出现 `/ 12` 等硬编码换算。
"""
from __future__ import annotations
from typing import Optional


_PT_PER_CHAR_DEFAULT = 12.0   # 默认字号（12pt = 1 字符宽度）
_CM_PER_INCH = 2.54
_PT_PER_INCH = 72.0
_PT_PER_CM   = _PT_PER_INCH / _CM_PER_INCH   # ≈ 28.35


class UnitConverter:
    """
    集中式单位换算工具（只包含静态方法，无需实例化）。
    所有解析器/格式化器应通过此类进行单位转换。
    """

    @staticmethod
    def pt_to_cm(pt: float) -> float:
        """磅（pt）→ 厘米（cm）"""
        return pt / _PT_PER_CM

    @staticmethod
    def cm_to_pt(cm: float) -> float:
        """厘米（cm）→ 磅（pt）"""
        return cm * _PT_PER_CM

    @staticmethod
    def pt_to_chars(pt: float, font_size_pt: float = _PT_PER_CHAR_DEFAULT) -> float:
        """
        磅（pt）→ 字符数（近似）。
        :param pt: 缩进值（pt）
        :param font_size_pt: 当前字号（pt），默认 12pt
        """
        if font_size_pt <= 0:
            return 0.0
        return round(pt / font_size_pt, 2)

    @staticmethod
    def emu_to_cm(emu: int) -> float:
        """EMU（English Metric Units）→ 厘米"""
        return emu / 914400 * _CM_PER_INCH

    @staticmethod
    def half_pt_to_pt(half_pt: int) -> float:
        """半磅（Word XML 内部单位）→ 磅"""
        return half_pt / 2.0

    @staticmethod
    def twips_to_pt(twips: int) -> float:
        """缇（twips，Word XML 间距单位）→ 磅。1pt = 20 twips"""
        return twips / 20.0

    @staticmethod
    def normalize_line_spacing(raw_value: Optional[object]) -> Optional[float]:
        """
        将 python-docx 返回的 line_spacing（可能是 Length 对象或 float）
        统一转换为"磅（pt）或纯倍数"的 float。
        - 若有 .pt 属性，视为固定磅值。
        - 否则视为倍数（如 1.5）。
        """
        if raw_value is None:
            return None
        if hasattr(raw_value, "pt"):
            return float(raw_value.pt)
        return float(raw_value)
