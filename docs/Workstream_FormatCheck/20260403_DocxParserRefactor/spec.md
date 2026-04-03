# 技术方案：DocxParser 样式解析树重构

## 背景 (Background)
`run.bold is None` 时当前代码直接默认 `False`，但 Word 的真实渲染遵循继承链：
`run_rPr → para_pPr → para_style → parent_style → document_defaults`

## 核心组件设计

### `StyleResolver` 类
```python
class StyleResolver:
    """
    预计算每个 Word 样式的最终渲染属性（Computed Style）。
    在 DocxParser 初始化时一次性构建，后续只做 O(1) 查表。
    """
    def __init__(self, doc: Document):
        self._computed: dict[str, dict] = {}
        self._build(doc)

    def _build(self, doc: Document):
        # 1. 读取 document defaults（最低优先级）
        # 2. 按继承链顺序 BFS 遍历所有 styles
        # 3. 子样式属性 override 父样式属性
        ...

    def get_computed_value(self, style_name: str, attr: str) -> Any:
        """返回给定样式的最终计算值"""
        return self._computed.get(style_name, {}).get(attr)
```

### `InvisibleToken` 枚举
```python
from enum import Enum

class InvisibleToken(Enum):
    TAB = "TAB"
    FULL_SPACE = "FULL_SPACE"   # 全角空格 \u3000
    HALF_SPACE = "HALF_SPACE"   # 半角空格
    LINE_BREAK = "LINE_BREAK"
```

### `parsed_data` 字段扩展
```python
{
    "text": str,
    "tokens": list[str | InvisibleToken],  # NEW: 保留排版骨架
    "style_name": str,
    "computed_bold": bool,                  # NEW: 由 StyleResolver 计算
    "computed_font_size_pt": float,         # NEW
    "computed_font_name_ascii": str,        # NEW
    "computed_font_name_east_asia": str,    # NEW
    "source": "paragraph" | "table" | "list",  # NEW
    ...
}
```

## 优先级
- **P0（必须）**: StyleResolver + Run解析重构
- **P1（应该）**: 表格解析扩展
- **P2（可以）**: 列表节点解析
