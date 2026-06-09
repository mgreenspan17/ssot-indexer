import json
import os
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


@router.get("/api/scan/sample_record")
def api_scan_sample_record(output_dir: str = "/home/mannieg/ssot-indexer/scan_results") -> dict[str, Any]:
    paths_to_check = [
        Path(output_dir),
        Path("/srv/data/ssot/scan_results"),
        Path("/home/mannieg/ssot-indexer/scan_results")
    ]
    manifest_file = None
    
    for p in paths_to_check:
        if p.exists():
            jsonl_files = sorted(
                p.glob("scan_manifest_*.jsonl"),
                key=lambda f: f.stat().st_mtime,
                reverse=True
            )
            if jsonl_files:
                manifest_file = jsonl_files[0]
                break
                
    if not manifest_file or not manifest_file.exists():
        raise HTTPException(status_code=404, detail="No scan manifest files found to sample")
        
    try:
        last_line = ""
        with open(manifest_file, "rb") as f:
            try:
                # Seek to near the end of the file
                f.seek(-2, os.SEEK_END)
                # Read backwards to find the last newline character
                while f.read(1) != b'\n':
                    f.seek(-2, os.SEEK_CUR)
                last_line = f.readline().decode("utf-8").strip()
            except OSError:
                # If file is too small or other error, seek back to start
                f.seek(0)
                last_line = f.readline().decode("utf-8").strip()
                
        # If last line was empty (e.g. trailing newline at end of file), try reading again from end
        if not last_line:
            with open(manifest_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1].strip()
                    
        if last_line:
            return json.loads(last_line)
        else:
            raise HTTPException(status_code=404, detail="Manifest file is empty")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read sample record: {str(e)}")
