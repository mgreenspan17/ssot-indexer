"""Metadata store for SSOT OS.

Assumptions:
- Metadata is small, structured, and key-addressable.

Boundaries:
- No persistence backend is implied; this is an importable abstraction.

Integration notes:
- Replace the in-memory dict with SQLite, Postgres, or object storage later.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MetadataStore:
    records: dict[str, dict[str, Any]] = field(default_factory=dict)

    def write(self, key: str, value: dict[str, Any]) -> None:
        self.records[key] = value

    def read(self, key: str) -> dict[str, Any] | None:
        return self.records.get(key)
