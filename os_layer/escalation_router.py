"""Escalation routing for SSOT OS.

Assumptions:
- Blockers are reported with task metadata and lane context.

Boundaries:
- This module computes escalation targets only.

Integration notes:
- Copilot should receive the escalation payload and decide whether to elevate to Operator.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EscalationTarget:
    target: str
    reason: str
    metadata: dict[str, Any]


def route_escalation(blocker: dict[str, Any]) -> EscalationTarget:
    lane = str(blocker.get("lane", "unknown"))
    if lane == "warp":
        return EscalationTarget("copilot", "Warp requires coordination or authorization", blocker)
    if lane == "cody":
        return EscalationTarget("copilot", "Cody requires spec clarification or phase approval", blocker)
    if lane == "experimental":
        return EscalationTarget("copilot", "Experimental compute task exceeded its bounds", blocker)
    return EscalationTarget("operator", "Governance, security, or architecture escalation", blocker)
