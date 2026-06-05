from __future__ import annotations

import os
from datetime import datetime, timezone
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, sort_keys=True)


def configure_logging(log_dir: str | Path | None = None, level: int = logging.INFO) -> logging.Logger:
    if log_dir is None:
        log_dir = os.environ.get("SSOT_LOG_DIR", "/var/log/ssot-indexer")
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(JsonFormatter())
    root.addHandler(stream_handler)

    file_handler = RotatingFileHandler(log_path / "ssot-indexer.log", maxBytes=5 * 1024 * 1024, backupCount=5)
    file_handler.setFormatter(JsonFormatter())
    root.addHandler(file_handler)
    return root


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

