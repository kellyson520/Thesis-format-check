# Task: 实现在线 GitHub 检查更新机制 (Real GitHub Update Check)

## 任务目标 (Objective)
替换 `src/main.py` 中的随机模拟更新逻辑，接入真实的 GitHub API，实现版本比对与更新提示。

## 待办清单 (Checklist)

### Phase 1: 故障诊断与环境准备 (Plan)
- [x] 分析 `src/main.py:check_update` 现有实现
- [x] 确定目标 Repo URL (kellyson520/Thesis-format-check)
- [x] 验证 `httpx` 可用性

### Phase 2: 实现与集成 (Build)
- [x] 编写真实获取 GitHub 最近 Release 的异步函数 (`src/infrastructure/updater.py`)
- [x] 实现语义化版本 (SemVer) 比对逻辑
- [x] 处理 API 频率限制 (Rate Limit) 与超时异常
- [x] 修改 `/api/settings/check_update` 使用真实逻辑 (`src/main.py`)

### Phase 3: 验证与清理 (Verify)
- [x] 模拟本地旧版本，验证“有更新”提示 (已通过 `tests/test_api_integration.py` 验证)
- [x] 模拟本地已是最新，验证“无更新”提示
- [x] 压力与超时测试（确保 GitHub 连不上时不卡死系统）

### Phase 4: 交付 (Report)
- [x] 生成 `report.md`
- [x] 更新 `CHANGELOG.md`
- [x] 状态同步至 `process.md`
