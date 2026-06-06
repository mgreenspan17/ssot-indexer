"""Filesystem health check.

Assumptions:
- Filesystem checks are placeholders until the Warp crawl publishes live storage paths.

Boundaries:
- No writes are performed by this module.
"""
from __future__ import annotations


def check() -> dict[str, object]:
    return {"component": "filesystem", "healthy": True, "detail": "filesystem placeholder healthy"}
