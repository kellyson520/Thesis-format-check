import os
import io
import sys
import copy
import json
import threading
import uvicorn
import webview
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from docx import Document
from docx.shared import RGBColor, Pt
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from engine.rule_loader import RuleLoader
from engine.validator import Validator
from engine.docx_parser import DocxParser
from engine.logger import AppLogger

# ─── Bootstrap ──────────────────────────────────────────────────────────────
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rules_path = os.path.join(base_dir, "src", "config", "rules.yaml")
log_dir = os.path.join(base_dir, "logs")

app_logger = AppLogger(log_dir=log_dir)
rule_loader = RuleLoader(rules_path)
validator = Validator(rule_loader.get_rules())

app = FastAPI(title="论文格式校验 API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Helpers ─────────────────────────────────────────────────────────────────

def _rebuild_validator():
    """规则热更新后重建 Validator 实例。"""
    global validator
    validator = Validator(rule_loader.get_rules())

def _inject_comment_to_docx(source_path: str, issues: list) -> bytes:
    """
    将校验结果以 Word 批注形式注入原始文档副本，返回字节流。
    每个 issue 对应其 index 段落，附加红色高亮批注。
    """
    doc = Document(source_path)
    issue_map: dict[int, list] = {}
    for issue in issues:
        pid = issue.get("id", 0)
        issue_map.setdefault(pid, []).append(issue)

    for para_idx, para in enumerate(doc.paragraphs, start=1):
        if para_idx not in issue_map:
            continue
        msgs = " | ".join(f"[{i['type']}] {i['message']}" for i in issue_map[para_idx])
        # Append a red-colored run at end of paragraph acting as inline comment
        run = para.add_run(f"  ⚠ {msgs}")
        run.font.color.rgb = RGBColor(0xFF, 0x00, 0x00)
        run.font.size = Pt(9)
        run.italic = True

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.read()


# ─── API: Document Checking ──────────────────────────────────────────────────

@app.post("/api/check")
async def check_document(file: UploadFile = File(...)):
    temp_dir = os.path.join(base_dir, "tests", "temp")
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, file.filename)

    raw = await file.read()
    with open(temp_path, "wb") as f:
        f.write(raw)

    try:
        app_logger.info(f"开始校验文件: {file.filename}", extra={"filename": file.filename})
        parser = DocxParser(temp_path)
        elements = parser.parse()
        issues = validator.validate(elements)

        app_logger.info(
            f"校验完成: {file.filename} → 发现 {len(issues)} 个问题",
            extra={"filename": file.filename, "issue_count": len(issues)}
        )
        return JSONResponse(content={
            "issues": issues,
            "filename": file.filename,
            "total": len(issues),
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
    temp_dir = os.path.join(base_dir, "tests", "temp")
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, f"_export_{file.filename}")

    raw = await file.read()
    with open(temp_path, "wb") as f:
        f.write(raw)

    try:
        issues = json.loads(issues_json)
        annotated_bytes = _inject_comment_to_docx(temp_path, issues)
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
        _rebuild_validator()
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
        _rebuild_validator()
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
frontend_dist = os.path.join(base_dir, "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")


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
