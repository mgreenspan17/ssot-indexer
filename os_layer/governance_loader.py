"""Governance loader for SSOT OS.

Assumptions:
- The authoritative policy text lives in the canonical governance file or its registry mirror.
- Consumers pass file contents or a file path; the loader does not reach out on its own.

Boundaries:
- No network calls and no mutation of governance sources.

Integration notes:
- Use with governance_validator and governance_enforcer to keep policy loading, checking, and enforcement separated.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

CANONICAL_GOVERNANCE_PATH = Path("/srv/data/ssot-governance/AGENT_GOVERNANCE.md")
REGISTRY_GOVERNANCE_SECTION = "/registry/agent-governance"


@dataclass(frozen=True)
class GovernanceDocument:
    source: str
    text: str
    version: str = "1.0.0"
    updated_at: str | None = None
    checksum: str | None = None
    metadata: dict[str, Any] | None = None


def load_governance_text(path: str | Path = CANONICAL_GOVERNANCE_PATH) -> str:
    return Path(path).read_text(encoding="utf-8")


def load_governance(path: str | Path = CANONICAL_GOVERNANCE_PATH, *, source: str = "canonical") -> GovernanceDocument:
    text = load_governance_text(path)
    return GovernanceDocument(source=source, text=text, metadata={"canonical_path": str(Path(path))})
