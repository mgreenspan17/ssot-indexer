"""OS initialization sequence for SSOT OS.

Assumptions:
- Initialization is a planning artifact until Warp or the scheduler performs the actual boot.

Boundaries:
- This module does not start services.

Integration notes:
- Use heartbeat.py to publish a startup signal after initialization is confirmed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class OSInitStep:
    name: str
    detail: str


@dataclass
class OSBootSequence:
    steps: list[OSInitStep] = field(default_factory=list)

    def add_step(self, name: str, detail: str) -> None:
        self.steps.append(OSInitStep(name=name, detail=detail))

    def as_dict(self) -> list[dict[str, str]]:
        return [{"name": step.name, "detail": step.detail} for step in self.steps]


def build_boot_sequence() -> OSBootSequence:
    sequence = OSBootSequence()
    sequence.add_step("load_governance", "Load governance from the registry mirror and canonical file")
    sequence.add_step("validate_lanes", "Confirm lane boundaries before routing work")
    sequence.add_step("prime_memory", "Prepare memory and registry caches")
    sequence.add_step("start_health_checks", "Prepare diagnostics loop and health surfaces")
    sequence.add_step("emit_heartbeat", "Record boot heartbeat after validation")
    return sequence
