"""Governance health check.

Assumptions:
- Governance policy is available from the repository copy or registry mirror.

Boundaries:
- Read-only check only.
"""
from __future__ import annotations

from pathlib import Path


def check() -> dict[str, object]:
    path = Path("AGENT_GOVERNANCE.md")
    healthy = path.exists()
    return {"component": "governance", "healthy": healthy, "detail": "governance artifact present" if healthy else "governance artifact missing"}
