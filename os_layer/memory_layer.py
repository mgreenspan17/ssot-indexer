"""Memory layer for SSOT OS.

Assumptions:
- Memory records are agent-visible but not agent-owned.

Boundaries:
- This module stores and returns structured data only.

Integration notes:
- Pair with metadata_store, embedding_store, and registry_cache for richer memory surfaces.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MemoryLayer:
    facts: dict[str, dict[str, Any]] = field(default_factory=dict)

    def put(self, key: str, value: dict[str, Any]) -> None:
        self.facts[key] = value

    def get(self, key: str) -> dict[str, Any] | None:
        return self.facts.get(key)

    def list_keys(self) -> tuple[str, ...]:
        return tuple(sorted(self.facts))
