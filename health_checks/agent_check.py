"""Agent health check.

Assumptions:
- Agent metadata is surfaced by the runtime, not by this module.

Boundaries:
- This module returns a placeholder check that can be replaced later.
"""
from __future__ import annotations


def check() -> dict[str, object]:
    return {"component": "agent", "healthy": True, "detail": "agent runtime placeholder healthy"}
