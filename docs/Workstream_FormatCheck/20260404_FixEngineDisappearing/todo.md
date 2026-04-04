# 修复引擎运行中状态消失问题 (Fix Engine Disappearing After Upload)

## 背景 (Context)
用户反馈在上传论文文件后，界面显示“引擎运行中”，但随后该状态消失且没有输出校验结果。这可能涉及后端崩溃、WebSocket 断开或前端状态管理异常。

## 待办清单 (Checklist)

### Phase 1: 故障诊断 (Discovery)
- [x] 检查 `src/main.py` 及相关路由的日志输出
- [x] 运行 `get_runtime_errors` 获取最近的运行期错误
- [x] 审计 `ValidatorPipeline` 的异常处理逻辑
- [x] 检查前端 WebSocket 监听逻辑及错误处理

### Phase 2: 修复与验证 (Fix & Verify)
- [x] 修复导致的奔溃或中断的具体 Bug
- [x] 增强全局异常捕获，确保引擎状态即使失败也能正确闭环（而非消失）
- [x] 编写针对性单元测试，模拟异常上传流
- [x] 本地验证修复效果

### Phase 3: 交付与归档 (Report)
- [x] 生成 `report.md`
- [x] 更新 `CHANGELOG.md`
- [x] 任务闭环归档
