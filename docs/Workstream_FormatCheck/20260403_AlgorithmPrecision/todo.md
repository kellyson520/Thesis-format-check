# 数据校验算法精度提升

## 背景 (Context)
当前中英文混排检测使用 `ord(char) < 128` 判断，被空格、数字严重污染；首行缩进使用 `pt / 12` 魔法数字换算，无法适应不同字号段落（如小四12pt vs 五号10.5pt）。

## 策略 (Strategy)
使用 `unicodedata` 精准识别字符集（CJK Block 判断）；建立 `UnitConverter` 工具类，根据段落实际继承字号动态换算 pt/cm/chars。

## 待办清单 (Checklist)

### Phase 1: 中英文字符集检测优化
- [ ] 实现 `is_cjk_character(char: str) -> bool` 使用 `unicodedata` 判断 CJK Block
- [ ] 实现 `detect_text_charset(text: str) -> TextCharset` 清洗数字和空白后判断
- [ ] 替换 Validator 中所有 `has_chinese` / `has_ascii` 调用点
- [ ] 编写单元测试 `tests/unit/utils/test_charset_detector.py`

### Phase 2: UnitConverter 工具类
- [ ] 实现 `UnitConverter` 类
  - `pt_to_chars(pt_value, font_size_pt) -> float`
  - `cm_to_pt(cm_value) -> float`
  - `pt_to_cm(pt_value) -> float`
- [ ] 内置字号常量字典（小初=42pt, 初号=36pt, 小一=30pt ... 小五=9pt）
- [ ] 替换 Validator 中所有 `/ 12` `/ 28.35` 类型的魔法数字
- [ ] 编写单元测试 `tests/unit/utils/test_unit_converter.py`

### Phase 3: 集成与验证
- [ ] 与 StyleResolver 集成：`UnitConverter` 使用 computed font_size 动态换算
- [ ] 运行回归测试，确认缩进误报率降低
