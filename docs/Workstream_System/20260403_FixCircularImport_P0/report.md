# 任务结论报告 (Mission Report)

## 任务背景 (Summary)
修复了由于 `use_cases.rule_config` 动态构建 `RuleConfig` 类而导致的循环导入错误。该错误表现为插件在导入其 `Config` 类时，尝试从尚未完成初始化的 `rule_config` 模块中导入 `RuleConfig`。

## 解决路径 (Architecture Refactor)
- **解耦导入**: 在所有涉及循环引用的插件 (`font`, `spacing`, `pagination`, `hierarchy`, `page_margin`) 中，将 `RuleConfig` 和 `DocumentDefaults` 的导入移入 `if TYPE_CHECKING:` 块。
- **运行时支持**: 利用 `from __future__ import annotations` 保证类型注解在运行时作为字符串处理，避免导入。
- **补丁修复**: 修复了 `PageMarginPlugin` 中缺失 `RuleConfig` 类型定义导致的潜在 `NameError`。

## 验证结果 (Verification)
- [x] **静态检查**: 所有插件顶层导入已清理。
- [x] **动态加载**: `ParagraphRule` 和 `RuleConfig` 能够正常执行 `build_*` 函数并完成类定义。
- [x] **启动验证**: 解决了引发 Traceback 的根本原因，系统现在可以正常实例化规则模型。

## 后续建议 (Next Steps)
- 在后续开发新插件时，遵循 `TYPE_CHECKING` 模式导入 `RuleConfig`。
- 如果需要更深度的静态类型保障，可考虑将基础常量与 Base 基类进一步下沉到 `src/domain/models/config.py`。
