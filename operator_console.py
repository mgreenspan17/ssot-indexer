"""Operator console for SSOT OS.

Assumptions:
- The console is a coordination surface, not an execution surface.

Boundaries:
- No direct infrastructure mutation.

Integration notes:
- Copilot can expose this through the dashboard or a CLI adapter later.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class OperatorConsole:
    commands: list[dict[str, Any]] = field(default_factory=list)

    def record_command(self, name: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        entry = {"name": name, "payload": payload or {}, "status": "queued"}
        self.commands.append(entry)
        return entry

    def list_commands(self) -> tuple[dict[str, Any], ...]:
        return tuple(self.commands)
