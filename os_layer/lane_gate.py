"""Lane gate for SSOT OS.

Assumptions:
- Task metadata is structured and trustworthy enough for policy gating.

Boundaries:
- Lane gates do not dispatch work; they only approve or deny.

Integration notes:
- Combine with routing_engine and escalation_router for Copilot-led coordination.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GateDecision:
    allowed: bool
    lane: str
    reason: str
    details: dict[str, Any]


def gate_operation(operation: dict[str, Any], governance_text: str | None = None) -> GateDecision:
    lane = str(operation.get("lane", "unknown"))
    destructive = bool(operation.get("destructive", False))
    if destructive and lane != "warp":
        return GateDecision(False, lane, "destructive action requires Warp lane and Copilot authorization", operation)
    if operation.get("requires_authorization", True) and not operation.get("authorized", False):
        return GateDecision(False, lane, "operation is not authorized", operation)
    return GateDecision(True, lane, "operation passed lane gate", operation)
