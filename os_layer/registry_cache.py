"""Registry cache abstraction for SSOT OS.

Assumptions:
- The registry mirror is read-mostly and refreshed periodically.

Boundaries:
- This module does not write to the registry mirror.

Integration notes:
- Use it to keep local runtime copies of registry sections and governance metadata.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RegistryCache:
    sections: dict[str, dict[str, Any]] = field(default_factory=dict)
    version: str = "1.0.0"
    checksum: str | None = None

    def update(self, section: str, payload: dict[str, Any]) -> None:
        self.sections[section] = payload

    def get(self, section: str) -> dict[str, Any] | None:
        return self.sections.get(section)
