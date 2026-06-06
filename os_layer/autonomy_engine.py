"""Autonomy scoring engine for SSOT OS.

Assumptions:
- Autonomy is bounded by lane, safety, and escalation rules.

Boundaries:
- Scores are advisory and never override governance.

Integration notes:
- Copilot can use these scores to determine which agent may proceed autonomously.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

AUTONOMY_RULES = {
    "warp": {"execution": 3, "design": 1},
    "cody": {"artifact_generation": 3, "execution": 0},
    "copilot": {"coordination": 3, "direct_execution": 0},
    "experimental": {"compute": 3, "infrastructure": 0},
}


@dataclass(frozen=True)
class AutonomyScore:
    agent: str
    lane: str
    score: int
    reason: str
    metadata: dict[str, Any]


def score_agent(agent: dict[str, Any]) -> AutonomyScore:
    lane = str(agent.get("lane", "experimental"))
    role = str(agent.get("role", "compute"))
    lane_rules = AUTONOMY_RULES.get(lane, AUTONOMY_RULES["experimental"])
    score = int(lane_rules.get(role, 0))
    return AutonomyScore(agent=str(agent.get("agent", "unknown")), lane=lane, score=score, reason="score derived from lane rules", metadata=agent)
