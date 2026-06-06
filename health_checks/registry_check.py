"""Registry health check.

Assumptions:
- Registry availability is verified elsewhere when live data exists.

Boundaries:
- This module is a placeholder read-only diagnostic.
"""
from __future__ import annotations


def check() -> dict[str, object]:
    return {"component": "registry", "healthy": True, "detail": "registry mirror placeholder healthy"}
