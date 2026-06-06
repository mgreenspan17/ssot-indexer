"""Heartbeat utilities for SSOT OS.

Assumptions:
- Heartbeats are lightweight status records.

Boundaries:
- This module only creates heartbeat payloads.

Integration notes:
- Warp and Copilot can use the payload for readiness and liveness reporting.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class Heartbeat:
    component: str
    status: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] | None = None


def beat(component: str, status: str = "ok", metadata: dict[str, Any] | None = None) -> Heartbeat:
    return Heartbeat(component=component, status=status, metadata=metadata)
