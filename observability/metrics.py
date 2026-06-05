from __future__ import annotations

from fastapi import FastAPI, Response

try:
    from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest
except Exception:  # pragma: no cover - optional dependency fallback
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4"

    class _Counter:
        def labels(self, *args, **kwargs):
            return self

        def inc(self, amount: float = 1.0) -> None:
            return None

    def Counter(*args, **kwargs):  # type: ignore[misc]
        return _Counter()

    def generate_latest() -> bytes:  # type: ignore[misc]
        return b""


REQUEST_COUNTER = Counter("ssot_requests_total", "Total SSOT requests", ["component"])


def create_metrics_app() -> FastAPI:
    app = FastAPI(title="SSOT Metrics")

    @app.get("/")
    def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app


def increment_scan_count() -> None:
    REQUEST_COUNTER.labels("scan").inc()
