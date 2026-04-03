# Specification: Validation Engine Refactor

## 1. 核心遗漏属性的闭环校验机制
必须建立 `DocxParser` 提取的数据与 `rules.yaml` 之间的强对应：
*   **段前/段后间距 (`space_before`, `space_after`)**: 提取为 `pt`，并在 `validator.py` 中做数值比对（通常需要设定极小的容差范围，如±0.5pt）。
*   **行距 (`line_spacing`)**: 需识别单倍、1.5倍等相对行距与固定磅值，进行归一化校验。
*   **字重 (`bold`) 继承处理**: 修改布尔值强匹配逻辑，当 `run.bold` 为 `None` 且段落无明确声明时，防止发生一刀切的误报。

## 2. Validation Issue 结构体重构
目前引擎只抛出字符串报错，难以进行逆向追踪与一键修复。需重构结构体：
```python
from dataclasses import dataclass
from typing import Any, Optional

@dataclass
class ValidationIssue:
    element_index: int       # 段落序列索引
    issue_type: str          # 例如 "BOLD_MISMATCH" 或 "SPACING_ERROR"
    expected_value: Any
    actual_value: Any
    message: str
    run_index: Optional[int] = None # 如果错误细化到段落内的Run级别
```
通过这种精准的指针，后续能在 Fixer 流程中直接定位导致错误的文本内容。
