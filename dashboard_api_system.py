"""Dashboard system telemetry adapter.

Assumptions:
- Live host telemetry will later arrive from Warp, the scheduler, or host agents.

Boundaries:
- Read-only adapter only; no host inspection side effects.

Integration notes:
- Replace placeholder metrics with live system calls or scraped telemetry later.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def get_system_health() -> dict[str, Any]:
    return {
        "healthy": True,
        "status": "placeholder",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def get_cpu_load() -> dict[str, Any]:
    return {"load_1m": 0.0, "load_5m": 0.0, "load_15m": 0.0}


def get_memory_usage() -> dict[str, Any]:
    return {"used_mb": 0, "total_mb": 0, "percent": 0.0}


def get_disk_usage() -> dict[str, Any]:
    return {
        "root": {"used_gb": 0, "total_gb": 0, "percent": 0.0},
        "raid": {"used_gb": 0, "total_gb": 0, "percent": 0.0},
    }
