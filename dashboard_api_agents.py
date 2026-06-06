"""Dashboard agent data adapter.

Assumptions:
- Agent runtime telemetry will later be supplied by Warp, Copilot, or the mesh.

Boundaries:
- Read-only adapter only; no agent control actions.

Integration notes:
- Keep function signatures stable so the dashboard can adopt live agent feeds later.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def get_agent_status() -> list[dict[str, Any]]:
    return [
        {
            "name": "Warp",
            "lane": "execution",
            "status": "placeholder",
            "last_seen": datetime.now(timezone.utc).isoformat(),
        },
        {
            "name": "Copilot",
            "lane": "coordination",
            "status": "placeholder",
            "last_seen": datetime.now(timezone.utc).isoformat(),
        },
    ]


def get_agent_health() -> list[dict[str, Any]]:
    return [
        {"name": "Warp", "healthy": True, "detail": "placeholder health"},
        {"name": "Cody", "healthy": True, "detail": "placeholder health"},
    ]


def get_agent_autonomy() -> dict[str, Any]:
    return {
        "Warp": {"execution": 3, "design": 1},
        "Cody": {"artifact_generation": 3, "execution": 0},
        "Copilot": {"coordination": 3, "direct_execution": 0},
        "Experimental": {"compute": 3, "infrastructure": 0},
    }
