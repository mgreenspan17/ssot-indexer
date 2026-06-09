from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(tags=["dashboard"])

BASE_DIR = Path(__file__).resolve().parent.parent
DASHBOARD_DIR = BASE_DIR / "dashboard"


@router.get("/")
def dashboard_root() -> FileResponse:
    if not (DASHBOARD_DIR / "index.html").exists():
        raise HTTPException(status_code=404, detail="Dashboard index.html not found")
    return FileResponse(DASHBOARD_DIR / "index.html")


@router.get("/dashboard.js")
def dashboard_js() -> FileResponse:
    if not (DASHBOARD_DIR / "dashboard.js").exists():
        raise HTTPException(status_code=404, detail="Dashboard dashboard.js not found")
    return FileResponse(DASHBOARD_DIR / "dashboard.js")


@router.get("/dashboard.css")
def dashboard_css() -> FileResponse:
    if not (DASHBOARD_DIR / "dashboard.css").exists():
        raise HTTPException(status_code=404, detail="Dashboard dashboard.css not found")
    return FileResponse(DASHBOARD_DIR / "dashboard.css")


@router.get("/api/scan/state")
def api_scan_state(state_path: str = "/tmp/ssot_scan_state.json") -> dict[str, Any]:
    path = Path(state_path)
    if not path.exists():
        return {
            "status": "idle",
            "started_at": "",
            "current_file": "",
            "files_indexed": 0,
            "files_total_estimate": 0,
            "bytes_hashed": 0,
            "errors": 0,
            "error_log": [],
            "recent_files": [],
            "files_per_second": 0.0,
            "elapsed_seconds": 0.0,
            "eta_seconds": 0.0,
            "roots": [],
            "current_root": "",
            "current_root_index": 0,
            "total_roots": 0
        }
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"status": "error", "error": str(e)}
