"""Routing engine for SSOT OS.

Assumptions:
- Routing decisions are made from task metadata and governance boundaries.

Boundaries:
- This module selects lanes and escalations; it does not execute workloads.

Integration notes:
- Copilot should use this engine to dispatch work to Warp, Cody, or specialized agents.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

LANE_WARP = "warp"
LANE_CODY = "cody"
LANE_COPILOT = "copilot"
LANE_EXPERIMENTAL = "experimental"


@dataclass(frozen=True)
class RoutingDecision:
    lane: str
    reason: str
    confidence: float
    metadata: dict[str, Any]


def route_task(task: dict[str, Any], governance_text: str | None = None) -> RoutingDecision:
    kind = str(task.get("kind", "")).lower()
    if kind in {"deploy", "restart", "validate", "sync"}:
        return RoutingDecision(LANE_WARP, "operational execution task", 0.95, task)
    if kind in {"design", "patch", "document", "plan"}:
        return RoutingDecision(LANE_CODY, "artifact generation task", 0.92, task)
    if kind in {"route", "coordinate", "approve", "triage"}:
        return RoutingDecision(LANE_COPILOT, "coordination task", 0.93, task)
    return RoutingDecision(LANE_EXPERIMENTAL, "specialized compute or unclassified bounded task", 0.70, task)
