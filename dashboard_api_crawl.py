"""Dashboard crawl data adapter.

Assumptions:
- Warp will later supply live crawl batches and progress metrics.
- Placeholder values are acceptable until that integration exists.

Boundaries:
- Read-only adapter only; no crawling or mutation.

Integration notes:
- Replace the placeholder functions with live crawl-store lookups without changing dashboard callers.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def get_crawl_progress() -> dict[str, Any]:
    return {
        "stage": "placeholder",
        "completed": 0.0,
        "queued": 0,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


def get_recent_batches() -> list[dict[str, Any]]:
    return [
        {
            "batch_id": "placeholder-batch-001",
            "status": "pending",
            "records": 0,
            "submitted_at": datetime.now(timezone.utc).isoformat(),
        }
    ]


def get_crawl_status() -> dict[str, Any]:
    return {
        "healthy": True,
        "mode": "placeholder",
        "summary": "Crawl data adapter is awaiting live Warp feed integration.",
    }
