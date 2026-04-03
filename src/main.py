import os
import io
import sys
import json
import threading
import shutil
import uvicorn
import secrets
import webview
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
from docx import Document
from docx.shared import RGBColor, Pt
import tempfile

# ── 旧引擎（Shim 层，保持向下兼容）──────────────────────────────────────────
from infrastructure.logger import AppLogger

# ── 新Clean Architecture 层（直接路径）────────────────────────────────────────
from use_cases.rule_config import RuleLoader
from use_cases.validator_pipeline import ValidatorPipeline
from use_cases.fixer_pipeline import FixerPipeline
from infrastructure.parsers.docx_parser import DocxParser
from infrastructure.reporters.docx_fixer import DocxFixer
from infrastructure.reporters.word_reporter import AnnotationReporter


# ─── 路径解析：兼容 PyInstaller 打包与直接开发运行 ───────────────────────────
#
# Release ZIP 目录结构（frozen 模式）:
#   ThesisFormatChecker.exe
#   config/
#     rules.yaml          ← EXE 同级 config/ 下，用户可直接编辑
#   logs/                 ← 运行时自动创建
#
# 开发模式目录结构:
#   src/
#     main.py
#   src/config/rules.yaml

if getattr(sys, "frozen", False):
    # PyInstaller打包运行(--onefile)：内部绑定的静态文件解压到 sys._MEIPASS
    app_root   = sys._MEIPASS
    base_dir   = os.path.dirname(sys.executable)
    config_dir = os.path.join(base_dir, "config")
    rules_path = os.path.join(config_dir, "rules.yaml")
    log_dir    = os.path.join(base_dir, "logs")
    
    # 支持完全独立的单一 EXE（不携带外部包）：如果没有 config 目录或 rules.yaml，从打包内存中复制一份默认的来用。
    if not os.path.exists(rules_path):
        os.makedirs(config_dir, exist_ok=True)
        bundled_rules = os.path.join(app_root, "src", "config", "rules.yaml")
        if os.path.exists(bundled_rules):
            shutil.copy2(bundled_rules, rules_path)
else:
    # 开发模式：使用项目根目录（src/main.py 向上两级）
    base_dir   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_root   = base_dir
    rules_path = os.path.join(base_dir, "src", "config", "rules.yaml")
    log_dir    = os.path.join(base_dir, "logs")

app_logger  = AppLogger(log_dir=log_dir)
rule_loader = RuleLoader(rules_path)
# ValidatorPipeline 基于 RuleConfig（Pydantic 强类型），不再依赖裸字典
_pipeline   = ValidatorPipeline(rule_loader.get_rules())
_fix_pipeline = FixerPipeline(DocxFixer)  # 注册 DocxFixer 工厂


app = FastAPI(title="论文格式校验 API", version="2.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 安全加固：动态 Token 鉴权中间件 ──────────────────────────────────────────
_API_TOKEN = secrets.token_hex(16)

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 静态文件和根路径放行，API 路径必须校验 Token
        if request.url.path.startswith("/api"):
            token = request.headers.get("X-Token")
            if token != _API_TOKEN:
                return JSONResponse(status_code=403, content={"detail": "Access Denied: Invalid Token"})
        return await call_next(request)

app.add_middleware(AuthMiddleware)

# ─── Helpers ─────────────────────────────────────────────────────────────────

def _rebuild_pipeline() -> None:
    """规则热更新后重建 ValidatorPipeline 实例。"""
    global _pipeline
    _pipeline = ValidatorPipeline(rule_loader.get_rules())

# _inject_comment_to_docx 已迁移至 AnnotationReporter（infrastructure/reporters/word_reporter.py）


# ─── API: Document Checking ──────────────────────────────────────────────────

@app.post("/api/check/stream")
async def check_document_stream(file: UploadFile = File(...)):
    """
    在线实时校验（SSE）：上传 Docx，实时流式返回发现的 Issues。
    P2 进度：允许前端显示实时进度条。
    """
    try:
        app_logger.info(f"开始流式校验文件: {file.filename}")
        raw = await file.read()
        
        # 直接使用内存流解析
        parser = DocxParser(io.BytesIO(raw))
        doc_model = parser.parse()

        async def event_generator():
            try:
                # 将同步 Generator 转换为流式生成器
                for event in _pipeline.run(doc_model):
                    # 按照 SSE 规范格式化数据
                    data = json.dumps(event.to_dict(), ensure_ascii=False)
                    yield f"data: {data}\n\n"
            except Exception as inner_e:
                # 中途崩溃时，发送一个特殊的 error 事件
                err_data = json.dumps({"type": "error", "message": f"校验中断: {inner_e}"})
                yield f"data: {err_data}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream"
        )
    except Exception as e:
        app_logger.error(f"流式校验系统异常: {e}")
        # 在 SSE 流中报错通常需要发送一个特定的 error 事件或在 data 中包含错误信息
        return Response(content=f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n", media_type="text/event-stream")


@app.post("/api/check")
async def check_document(file: UploadFile = File(...)):
    """
    在线校验：上传 Docx，返回 Issues JSON。
    P1 升级：实现 Zero-Disk IO，不再落盘临时文件。
    """
    try:
        app_logger.info(f"开始校验文件: {file.filename}")
        raw = await file.read()
        
        # 直接使用内存流解析
        parser    = DocxParser(io.BytesIO(raw))
        doc_model = parser.parse()

        all_issues = []
        for event in _pipeline.run(doc_model):
            for issue in event.issues:
                all_issues.append({
                    "id":         issue.id,
                    "para_index": issue.para_index,
                    "issue_code": issue.issue_code.value,
                    "type":       issue.severity.value,
                    "context":    issue.context,
                    "message":    issue.message,
                    # 将 Patch 转换为字典供前端显示修复建议（可选）
                    "fixable":    issue.suggested_patch is not None
                })

        app_logger.info(f"校验完成: {file.filename} -> 发现 {len(all_issues)} 个问题")
        return JSONResponse(content={
            "issues": all_issues,
            "filename": file.filename,
            "total": len(all_issues),
            "checked_at": datetime.now().isoformat()
        })
    except Exception as e:
        app_logger.error(f"校验失败: {file.filename} -> {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


# ─── API: Annotated Export ────────────────────────────────────────────────────

class ExportRequest(BaseModel):
    filename: str
    issues: list


@app.post("/api/export/annotated")
async def export_annotated(file: UploadFile = File(...), issues_json: str = "[]"):
    """
    上传原始 docx + issues JSON，返回附批注的新 docx 文件流。
    前端可直接触发浏览器下载。
    """
    temp_dir = os.path.join(tempfile.gettempdir(), "thesis_checker_temp")
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, f"_export_{file.filename}")

    raw = await file.read()
    with open(temp_path, "wb") as f:
        f.write(raw)

    try:
        issues_raw = json.loads(issues_json)
        # 使用新 AnnotationReporter（接受旧格式 dict list 以保持 API 兼容）
        from domain.models import Issue, IssueCode, IssueSeverity
        domain_issues = [
            Issue(
                id=i.get("id", 0),
                para_index=i.get("para_index", i.get("id", 0)),
                issue_code=IssueCode(i.get("issue_code", "W005")),
                severity=IssueSeverity(i.get("type", "Warn")),
                context=i.get("context", ""),
                message=i.get("message", ""),
            )
            for i in issues_raw
        ]
        reporter = AnnotationReporter(temp_path)
        annotated_bytes = reporter.generate(domain_issues)
        out_name = file.filename.replace(".docx", "_校验批注.docx")
        return Response(
            content=annotated_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{out_name}"'}
        )
    except Exception as e:
        app_logger.error(f"批注导出失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass


@app.post("/api/fix")
async def fix_document(file: UploadFile = File(...)):
    """
    一键自动修复：上传 Docx，后端执行全量校验并应用 Patch，返回修复后的 Docx。
    """
    try:
        app_logger.info(f"开始自动修复文件: {file.filename}")
        raw = await file.read()
        
        # 1. 执行校验获取 Issues（包含 Patch）
        parser    = DocxParser(io.BytesIO(raw))
        doc_model = parser.parse()
        
        all_issues = []
        for event in _pipeline.run(doc_model):
            all_issues.extend(event.issues)
            
        # 2. 执行修复
        fixed_bytes = _fix_pipeline.apply_fixes(raw, all_issues)

        out_name = file.filename.replace(".docx", "_格式已修复.docx")
        app_logger.info(f"一键自动修复完成: {out_name}")
        
        return Response(
            content=fixed_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{out_name.encode("utf-8").decode("latin-1")}"'}
        )
    except Exception as e:
        app_logger.error(f"自动化修复失败: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


# ─── API: Rules Management ────────────────────────────────────────────────────

@app.get("/api/rules/summary")
async def get_rules_summary():
    """返回当前生效规则摘要，用于前端卡片展示。"""
    try:
        summary = rule_loader.get_summary()
        app_logger.info("获取规则摘要成功")
        return JSONResponse(content=summary)
    except Exception as e:
        app_logger.error(f"获取规则摘要失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rules/libraries")
async def get_libraries():
    """获取所有可用的规则库 (.yaml)。"""
    try:
        lib_dir = os.path.join(app_root, "config") if getattr(sys, "frozen", False) else os.path.join(app_root, "src", "config")
        if not os.path.exists(lib_dir):
            return JSONResponse(content={"libraries": [], "current": ""})
        files = [f for f in os.listdir(lib_dir) if f.endswith(".yaml") or f.endswith(".yml")]
        app_logger.info(f"扫描规则库成功，发现 {len(files)} 个文件")
        return JSONResponse(content={"libraries": files, "current": os.path.basename(rules_path)})
    except Exception as e:
        app_logger.error(f"获取规则库列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rules/switch")
async def switch_library(filename: str):
    """一键切换到选定的规则库文件并热重载。"""
    global rules_path
    lib_dir = os.path.join(app_root, "config") if getattr(sys, "frozen", False) else os.path.join(app_root, "src", "config")
    new_path = os.path.join(lib_dir, filename)
    if not os.path.exists(new_path):
        raise HTTPException(status_code=404, detail="Rule file not found")
    
    rules_path = new_path
    rule_loader.filepath = new_path
    rule_loader.reload()
    _rebuild_pipeline()
    return JSONResponse(content={"status": "ok", "message": f"规则已切换至 {filename}"})


@app.get("/api/rules/export/yaml")
async def export_rules_yaml():
    """导出当前规则为 YAML 文件下载。"""
    yaml_content = rule_loader.export_as_yaml()
    return Response(
        content=yaml_content.encode("utf-8"),
        media_type="application/x-yaml",
        headers={"Content-Disposition": 'attachment; filename="rules_export.yaml"'}
    )


@app.get("/api/rules/export/json")
async def export_rules_json():
    """导出当前规则为 JSON 文件下载。"""
    json_content = rule_loader.export_as_json()
    return Response(
        content=json_content.encode("utf-8"),
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="rules_export.json"'}
    )

@app.get("/api/rules/full_json")
async def get_full_rules_json():
    """返回完整规则JSON对象（用于可视化编辑器绑定）。"""
    return JSONResponse(content=rule_loader.get_rules().model_dump())

@app.post("/api/rules/save_json")
async def save_rules_json(rules: Dict[Any, Any]):
    """接收完整JSON对象覆写当前规则并重载。"""
    try:
        json_str = json.dumps(rules, ensure_ascii=False)
        result = rule_loader.import_from_json(json_str)
        _rebuild_pipeline()
        app_logger.info("规则文件通过可视化编辑器成功覆盖")
        return JSONResponse(content=result)
    except Exception as e:
        app_logger.error(f"规则保存失败: {e}")
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/api/rules/import")
async def import_rules(file: UploadFile = File(...)):
    """
    上传自定义规则文件（.yaml 或 .json），经校验后覆盖当前规则并热重载。
    """
    content = (await file.read()).decode("utf-8")
    fname = file.filename or ""
    try:
        if fname.endswith(".json"):
            result = rule_loader.import_from_json(content)
        else:
            result = rule_loader.import_from_yaml(content)
        _rebuild_pipeline()
        app_logger.info(f"规则文件已更新: {fname}", extra={"file": fname})
        return JSONResponse(content=result)
    except ValueError as e:
        app_logger.error(f"规则导入失败: {e}")
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/api/rules/reload")
async def reload_rules():
    """强制从磁盘热重载规则（无需重启服务）。"""
    try:
        rule_loader.reload()
        _rebuild_pipeline()
        app_logger.info("规则热重载成功")
        return JSONResponse(content={"status": "ok", "message": "规则热重载完成"})
    except Exception as e:
        app_logger.error(f"规则热重载失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─── API: Logs ────────────────────────────────────────────────────────────────

@app.get("/api/logs")
async def get_logs(limit: int = 100, level: str = None):
    """返回最近结构化日志记录列表。"""
    records = app_logger.get_recent_logs(limit=limit, level_filter=level)
    return JSONResponse(content={"logs": records, "count": len(records)})


@app.delete("/api/logs")
async def clear_logs():
    """清空日志文件。"""
    app_logger.clear_logs()
    return JSONResponse(content={"status": "ok", "message": "日志已清空"})


# ─── API: Settings & System ──────────────────────────────────────────────────
from version import VERSION, BUILD_DATE

@app.get("/api/settings")
async def get_settings():
    """获取系统信息与插件列表状态。"""
    cfg = rule_loader.get_rules()
    
    # 动态构建插件列表
    plugins = []
    plugin_display_names = {
        "font": "字体格式校验",
        "spacing": "段落间距校验",
        "pagination": "Word 高级排版校验",
        "hierarchy": "标题层级合法性",
        "references": "GB/T 7714 参考文献"
    }
    
    for pid, name in plugin_display_names.items():
        if hasattr(cfg, pid):
            pcfg = getattr(cfg, pid)
            if hasattr(pcfg, "enabled"):
                plugins.append({"id": pid, "name": name, "enabled": pcfg.enabled})
    
    # 获取缓存大小 (MB)
    temp_dir = os.path.join(tempfile.gettempdir(), "thesis_checker_temp")
    sz = 0
    if os.path.exists(temp_dir):
        for f in os.listdir(temp_dir):
            fp = os.path.join(temp_dir, f)
            if os.path.isfile(fp):
                sz += os.path.getsize(fp)
    
    return JSONResponse(content={
        "version": VERSION,
        "build_date": BUILD_DATE,
        "plugins": plugins,
        "cache_size_mb": round(sz / (1024 * 1024), 2),
        "rules_file": os.path.basename(rules_path)
    })


@app.post("/api/settings/plugin")
async def update_plugin_status(request: Request):
    """开启或关闭指定插件。"""
    body = await request.json()
    plugin_id = body.get("id")
    enabled = body.get("enabled", True)
    
    if not plugin_id:
        raise HTTPException(status_code=400, detail="Missing id")
    
    ok = rule_loader.set_plugin_enabled(plugin_id, enabled)
    if ok:
        _rebuild_pipeline()
        return {"status": "ok", "message": f"Plugin {plugin_id} { 'enabled' if enabled else 'disabled' }"}
    else:
        return JSONResponse(status_code=404, content={"message": f"Plugin {plugin_id} not found or not supporting toggle"})


@app.post("/api/settings/clear_cache")
async def clear_cache():
    """手动清理临时文件与日志。"""
    temp_dir = os.path.join(tempfile.gettempdir(), "thesis_checker_temp")
    deleted = 0
    if os.path.exists(temp_dir):
        for f in os.listdir(temp_dir):
            fp = os.path.join(temp_dir, f)
            try:
                if os.path.isfile(fp):
                    os.remove(fp)
                    deleted += 1
                elif os.path.isdir(fp):
                    shutil.rmtree(fp)
                    deleted += 1
            except: pass
            
    # 只清除旧日志，保留当前日志文件本身
    app_logger.clear_logs() 
    
    return {"status": "ok", "deleted_items": deleted, "message": "Cache cleared successfully"}


@app.get("/api/settings/check_update")
async def check_update():
    """模拟检查更新（实际可对接 GitHub API 或版本服务器）。"""
    # 模拟 30% 概率有新版本
    import random
    has_update = random.random() < 0.3
    if has_update:
        return {
            "has_update": True, 
            "current": VERSION,
            "latest": "1.2.1",
            "changelog": "1. 优化了表格解析性能\n2. 修复了孤行控制检查的一个边缘崩溃"
        }
    else:
        return {"has_update": False, "current": VERSION}




# ─── Static files (Production build) ─────────────────────────────────────────
frontend_dist = os.path.join(app_root, "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")
else:
    from fastapi.responses import HTMLResponse
    @app.get("/")
    async def index_fallback():
        return HTMLResponse(
            "<h1>前端未构建 (Frontend Not Built)</h1>"
            "<p>请在 <code>frontend</code> 目录下运行 <code>npm install</code> 和 <code>npm run build</code>，然后重启当前程序。</p>"
            "<p>Please run <code>npm install</code> and <code>npm run build</code> in the <code>frontend</code> directory, then restart the application.</p>"
        )


# ─── Server Bootstrap ─────────────────────────────────────────────────────────

def start_server(port: int):
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    import socket
    # 动态获取空闲端口
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        listen_port = s.getsockname()[1]

    t = threading.Thread(target=start_server, args=(listen_port,), daemon=True)
    t.start()

    dev_mode = "--dev" in sys.argv
    # 开发模式仍固定 5173 以便于 Vite 调试热重载，生产模式使用随机端口
    if dev_mode:
        url = f"http://127.0.0.1:5173/?token={_API_TOKEN}&port={listen_port}"
    else:
        url = f"http://127.0.0.1:{listen_port}/?token={_API_TOKEN}"

    webview.create_window(
        title=f"论文格式智能校验 · v1.2.0 (Port: {listen_port})",
        url=url,
        width=1200,
        height=840,
        min_size=(900, 600),
        resizable=True,
    )
    webview.start()
