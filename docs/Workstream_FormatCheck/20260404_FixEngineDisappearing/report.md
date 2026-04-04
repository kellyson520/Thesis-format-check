# v1.2.4 引擎稳定性修复任务报告 (Task Report)

## 任务概况 (Summary)
成功修复了用户反馈的“引擎运行中状态消失”问题，并额外解决了文件导出时在大文档或中文文件名下的编码崩溃 Bug。系统版本已升级至 `1.2.4`。

## 架构变更 (Architecture Refactor)
- **ValidatorPipeline (Use Cases Layer)**: 
    - 补齐了 `event_type` 字段以匹配前端 Vue 监听逻辑。
    - 统一了事件名称，将 `complete` 改为 `done`。
    - 强化了流式 Issue 对象的序列化，显式注入 `type` (severity) 和 `fixable` 指示，解决了前端渲染时的属性缺失。
- **main.py (Infrastructure Layer)**:
    - 引入 `urllib.parse.quote` 处理 `Content-Disposition` 中的非 ASCII 文件名。
    - 采用 `filename*` 标准化 RFC 5987 格式，确保文件名在 Windows 环境下不乱码且不导致 Header 注入报错。

## 质量验证 (Verification)
- **单元与集成测试**: 更新并成功运行 `tests/test_api_integration.py`。
- **关键路径验证**:
    - [x] SSE 流式进度推送（含有 `event_type`）
    - [x] 校验完成状态 (`loading -> results`)
    - [x] 带中文附件的文件修复下载（无 `UnicodeEncodeError`）

## 操作手册 (Manual)
无需额外操作。本次更新为热补丁，前端与后端已完全解耦并重新对齐。
