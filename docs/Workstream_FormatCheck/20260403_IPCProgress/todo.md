# IPC 通信优化与实时进度条

## 背景 (Context)
300页博士论文处理可能需要15-30秒，普通 HTTP 请求导致前端长时间"假死"，用户不知道系统是卡死还是在处理中，极易强制关闭软件。需要引入实时进度推送机制。

## 策略 (Strategy)
引入 Server-Sent Events (SSE) 或 WebSocket，后端在解析DOM、校验规则、生成报告各阶段实时推送进度百分比。前端展示平滑进度条替代简单转圈。

## 待办清单 (Checklist)

### Phase 1: 后端 SSE 接口
- [ ] 设计进度事件数据结构
  ```json
  {"stage": "parsing_dom", "progress": 20, "message": "正在解析文档结构..."}
  {"stage": "validating", "progress": 65, "message": "校验第 3/12 章..."}
  {"stage": "generating_report", "progress": 90, "message": "生成校验报告..."}
  {"stage": "done", "progress": 100, "result_url": "/api/result/{job_id}"}
  ```
- [ ] 实现 `GET /api/check/stream/{job_id}` SSE 端点（`EventSourceResponse`）
- [ ] 在 `DocxParser` 和 `Validator` 中注入进度回调 `progress_callback: Callable`
- [ ] 与 T4（后台任务队列）对齐，任务在 `ProcessPoolExecutor` 中回调主进程

### Phase 2: 前端进度条 UI
- [ ] 设计"毛玻璃风格"进度条组件（`ProgressPanel.vue`）
  - 阶段图标 + 文字描述
  - 平滑动画百分比填充
  - 完成后3秒自动切换到结果页
- [ ] 接入 `EventSource` API 监听 SSE 流
- [ ] 断线重连机制（网络抖动或超时自动 retry）

### Phase 3: 超时保护
- [ ] 设定最大处理超时（120秒），超时后推送 `{"stage": "timeout", "error": "..."}`
- [ ] 前端显示超时提示并提供"重试"按钮

### Phase 4: 验证
- [ ] 端到端测试：上传300页文档，SSE事件流正常推送
- [ ] UI 测试：进度条动画流畅，阶段切换无闪烁
