# DocxParser 重构：建立"真实样式解析树"

## 背景 (Context)
当前 `DocxParser` 是扁平化解析器，直接读取 `run.bold` 等属性，无法处理 Word 的样式继承链（Normal → Heading → 用户样式）。这是字重/字号/字体误报的根源。需要建立 CSS-like 的层叠样式解析能力。

## 策略 (Strategy)
先读 `styles.xml` + `document defaults` 构建 Computed Style 字典树（Style Resolver），再进行段落/Run 遍历；引入 Invisible Token 替代粗暴 `strip()`；扩展至表格和列表节点。

## 待办清单 (Checklist)

### Phase 1: Style Resolver 构建
- [ ] 读取 `document.styles` 构建样式继承链字典树
- [ ] 实现 `resolver.get_computed_value(para_style, run_style, attr)` 通用方法
- [ ] 覆盖 `bold`, `italic`, `font_size`, `font_name`, `color` 五个关键属性
- [ ] 编写单元测试 `tests/unit/engine/test_style_resolver.py`

### Phase 2: Run 解析重构
- [ ] 移除 `if not run.text.strip(): continue` 粗暴过滤
- [ ] 引入 `InvisibleToken` 枚举（TAB, FULL_SPACE, HALF_SPACE）
- [ ] 将首行缩进检测改为基于 Token 统计而非字符串 len()
- [ ] 更新 `parsed_data` 字段结构文档（`spec.md`）

### Phase 3: 扩展解析范围
- [ ] 实现 `_parse_tables()` 方法，遍历 `doc.tables` 单元格段落
- [ ] 实现 `_parse_lists()` 方法，识别 `w:numPr` 列表节点
- [ ] 将表格/列表段落同样转化为标准元素字典
- [ ] 编写集成测试 `tests/integration/test_parser_extended.py`

### Phase 4: 验证与对齐
- [ ] 运行现有测试套件，确保无回归
- [ ] 对比重构前后：误报率下降验证（使用 `tests/fixtures/` 测试文档）
- [ ] 更新 `docs/tree.md`
