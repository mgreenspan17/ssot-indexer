"""Dashboard API for the SSOT homepage.

Assumptions:
- Placeholder data is acceptable until Warp provides live crawl and mesh feeds.

Boundaries:
- Read-only status endpoints only.

Integration notes:
- Frontend consumers can replace the static placeholders with live API calls later.
"""
from __future__ import annotations

from fastapi import FastAPI


def create_dashboard_app() -> FastAPI:
    app = FastAPI(title="SSOT OS Dashboard API", version="1.0.0")

    @app.get("/dashboard/status")
    def status() -> dict[str, object]:
        return {
            "governance_version": "1.0.0",
            "agent_status": [{"name": "Warp", "status": "placeholder"}],
            "crawl_progress": {"completed": 0.0, "queued": 0, "stage": "placeholder"},
            "file_browser": {"entries": []},
            "system_health": {"healthy": True, "checks": []},
        }

    @app.get("/dashboard/governance")
    def governance() -> dict[str, str]:
        return {
            "canonical_source": "/srv/data/ssot-governance/AGENT_GOVERNANCE.md",
            "registry_mirror": "/registry/agent-governance",
        }

    return app
