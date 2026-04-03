"""
Use Cases Layer — StyleMapper（样式名标准化映射器）
职责：将 Word 样式名映射为标准化层级标识，消除各处 startsWith("Heading 1") 硬编码。

层规则：
  - 只依赖 Python 标准库（re），不导入 docx / fastapi。
  - 可被 validator_pipeline.py 和 rule_config.py 共同导入，不产生循环依赖。
"""
from __future__ import annotations
import re
from typing import Dict, Optional


class StyleMapper:
    """
    将 Word 样式名标准化映射为层级标识。
    
    优先级：自定义映射（来自 rules.yaml style_mapping）> 内置正则模式。
    
    旧代码：sn.startswith("Heading 1") or sn.startswith("标题 1")
    新代码：StyleMapper.get_heading_level(sn) → 1 / 2 / 3 / None
    """

    # 内置规则：匹配 Word 标准英文/中文 Heading 样式（含数字后跟随的变体）
    _BUILTIN_PATTERNS = [
        (re.compile(r"^(?:Heading|标题)\s*1\b", re.IGNORECASE), 1),
        (re.compile(r"^(?:Heading|标题)\s*2\b", re.IGNORECASE), 2),
        (re.compile(r"^(?:Heading|标题)\s*3\b", re.IGNORECASE), 3),
        (re.compile(r"^(?:Heading|标题)\s*4\b", re.IGNORECASE), 4),
        (re.compile(r"^(?:Heading|标题)\s*5\b", re.IGNORECASE), 5),
    ]

    # 识别"参考文献"一级标题的关键词集合
    _REF_KEYWORDS = frozenset({"参考文献", "References", "REFERENCES"})

    # 触发退出 REFERENCES 状态的一级标题关键词前缀
    _EXIT_PREFIXES = ("附录", "致谢", "结论", "总结", "Conclusion", "Appendix", "Acknowledgment")

    def __init__(self, custom_mapping: Optional[Dict[str, int]] = None):
        """
        custom_mapping: 来自 rules.yaml style_mapping 的自定义映射，格式：
            {"我的奇葩一级标题": 1, "我的二级标题样式": 2}
        """
        self._custom: Dict[str, int] = custom_mapping or {}

    def get_heading_level(self, style_name: str) -> Optional[int]:
        """
        返回样式名对应的标题层级（1-5），非标题样式返回 None。
        优先级：自定义映射（精确匹配）> 内置正则模式。
        """
        # 自定义映射（精确匹配）
        if style_name in self._custom:
            return self._custom[style_name]

        # 内置正则模式
        for pattern, level in self._BUILTIN_PATTERNS:
            if pattern.match(style_name):
                return level

        return None

    def is_references_heading(self, style_name: str, text: str) -> bool:
        """
        判断是否为"参考文献"节标题。
        同时检查样式（必须是一级标题）和文本内容（关键词匹配）。
        """
        if self.get_heading_level(style_name) != 1:
            return False
        cleaned = text.replace(" ", "").replace("\u3000", "")
        return cleaned in self._REF_KEYWORDS

    def is_exit_heading(self, style_name: str, text: str) -> bool:
        """
        判断是否为"退出参考文献区域"的一级标题（附录/致谢/结论等）。
        只有在 REFERENCES 状态下遇到下一个一级标题时才触发。
        """
        if self.get_heading_level(style_name) != 1:
            return False
        # 文本不是"参考文献"本身，且匹配退出关键词
        cleaned = text.replace(" ", "").replace("\u3000", "")
        if cleaned in self._REF_KEYWORDS:
            return False
        return any(cleaned.startswith(kw) for kw in self._EXIT_PREFIXES)

    def is_heading(self, style_name: str) -> bool:
        """判断样式是否为任意级别的标题。"""
        return self.get_heading_level(style_name) is not None
