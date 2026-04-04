# 改进异常处理技术方案 (Exception Handling Spec)

## 目标 (Objective)
建立一套统一、分层且"拒绝静默错误"的错误处理框架。

## API 层：FastAPI 全局拦截器 (L3 Infrastructure/Adapter)

使用 FastAPI 的 `exception_handler` 捕获所有 `Exception`：
```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from infrastructure.logger import get_logger

logger = get_logger(__name__)

def setup_exception_handlers(app: FastAPI):
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Global error on {request.url.path}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "message": str(exc),
                "type": type(exc).__name__
            }
        )
```

## 基础设施层：安全降级模式 (L3 Infrastructure)
针对如样式解析 (`StyleResolver`) 的辅助功能，若解析单项属性失败，不应导致整个解析流程崩溃，但必须标记 `debug` 日志，而不是 `pass`。

```python
# 修改前
try:
    val = some_op()
except: 
    pass

# 修改后
try:
    val = some_op()
except Exception as e:
    logger.debug(f"Failed to get value from some_op: {e}")
    val = default_val
```

## 业务逻辑层：分片故障隔离 (L2 UseCase)
`ValidatorPipeline` 在执行规则时，如果一个 `Plugin` 出错，应记录日志并将该规则标记为 `Incomplete`，而不应中断对其余段落的检查。

## 待修复清单 (Grep Audit Result)
- `src/main.py:501`: `except: pass` -> 记录调试信息。
- `src/infrastructure/parsers/style_resolver.py`: 多处 `except Exception:` -> 替换为具体异常并记录 Debug 日志。
- `src/infrastructure/updater.py`: 异常信息未有效上报前端。
