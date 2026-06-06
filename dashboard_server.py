"""Lightweight dashboard server for local operator UI.

Assumptions:
- The dashboard shell in dashboard/ remains unchanged.
- Data adapters currently return placeholder values.

Boundaries:
- This server is local-only and non-invasive.
- It does not modify system state or require systemd.

Integration notes for Warp:
- Replace adapter internals (dashboard_api_*.py) with live feeds.
- Keep route contracts stable so dashboard shell does not need rewrites.
- Safe to run in parallel with crawl because endpoints are read-only.

Run:
- python dashboard_server.py
- Opens at http://localhost:5050
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

import dashboard_api_agents
import dashboard_api_crawl
import dashboard_api_files
import dashboard_api_governance
import dashboard_api_system


BASE_DIR = Path(__file__).resolve().parent
DASHBOARD_DIR = BASE_DIR / "dashboard"


def create_dashboard_server() -> FastAPI:
    app = FastAPI(title="SSOT Dashboard Server", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5050",
            "http://127.0.0.1:5050",
        ],
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    if not DASHBOARD_DIR.exists():
        raise RuntimeError(f"dashboard directory missing: {DASHBOARD_DIR}")

    app.mount("/static", StaticFiles(directory=str(DASHBOARD_DIR)), name="static")

    @app.get("/")
    def root() -> FileResponse:
        return FileResponse(DASHBOARD_DIR / "index.html")

    @app.get("/dashboard.js")
    def dashboard_js() -> FileResponse:
        return FileResponse(DASHBOARD_DIR / "dashboard.js")

    @app.get("/dashboard.css")
    def dashboard_css() -> FileResponse:
        return FileResponse(DASHBOARD_DIR / "dashboard.css")

    @app.get("/components/{component_path:path}")
    def dashboard_components(component_path: str) -> FileResponse:
        file_path = DASHBOARD_DIR / "components" / component_path
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="component not found")
        return FileResponse(file_path)

    @app.get("/api/crawl/progress")
    def api_crawl_progress() -> dict[str, Any]:
        return dashboard_api_crawl.get_crawl_progress()

    @app.get("/api/crawl/recent-batches")
    def api_recent_batches() -> list[dict[str, Any]]:
        return dashboard_api_crawl.get_recent_batches()

    @app.get("/api/crawl/status")
    def api_crawl_status() -> dict[str, Any]:
        return dashboard_api_crawl.get_crawl_status()

    @app.get("/api/files/list")
    def api_list_files(path: str = Query("/srv/data/ssot-ingestion")) -> list[dict[str, Any]]:
        return dashboard_api_files.list_files(path)

    @app.get("/api/files/metadata")
    def api_file_metadata(path: str = Query(...)) -> dict[str, Any]:
        return dashboard_api_files.get_file_metadata(path)

    @app.get("/api/files/search")
    def api_search_files(query: str = Query("")) -> list[dict[str, Any]]:
        return dashboard_api_files.search_files(query)

    @app.get("/api/agents/status")
    def api_agent_status() -> list[dict[str, Any]]:
        return dashboard_api_agents.get_agent_status()

    @app.get("/api/agents/health")
    def api_agent_health() -> list[dict[str, Any]]:
        return dashboard_api_agents.get_agent_health()

    @app.get("/api/agents/autonomy")
    def api_agent_autonomy() -> dict[str, Any]:
        return dashboard_api_agents.get_agent_autonomy()

    @app.get("/api/governance/version")
    def api_governance_version() -> dict[str, str]:
        return {"version": dashboard_api_governance.get_governance_version()}

    @app.get("/api/governance/checksum")
    def api_governance_checksum() -> dict[str, str]:
        return {"checksum": dashboard_api_governance.get_governance_checksum()}

    @app.get("/api/governance/last-updated")
    def api_governance_last_updated() -> dict[str, str]:
        return {"last_updated": dashboard_api_governance.get_governance_last_updated()}

    @app.get("/api/system/health")
    def api_system_health() -> dict[str, Any]:
        return dashboard_api_system.get_system_health()

    @app.get("/api/system/cpu")
    def api_cpu_load() -> dict[str, Any]:
        return dashboard_api_system.get_cpu_load()

    @app.get("/api/system/memory")
    def api_memory_usage() -> dict[str, Any]:
        return dashboard_api_system.get_memory_usage()

    @app.get("/api/system/disk")
    def api_disk_usage() -> dict[str, Any]:
        return dashboard_api_system.get_disk_usage()

    @app.get("/api/dashboard/status")
    def api_dashboard_status() -> dict[str, Any]:
        return {
            "governance_version": dashboard_api_governance.get_governance_version(),
            "agent_status": dashboard_api_agents.get_agent_status(),
            "crawl_progress": dashboard_api_crawl.get_crawl_progress(),
            "file_browser": {
                "entries": dashboard_api_files.list_files("/srv/data/ssot-ingestion"),
            },
            "system_health": dashboard_api_system.get_system_health(),
        }

    return app


app = create_dashboard_server()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5050)
