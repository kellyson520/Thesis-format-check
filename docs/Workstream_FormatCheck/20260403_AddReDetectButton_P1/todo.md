# 增加重新检测功能按钮 (Add Re-detect Button)

## 背景 (Context)
用户在查看校验结果或修改规则后，希望能快速重新触发对当前已上传文件的校验，而无需重新选择或拖拽文件。

## 策略 (Strategy)
在前端 `App.vue` 中增加一个 `reCheck` 函数，该函数复用现有的 `uploadFile` 逻辑，但针对已存在的文件对象进行操作。在 UI 的操作栏中增加“重新检测”按钮。

## 待办清单 (Checklist)

### Phase 1: 核心逻辑实现
- [x] 在 `App.vue` 中定义 `reCheck` 函数
- [x] 确保 `reCheck` 能够正确重置 `issues`, `progress`, `validationDone` 等状态
- [x] 确保 `reCheck` 调用 `uploadFile` 时逻辑闭环

### Phase 2: UI 集成
- [x] 在结果面板的 `action-row` 中添加“重新检测”按钮
- [x] 调整按钮样式，确保符合现有的设计系统（极简、磨砂、动效）
- [x] 添加加载状态反馈

### Phase 3: 验证与验收
- [x] 手动测试：上传文件 -> 查看结果 -> 点击重新检测 -> 确认进度条与结果更新
- [x] 兼容性检查：确保在不同状态（加载中、已完成、错误）下的按钮表现符合预期
