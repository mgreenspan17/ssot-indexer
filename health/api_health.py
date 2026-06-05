from __future__ import annotations

from orchestrator.api import create_app


def check() -> bool:
    app = create_app()
    return app.title == "SSOT Indexer"


def status() -> str:
    return "ok" if check() else "degraded"


def summary() -> dict[str, str]:
    return {"component": "api", "status": status(), "detail": "FastAPI app loads"}

