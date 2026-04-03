# Task: Settings UI Refresh & Dynamic Plugin Toggles

## Objective
1.  **UI Consistency**: Move "System Settings" from an overlay to a primary tab in the main layout.
2.  **Toggle Management**: Ensure all feature plugins (Validators) have a master toggle in the Settings tab.
3.  **Dynamic Expansion**: Each plugin should be explicitly declared (backend) and have its own toggle (frontend).
4.  **Aesthetics**: Follow the "rich aesthetics" rule (premium look, gradients, cards, etc.).

## TODO
- [x] **Backend: Plugin Configuration Upgrade**
  - [x] `PageSetupConfig` (PageMarginPlugin) 增加 `enabled` 字段。
  - [x] `CaptionSeqConfig` (CaptionSeqPlugin) 增加显示声明配置。
  - [x] `RuleConfig` 顶层增加所有核心插件的显式声明 (font, spacing, hierarchy, references, caption_seq)。
  - [x] `RuleLoader` 同步逻辑：确保主配置与 `validators` 旧区块状态一致。
- [x] **Frontend: App.vue Tab Refactoring**
  - [x] 侧边栏增加「系统设置」主 Tab，移除 overlay 模式。
  - [x] 规则管理页面的「高级设置」迁移并重定向。
  - [x] 实现美观、显式的插件开关列表（Pipeline Management）。
  - [x] 适配 Premium Design (Settings Cards, Grid Layout, Badges)。
- [x] **Verification & Polish**
  - [x] 验证开关操作对后台 `rules.yaml` 的持久化影响。
  - [x] 验证开关对 `ValidatorPipeline` 的实时拦截效果。
  - [x] 完善插件标准声明示例 (`docs/Architecture/Plugin_Standard.md`)。
  - [x] 检查所有当前插件是否满足标准（已全部补齐卫句与 Mixin）。
  - [ ] 补齐 `Settings` 页面的移动端适配或极端窄屏优化 (Optional)。
