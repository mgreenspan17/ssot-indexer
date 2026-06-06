"""Dashboard governance data adapter.

Assumptions:
- Governance metadata will eventually come from the canonical SSOT policy and registry mirror.

Boundaries:
- Read-only adapter only; no governance mutation.

Integration notes:
- Dashboard consumers can query these functions now and switch to live governance storage later.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def get_governance_version() -> str:
    return "1.0.0"


def get_governance_checksum() -> str:
    return "<placeholder-checksum>"


def get_governance_last_updated() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_governance_status() -> dict[str, Any]:
    return {
        "version": get_governance_version(),
        "checksum": get_governance_checksum(),
        "last_updated": get_governance_last_updated(),
        "source": "/registry/agent-governance",
    }
