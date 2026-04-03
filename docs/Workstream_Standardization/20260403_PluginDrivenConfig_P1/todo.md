# 插件驱动型配置系统重构 (Plugin-driven Config Refactor)

## 背景 (Context)
当前 `RuleConfig` 是一个上帝类，所有插件的配置都集中定义在一个文件中。随着插件增多，该类变得臃肿且违背了"插件化"的初衷。用户要求"所有设置均由插件显示声明"，即配置的定义应当回归到插件本身。

## 待办清单 (Checklist)

### Phase 1: 架构设计与基础设施
- [ ] 定义 `ConfigurablePlugin` 接口或 Mixin (Plugin Infrastructure)
- [ ] 在 `RuleConfig` 中实现动态模型生成器 `create_dynamic_rule_config`

### Phase 2: 插件配置迁移 (逐个迁移)
- [ ] `PaginationPlugin`: 迁移 `PaginationConfig`
- [ ] `PageMarginPlugin`: 迁移 `PageSetupConfig`
- [ ] `FontPlugin`: 声明 `ParagraphRule` 中属于字体的部分
- [ ] `SpacingPlugin`: 声明 `ParagraphRule` 中属于间距的部分

### Phase 3: 整体集成与验证
- [ ] 更新 `RuleLoader` 以支持动态模型加载
- [ ] 确保 `rules.yaml` 依然能够正确映射到新模型
- [ ] 验证现有单元测试是否通过
- [ ] 编写测试用例确保新插件能自动注册其配置项
