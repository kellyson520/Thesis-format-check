# 修复循环导出错误 (Fix Circular Import)

## 背景 (Context)
在 `use_cases.rule_config` 动态构建 `RuleConfig` 过程中，需要导入各插件的 `Config` 类。而各插件的 `Plugin` 类又在顶层导入了 `RuleConfig` 进行类型标注，导致 `ImportError: cannot import name 'RuleConfig' from partially initialized module`。

## 待办清单 (Checklist)

### Phase 1: 核心修复
- [x] 修复 `src/use_cases/plugins/font_plugin.py` 的循环导入
- [x] 修复 `src/use_cases/plugins/spacing_plugin.py` 的循环导入
- [x] 修复 `src/use_cases/plugins/pagination_plugin.py` 的循环导入
- [x] 修复 `src/use_cases/plugins/hierarchy_plugin.py` 的循环导入
- [x] 修复 `src/use_cases/plugins/page_margin_plugin.py` 的 `RuleConfig` 缺失及潜在循环导入

### Phase 2: 验证与清理
- [x] 运行 `python main.py` 验证启动是否正常
- [x] 验证 `ParagraphRule` 动态生成是否正常
- [x] 编写交付报告 `report.md`
