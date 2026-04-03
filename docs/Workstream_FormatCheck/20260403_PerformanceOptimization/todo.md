# 长文档性能优化

## 背景 (Context)
纯 Python 字符串与 DOM 遍历处理几百页 `.docx` 时 CPU 密集，可能耗时 15-30 秒。FastAPI 的 `async` 无法拯救 CPU 密集型任务，反复实时编译正则也造成额外开销。

## 策略 (Strategy)
引入 `ProcessPoolExecutor` 后台执行解析/校验；在 Validator 初始化时预编译所有正则；将 `DocxParser` 改造为 Generator 模式实现流式校验降低峰值内存。

## 待办清单 (Checklist)

### Phase 1: 正则预编译
- [ ] 清点 Validator 中所有 `re.match` / `re.search` / `re.compile` 调用
- [ ] 将所有正则移至 `Validator.__init__` 中预编译（`self._re_caption`, `self._re_ref` 等）
- [ ] 估算性能收益（处理10000段落时的耗时对比）
- [ ] 编写基准测试 `tests/performance/test_regex_benchmark.py`

### Phase 2: Generator 模式重构
- [ ] 将 `DocxParser.parse()` 改为 `parse_stream() -> Generator[dict, None, None]`
- [ ] 修改 Validator 入口接受 Generator 输入
- [ ] 测试峰值内存：100页文档重构前后对比（目标降低 ≥ 40%）

### Phase 3: 多进程/后台任务
- [ ] 评估：`ProcessPoolExecutor` vs FastAPI `BackgroundTasks` 适用场景
- [ ] 实现后台任务包装器 `async def run_check_in_background(file_path: str)`
- [ ] 添加任务状态追踪（任务ID → 进度/结果）
- [ ] 与 T9（IPCProgress SSE接口）对齐接口设计

### Phase 4: 验证
- [ ] 使用 300 页博士论文 fixture 进行端到端性能测试
- [ ] 目标：总耗时 ≤ 10s（重构前估算 > 20s）
