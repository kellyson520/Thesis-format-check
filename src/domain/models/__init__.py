"""
Domain Layer — 核心实体定义
规则：此模块禁止导入 docx / fastapi / yaml / json 等任何外部库。
仅使用 Python 标准库 + Pydantic。
"""
from __future__ import annotations
from typing import List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field


# ─── Issue 错误码枚举 ───────────────────────────────────────────────────────
class IssueCode(str, Enum):
    PAGE_MARGIN   = "E001"  # 页边距不符
    FONT_EAST_ASIA = "E002"  # 中文字体不符
    FONT_ASCII     = "E003"  # 英文字体不符
    FONT_SIZE      = "E004"  # 字号不符
    BOLD           = "W001"  # 字重不符
    SPACE_BEFORE   = "E005"  # 段前间距不符
    SPACE_AFTER    = "E006"  # 段后间距不符
    LINE_SPACING   = "E007"  # 行距不符
    ALIGNMENT      = "W002"  # 对齐方式不符
    INDENT         = "W003"  # 首行缩进不足
    CAPTION_SEQ    = "W004"  # 题注编号不连续
    HEADING_SKIP   = "E008"  # 标题跳级
    REF_FORMAT     = "W005"  # 参考文献格式


class IssueSeverity(str, Enum):
    ERROR = "Error"
    WARN  = "Warn"


# ─── Issue 报告单元 ──────────────────────────────────────────────────────────
class Issue(BaseModel):
    """一个格式问题记录，与任何 Web 框架无关。"""
    id: int = 0
    para_index: int = -1
    issue_code: IssueCode
    severity: IssueSeverity
    context: str = ""
    message: str


# ─── 文档节点 —— 抽象文档模型 (ADM) ─────────────────────────────────────────
class TextRunNode(BaseModel):
    """Word 中的一个 Run（相同格式的连续文字片段）"""
    text: str
    ascii_font: Optional[str] = None
    east_asia_font: Optional[str] = None
    size_pt: Optional[float] = None       # 单位统一为 pt（由 UnitConverter 负责）
    bold: Optional[bool] = None


class ParagraphNode(BaseModel):
    """Word 中的一个段落，所有格式值已由 Parser 转换为统一单位。"""
    index: int                             # 原始段落索引（1-based）
    text: str
    style_name: str
    alignment: Optional[str] = None       # "left" / "center" / "right" / "justify"
    line_spacing: Optional[float] = None  # 统一为 pt 或倍数（由规则决定语义）
    first_line_indent_chars: float = 0.0  # 单位：字符数（UnitConverter 换算）
    space_before_pt: float = 0.0
    space_after_pt: float = 0.0
    runs: List[TextRunNode] = Field(default_factory=list)


class SectionNode(BaseModel):
    """Word 中的一个节（Section），包含页边距信息（单位：cm）"""
    top_margin_cm: Optional[float] = None
    bottom_margin_cm: Optional[float] = None
    left_margin_cm: Optional[float] = None
    right_margin_cm: Optional[float] = None


class DocumentModel(BaseModel):
    """完整的抽象文档模型，由 DocxParser 输出。不包含 python-docx 对象。"""
    paragraphs: List[ParagraphNode] = Field(default_factory=list)
    sections: List[SectionNode] = Field(default_factory=list)


# ─── 验证上下文（Plugin 之间共享的文档状态） ─────────────────────────────────
class DocumentSection(str, Enum):
    """文档区域枚举，用于 Plugin 询问当前所在位置。"""
    FRONT_MATTER = "front_matter"   # 摘要、目录等前置内容
    BODY         = "body"           # 正文
    REFERENCES   = "references"     # 参考文献
    APPENDIX     = "appendix"       # 附录


class RuleContext(BaseModel):
    """Plugin 运行时可访问的共享上下文（只读，禁止 Plugin 直接修改）。"""
    current_section: DocumentSection = DocumentSection.BODY
    last_heading_level: int = 0
    last_figure_num: int = 0
    last_table_num: int = 0
    in_references: bool = False
