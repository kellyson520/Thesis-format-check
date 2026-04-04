# 完善项目异常捕获 (Improve Exception Capturing)

## 背景 (Context)
当前项目中存在多处静默错误（如 `except: pass`）或宽泛的 `except Exception` 捕获，导致某些故障发生时无法在日志中体现或反馈给前端，增加了调试难度和系统的不可预测性。

## 技术要求 (Requirements)
1. **拒绝静默错误**: 禁止使用 `except: pass`，除非有极其明确的理由并附带解释注释。如果是预期内的可选操作失败，至少应记录 `debug` 级别日志。
2. **结构化错误响应**: FastAPI 接口在发生未预期错误时，应通过全局异常处理器返回标准的 `4xx/5xx` 响应，内含错误详情，而不是让客户端收到随机的 500 HTML 或静默失败。
3. **分层错误处理**:
    - **Infrastructure 层**: 捕获特定的库错误（如 `docx.AttributeError`），转化为 Domain 层的异常或记录日志。
    - **UseCases 层**: 确保复杂的 `ValidatorPipeline` 在插件执行出错时能捕获并标记特定 Issue，而不是中断整个流程。
    - **Domain 层**: 定义明确的异常基类。
4. **日志对齐**: 所有捕获的 Exception 必须通过 `logger.error(..., exc_info=True)` 记录完整的 Stacktrace。

## 待办清单 (Checklist)

### Phase 1: 现状审计与全局加固
- [ ] 审计 `src/main.py` 中的所有 API 异常捕获逻辑
- [ ] 实现 FastAPI 全局异常拦截器 (exception_handler)
- [ ] 清理已知的所有 `except: pass` 或无日志捕获

### Phase 2: 分层加固
- [ ] 加固 `src/infrastructure/parsers/` 下的 docx 解析异常
- [ ] 确保 `src/infrastructure/updater.py` 的网络请求有重试机制或明确的失败报告
- [ ] 优化 `src/use_cases/validator_pipeline.py`，防止单个插件崩溃导致整个检查中断

### Phase 3: 验证与验收
- [ ] 模拟网络超时/文件损坏测试异常反馈
- [ ] 运行 `local-ci` 确保无回归
- [ ] 生成交付报告 `report.md`
