"""Governance enforcer for SSOT OS.

Assumptions:
- Enforcement receives already validated governance and a structured request.

Boundaries:
- No side effects on import.
- Enforcement decisions are advisory until Copilot authorizes execution.

Integration notes:
- Warp should consume the returned decisions as gate output, not as direct commands.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .lane_gate import gate_operation


@dataclass(frozen=True)
class EnforcementDecision:
    allowed: bool
    lane: str
    reason: str
    details: dict[str, Any]


def enforce_operation(operation: dict[str, Any], governance_text: str) -> EnforcementDecision:
    gate = gate_operation(operation, governance_text)
    reason = "operation allowed by lane gate" if gate.allowed else gate.reason
    return EnforcementDecision(allowed=gate.allowed, lane=gate.lane, reason=reason, details=gate.details)
