import os
import io
import sys
import json
import threading
import shutil
import uvicorn
import webview
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
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
from infrastructure.parsers.docx_parser import DocxParser
from infrastructure.reporters.word_reporter import AnnotationReporter, DocumentFixer

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


app = FastAPI(title="论文格式校验 API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Helpers ─────────────────────────────────────────────────────────────────

def _rebuild_pipeline() -> None:
    """规则热更新后重建 ValidatorPipeline 实例。"""
    global _pipeline
    _pipeline = ValidatorPipeline(rule_loader.get_rules())

# _inject_comment_to_docx 已迁移至 AnnotationReporter（infrastructure/reporters/word_reporter.py）


# ─── API: Document Checking ──────────────────────────────────────────────────

@app.post("/api/check")
async def check_document(file: UploadFile = File(...)):
    temp_dir = os.path.join(tempfile.gettempdir(), "thesis_checker_temp")
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, file.filename)

    raw = await file.read()
    with open(temp_path, "wb") as f:
        f.write(raw)

    try:
        app_logger.info(f"开始校验文件: {file.filename}", extra={"filename": file.filename})

        # 新架构：DocxParser → DocumentModel → ValidatorPipeline（Generator）
        parser    = DocxParser(temp_path)
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
                })

        app_logger.info(
            f"校验完成: {file.filename} → 发现 {len(all_issues)} 个问题",
            extra={"filename": file.filename, "issue_count": len(all_issues)}
        )
        return JSONResponse(content={
            "issues": all_issues,
            "filename": file.filename,
            "total": len(all_issues),
            "checked_at": datetime.now().isoformat()
        })
    except Exception as e:
        app_logger.error(f"校验失败: {file.filename} → {e}", extra={"filename": file.filename, "error": str(e)})
        return JSONResponse(status_code=500, content={
            "issues": [{"id": 0, "type": "Error", "context": "System", "message": f"解析异常: {e}"}],
            "filename": file.filename,
            "total": 1,
            "checked_at": datetime.now().isoformat()
        })
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass


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
    一键自动修复格式，返回已修复规范的 Docx 文件。
    """
    temp_dir = os.path.join(tempfile.gettempdir(), "thesis_checker_temp")
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, f"_fix_{file.filename}")

    raw = await file.read()
    with open(temp_path, "wb") as f:
        f.write(raw)

    try:
        app_logger.info(f"开始自动修复文件: {file.filename}")
        # 新 DocumentFixer 接受 RuleConfig（Pydantic 强类型）
        fixer = DocumentFixer(temp_path, rule_loader.get_rules())
        fixed_bytes = fixer.fix()

        out_name = file.filename.replace(".docx", "_格式已修复.docx")
        app_logger.info(f"一键自动修复完成: {out_name}")
        
        return Response(
            content=fixed_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{out_name}"'}
        )
    except Exception as e:
        app_logger.error(f"自动化修复失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass


# ─── API: Rules Management ────────────────────────────────────────────────────

@app.get("/api/rules/summary")
async def get_rules_summary():
    """返回当前生效规则摘要，用于前端卡片展示。"""
    return JSONResponse(content=rule_loader.get_summary())


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

def start_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")


if __name__ == "__main__":
    t = threading.Thread(target=start_server, daemon=True)
    t.start()

    dev_mode = "--dev" in sys.argv
    url = "http://127.0.0.1:5173" if dev_mode else "http://127.0.0.1:8000"

    webview.create_window(
        title="论文格式智能校验 · PC极客端",
        url=url,
        width=1200,
        height=840,
        min_size=(900, 600),
        resizable=True,
    )
    webview.start()
