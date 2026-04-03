# TODO: 规则管理页面重构

- [ ] **Phase 1: 导航重组**
    - [ ] 定义 `rulesSubTab` 状态变量。
    - [ ] 设计并实现 Segmented Control 组件样式。
    - [ ] 实现 Tab 切换逻辑，挂载到 `switchTab` 及其副作用。

- [ ] **Phase 2: 内容切片 (Refactoring Editor)**
    - [ ] 抽取“常规设置” Tab。
    - [ ] 抽取“标题定义” Tab。
    - [ ] 抽取“正文逻辑” Tab。
    - [ ] 增加并实现“分页/插件”独立的配置 Tab。

- [ ] **Phase 3: 插件联动与优化**
    - [ ] 增加高级插件 Master Toggle 视觉效果。
    - [ ] 优化编辑器表单样式及校验。
    - [ ] 验证保存及热重载动作的准确性。

- [ ] **Phase 4: 质量门禁 (Verify)**
    - [ ] 检查所有表单的绑定正确性。
    - [ ] 检查不同屏幕尺寸下的布局。
