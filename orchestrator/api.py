from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from observability.logging import configure_logging
from observability.metrics import create_metrics_app
from observability.tracing import configure_tracing
from orchestrator.service import SSOTOrchestrator
from resolver.zpath import resolve_z_path


class ScanRequest(BaseModel):
    target: str


class ResolveRequest(BaseModel):
    z_path: str
    lookup: dict[str, str]


def create_app(orchestrator: SSOTOrchestrator | None = None) -> FastAPI:
    configure_logging()
    configure_tracing()
    app = FastAPI(title="SSOT Indexer", version="1.0.0")
    service = orchestrator or SSOTOrchestrator()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/scan")
    def scan(request: ScanRequest):
        manifest = service.scan(request.target)
        return manifest.to_dict()

    @app.post("/resolve")
    def resolve(request: ResolveRequest):
        try:
            result = resolve_z_path(request.z_path, request.lookup)
        except (ValueError, KeyError) as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return result.__dict__

    metrics_app = create_metrics_app()
    app.mount("/metrics", metrics_app)

    return app
