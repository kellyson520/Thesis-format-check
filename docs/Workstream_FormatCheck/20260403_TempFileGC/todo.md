# 垃圾回收与临时文件管理

## 背景 (Context)
系统依赖本地硬盘读写（`data/` / `tests/temp/`）。用户连续上传50次文档进行调试后，临时文件夹会迅速堆积废弃的 `.docx` 文件。崩溃时也无清理保障。

## 策略 (Strategy)
引入 Zero-Disk IO 策略：文件在内存用 `io.BytesIO` 流转，非必要绝不落盘；仅当用户点击"导出报告"时才写入用户指定路径。同时实现 FastAPI Lifespan 清理钩子。

## 待办清单 (Checklist)

### Phase 1: Zero-Disk IO 重构
- [ ] 将 `DocxParser` 入参改为接受 `bytes | io.BytesIO` 而非文件路径字符串
- [ ] 将上传文件直接在内存处理（FastAPI `UploadFile.read()` → `io.BytesIO`）
- [ ] 将 Fixer 输出改为 `io.BytesIO` 流，由用户触发"导出"时才 `write()`
- [ ] 删除所有 `open(path, 'wb')` 中间落盘逻辑

### Phase 2: Lifespan 清理钩子
- [ ] 使用 FastAPI `lifespan` context manager
- [ ] 启动时：扫描 `data/temp/` 目录，清理超过24小时的旧文件
- [ ] 关闭时：清理所有本次会话产生的临时文件
- [ ] 使用 `tempfile.TemporaryDirectory()` context manager 管理临时目录生命周期

### Phase 3: 文件 TTL 策略（可选）
- [ ] 为已完成 job 的结果文件设置 TTL（如30分钟）
- [ ] 实现后台定时清理任务（`asyncio.create_task` 定时器）

### Phase 4: 验证
- [ ] 测试：连续上传50次文档后，`data/temp/` 目录文件数量 ≤ 5
- [ ] 测试：进程强杀后重启，旧临时文件被clean
- [ ] 性能测试：Zero-Disk IO vs 落盘模式处理速度对比
