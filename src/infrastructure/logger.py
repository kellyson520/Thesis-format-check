import logging
import os
import json
from datetime import datetime
from logging.handlers import RotatingFileHandler

class AppLogger:
    """
    统一日志处理器：
    - 输出到控制台 (Console)
    - 输出到本地旋转日志文件 (RotatingFileHandler)
    - 支持结构化 JSON 日志查询 (get_recent_logs)
    """

    def __init__(self, log_dir: str, name: str = "thesis_checker"):
        self.name = name
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)

        self.log_file = os.path.join(log_dir, "app.log")
        self.json_log_file = os.path.join(log_dir, "structured.jsonl")

        # Standard logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        if not self.logger.handlers:
            # Console handler
            console = logging.StreamHandler()
            console.setLevel(logging.INFO)
            console.setFormatter(logging.Formatter(
                "[%(asctime)s][%(levelname)s] %(message)s",
                datefmt="%H:%M:%S"
            ))

            # File handler with rotation (max 2MB, 3 backups)
            file_handler = RotatingFileHandler(
                self.log_file, maxBytes=2 * 1024 * 1024,
                backupCount=3, encoding="utf-8"
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(logging.Formatter(
                "[%(asctime)s][%(levelname)s][%(name)s] %(message)s"
            ))

            self.logger.addHandler(console)
            self.logger.addHandler(file_handler)

    def _write_json(self, level: str, message: str, extra: dict = None):
        """Append a structured JSON line to the structured log."""
        record = {
            "ts": datetime.now().isoformat(),
            "level": level,
            "msg": message,
            "extra": extra or {}
        }
        try:
            with open(self.json_log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception:
            pass  # Never let logging bring down the engine

    def info(self, message: str, extra: dict = None):
        self.logger.info(message)
        self._write_json("INFO", message, extra)

    def warning(self, message: str, extra: dict = None):
        self.logger.warning(message)
        self._write_json("WARNING", message, extra)

    def error(self, message: str, extra: dict = None):
        self.logger.error(message)
        self._write_json("ERROR", message, extra)

    def debug(self, message: str, extra: dict = None):
        self.logger.debug(message)
        self._write_json("DEBUG", message, extra)

    def get_recent_logs(self, limit: int = 100, level_filter: str = None) -> list:
        """从结构化日志文件中读取最近 N 条，可按级别过滤。"""
        records = []
        if not os.path.exists(self.json_log_file):
            return records
        with open(self.json_log_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                    if level_filter is None or r.get("level") == level_filter.upper():
                        records.append(r)
                except json.JSONDecodeError:
                    continue
        return records[-limit:]  # Most recent last

    def clear_logs(self):
        """清空结构化日志文件。"""
        with open(self.json_log_file, "w", encoding="utf-8") as f:
            f.write("")
        self.info("日志已手动清空", extra={"action": "clear_logs"})
