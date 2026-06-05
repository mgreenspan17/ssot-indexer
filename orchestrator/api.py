from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from observability.logging import configure_logging, get_logger
from observability.metrics import create_metrics_app
from observability.tracing import configure_tracing
from orchestrator.service import SSOTOrchestrator
from orchestrator.registry import RegistryCache, RegistryMetadata
from resolver.zpath import resolve_z_path

logger = get_logger(__name__)


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

    # Registry integration
    registry_enabled = os.getenv("SSOT_REGISTRY_ENABLED", "false").lower() == "true"
    registry_url = os.getenv("SSOT_REGISTRY_URL", "http://127.0.0.1:9000")
    registry_cache = RegistryCache(registry_url) if registry_enabled else None

    if registry_cache:
        logger.info(f"MCP Registry enabled at {registry_url}")
    else:
        logger.info("MCP Registry disabled")

    @app.on_event("startup")
    async def startup():
        if registry_cache:
            try:
                metadata = await registry_cache.load_all_sections()
                logger.info(f"Registry sync complete: {metadata.sync_status}")
            except Exception as exc:
                logger.error(f"Registry sync failed: {exc}")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/registry/remote")
    def registry_remote() -> dict:
        if not registry_cache:
            return {"error": "Registry not enabled", "registry_enabled": False}

        metadata = registry_cache.get_metadata()
        if not metadata:
            return {
                "error": "Registry not yet synced",
                "registry_url": registry_cache.registry_url,
            }

        return {
            "registry_url": registry_cache.registry_url,
            "metadata": metadata.model_dump(),
            "sections": registry_cache.get_all(),
            "sync_complete": registry_cache.is_loaded(),
        }

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
