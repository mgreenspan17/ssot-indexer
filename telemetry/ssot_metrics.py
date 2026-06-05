from __future__ import annotations

from observability.metrics import create_metrics_app, increment_scan_count


def metrics_app():
    return create_metrics_app()


def scan_observed() -> None:
    increment_scan_count()
