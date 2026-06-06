"""Database health check.

Assumptions:
- Database connectivity is checked through the runtime stack when enabled.

Boundaries:
- No live database calls are made here.
"""
from __future__ import annotations


def check() -> dict[str, object]:
    return {"component": "database", "healthy": True, "detail": "database connectivity placeholder healthy"}
