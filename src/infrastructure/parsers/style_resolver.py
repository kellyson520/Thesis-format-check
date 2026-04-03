"""
Infrastructure Layer — StyleResolver（Word 样式继承链解析器）

职责：
  - 一次性读取 document.styles 和 document defaults，构建 Computed Style 字典树。
  - 提供 get_computed_*() 方法，当 Run/Para 属性为 None 时向上查找真实继承值。
  - 这是消除 run.bold=None 误判的根本修复。

层规则：
  - 仅依赖 python-docx（外环 Infrastructure 层）。
  - 不含任何业务判断逻辑（"正确"的概念属于 Plugin 层）。
"""
from __future__ import annotations
from typing import Optional, Dict, Any
import docx
from docx.oxml.ns import qn


# Word XML 数值属性名常量
_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _xml_bool(val: Any) -> Optional[bool]:
    """将 Word XML 的 <w:b/> 或 <w:b w:val="0"/> 转换为 Python bool。"""
    if val is None:
        return None
    # 已经是 bool
    if isinstance(val, bool):
        return val
    # lxml _Element：<w:b/> 无 val 属性表示 True，val="0" 表示 False
    # （python-docx run.bold 已经处理了这层，此处用于原始 XML 读取）
    s = str(val).lower()
    if s in ("1", "true", "on", ""):
        return True
    if s in ("0", "false", "off"):
        return False
    return None


def _read_rpr_bold(rPr) -> Optional[bool]:
    """从 <w:rPr> 元素读取 bold 属性（处理 <w:b/> 与 <w:b w:val='0'/>）。"""
    if rPr is None:
        return None
    b_el = rPr.find(qn("w:b"))
    if b_el is None:
        return None
    val = b_el.get(qn("w:val"))
    if val is None:
        return True          # <w:b/> 无 val → bold
    if val == "0":
        return False         # <w:b w:val="0"/> → NOT bold
    return True


def _read_rpr_size(rPr) -> Optional[float]:
    """从 <w:rPr> 读取 <w:sz>（单位: half-pt → pt 除以2）。"""
    if rPr is None:
        return None
    sz = rPr.find(qn("w:sz"))
    if sz is None:
        return None
    val = sz.get(qn("w:val"))
    if val and val.isdigit():
        return int(val) / 2.0
    return None


def _read_rpr_font_ascii(rPr) -> Optional[str]:
    """从 <w:rPr>/<w:rFonts> 读取 ascii 字体。"""
    if rPr is None:
        return None
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        return None
    return rFonts.get(qn("w:ascii")) or rFonts.get(qn("w:hAnsi"))


def _read_rpr_font_east_asia(rPr) -> Optional[str]:
    """从 <w:rPr>/<w:rFonts> 读取 eastAsia 字体。"""
    if rPr is None:
        return None
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        return None
    return rFonts.get(qn("w:eastAsia"))


# ─── Computed Style 条目 ──────────────────────────────────────────────────────

class _StyleEntry:
    """
    单个 Word 样式的计算属性（经过继承链合并后的最终值）。
    属性为 None 表示该层未定义，向上层查找。
    """
    __slots__ = ("bold", "size_pt", "ascii_font", "east_asia_font", "widow_control", "keep_with_next", "keep_together")

    def __init__(self):
        self.bold: Optional[bool]          = None
        self.size_pt: Optional[float]      = None
        self.ascii_font: Optional[str]     = None
        self.east_asia_font: Optional[str] = None
        self.widow_control: Optional[bool]  = None
        self.keep_with_next: Optional[bool] = None
        self.keep_together: Optional[bool]  = None

    def merge_from(self, child: "_StyleEntry") -> "_StyleEntry":
        """
        将 child 的非 None 属性覆盖到 self（deep copy 语义）。
        用于从父样式向子样式继承时，child 优先级更高。
        返回新的 _StyleEntry，原对象不变（immutable-friendly）。
        """
        result = _StyleEntry()
        result.bold          = child.bold          if child.bold          is not None else self.bold
        result.size_pt       = child.size_pt       if child.size_pt       is not None else self.size_pt
        result.ascii_font    = child.ascii_font    if child.ascii_font    is not None else self.ascii_font
        result.east_asia_font = child.east_asia_font if child.east_asia_font is not None else self.east_asia_font
        result.widow_control  = child.widow_control  if child.widow_control  is not None else self.widow_control
        result.keep_with_next = child.keep_with_next if child.keep_with_next is not None else self.keep_with_next
        result.keep_together  = child.keep_together  if child.keep_together  is not None else self.keep_together
        return result

    def __repr__(self):
        return (
            f"_StyleEntry(bold={self.bold}, size_pt={self.size_pt}, "
            f"ascii={self.ascii_font!r}, ea={self.east_asia_font!r})"
        )


def _read_ppr_bool(pPr, tag_name: str) -> Optional[bool]:
    """从 <w:pPr> 读取布尔标记（通常无 val = True）。"""
    if pPr is None: return None
    el = pPr.find(qn(f"w:{tag_name}"))
    if el is None: return None
    # 大多数分页标记如 <w:widowControl/> 只要存在就是 True，除非 val="0"
    val = el.get(qn("w:val"))
    return False if val == "0" else True

def _entry_from_style(style_el) -> _StyleEntry:
    """从样式的 XML 元素中同时收集 <w:rPr> 和 <w:pPr> 属性。"""
    e = _StyleEntry()
    if style_el is None: return e
    
    rPr = style_el.find(qn("w:rPr"))
    if rPr is not None:
        e.bold           = _read_rpr_bold(rPr)
        e.size_pt        = _read_rpr_size(rPr)
        e.ascii_font     = _read_rpr_font_ascii(rPr)
        e.east_asia_font = _read_rpr_font_east_asia(rPr)
    
    pPr = style_el.find(qn("w:pPr"))
    if pPr is not None:
        e.widow_control  = _read_ppr_bool(pPr, "widowControl")
        e.keep_with_next = _read_ppr_bool(pPr, "keepNext")
        e.keep_together  = _read_ppr_bool(pPr, "keepLines")
        
    return e


# ─── StyleResolver 主类 ────────────────────────────────────────────────────────

class StyleResolver:
    """
    预计算 Word 文档中所有样式的最终渲染属性。

    初始化步骤：
      1. 读取 document defaults（最低优先级基线）
      2. BFS 遍历所有样式，按继承链 merge 属性
      （子样式 > 父样式 > document defaults）

    使用示例：
      resolver = StyleResolver(doc)
      # 当 run.bold is None 时，用样式名回退
      computed_bold = resolver.get_computed_bold("Heading 1")
    """

    def __init__(self, doc: docx.Document):
        self._computed: Dict[str, _StyleEntry] = {}
        self._build(doc)

    # ── 构建阶段 ────────────────────────────────────────────────────────────

    def _build(self, doc: docx.Document) -> None:
        """一次性构建全部样式的 Computed Style 表。"""
        # Step 1: 读取 document defaults 作为根节点
        doc_defaults = self._read_doc_defaults(doc)

        # Step 2: 收集所有样式的原始属性（未继承）
        raw: Dict[str, _StyleEntry] = {}
        parent_map: Dict[str, Optional[str]] = {}   # style_name → parent_name

        for style in doc.styles:
            sname = style.name
            rPr = None
            try:
                # 获取样式的 <w:rPr>
                if style.element is not None:
                    rPr_el = style.element.find(qn("w:rPr"))
                    rPr = rPr_el
            except Exception:
                pass
            raw[sname] = _entry_from_style(style.element)
            # 记录父样式名
            base = getattr(style, "base_style", None)
            parent_map[sname] = base.name if base else None

        # Step 3: 拓扑顺序合并（BFS from roots）
        # 已计算集合（以 doc_defaults 为根）
        resolved: Dict[str, _StyleEntry] = {}

        def resolve(name: str, depth: int = 0) -> _StyleEntry:
            """递归计算样式的最终属性（带循环保护）。"""
            if name in resolved:
                return resolved[name]
            if depth > 32:
                # 防止循环继承死循环
                resolved[name] = doc_defaults
                return doc_defaults

            parent_name = parent_map.get(name)
            if parent_name:
                parent_entry = resolve(parent_name, depth + 1)
            else:
                parent_entry = doc_defaults

            # 子样式属性 override 父样式
            merged = parent_entry.merge_from(raw.get(name, _StyleEntry()))
            resolved[name] = merged
            return merged

        for sname in raw:
            resolve(sname)

        self._computed = resolved
        # 将 document defaults 也存一份，供未知样式兜底
        self._doc_defaults = doc_defaults

    def _read_doc_defaults(self, doc: docx.Document) -> _StyleEntry:
        """
        读取 <w:docDefaults>/<w:rPrDefault>/<w:rPr>。
        这是 Word 继承链的最底层（最低优先级）。
        """
        try:
            body = doc.element.body
            # styles.xml 中 docDefaults 路径
            styles_part = doc.part.styles
            if styles_part is None:
                return _StyleEntry()
            doc_defaults_el = styles_part._element.find(qn("w:docDefaults"))
            if doc_defaults_el is None:
                return _StyleEntry()
            rPrDefault = doc_defaults_el.find(qn("w:rPrDefault"))
            if rPrDefault is None:
                return _StyleEntry()
            rPr = rPrDefault.find(qn("w:rPr"))
            return _entry_from_rpr(rPr)
        except Exception:
            return _StyleEntry()

    # ── 查询接口 ────────────────────────────────────────────────────────────

    def _get(self, style_name: str) -> _StyleEntry:
        """获取样式的 Computed Entry，未知样式返回 document defaults。"""
        return self._computed.get(style_name, self._doc_defaults)

    def get_computed_bold(self, style_name: str) -> Optional[bool]:
        """
        返回给定样式的最终 bold 状态。
        当 Run.bold is None 时，应调用此方法获取继承值。

        返回 None 表示整个继承链均未定义（极少数情况，可视为 False）。
        """
        return self._get(style_name).bold

    def get_computed_size_pt(self, style_name: str) -> Optional[float]:
        """返回给定样式的最终字号（pt）。None 表示整个继承链均未定义。"""
        return self._get(style_name).size_pt

    def get_computed_ascii_font(self, style_name: str) -> Optional[str]:
        """返回给定样式的最终英文字体名。"""
        return self._get(style_name).ascii_font

    def get_computed_east_asia_font(self, style_name: str) -> Optional[str]:
        """返回给定样式的最终中文字体名。"""
        return self._get(style_name).east_asia_font

    def get_computed_widow_control(self, style_name: str) -> Optional[bool]:
        """返回给定样式的孤行控制状态。"""
        return self._get(style_name).widow_control

    def get_computed_keep_with_next(self, style_name: str) -> Optional[bool]:
        """返回给定样式的与下段同页状态。"""
        return self._get(style_name).keep_with_next

    def get_computed_keep_together(self, style_name: str) -> Optional[bool]:
        """返回给定样式的段内不分页状态。"""
        return self._get(style_name).keep_together

    def get_computed_value(self, style_name: str, attr: str) -> Any:
        """
        通用查询接口（attr: 'bold' | 'size_pt' | 'ascii_font' | 'east_asia_font'）。
        """
        entry = self._get(style_name)
        return getattr(entry, attr, None)

    @property
    def known_styles(self) -> list[str]:
        """返回所有已解析的样式名列表（调试用）。"""
        return list(self._computed.keys())
