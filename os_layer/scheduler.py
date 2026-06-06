"""Scheduler primitives for the SSOT compute mesh.

Assumptions:
- Scheduling inputs are already validated and lane-tagged.

Boundaries:
- This module computes scheduling suggestions only.

Integration notes:
- Pair with compute_mesh and retry_policy.md when Warp wires live execution.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SchedulePlan:
    job_id: str
    worker_id: str | None
    priority: int
    reason: str
    metadata: dict[str, Any]


def schedule_job(job: dict[str, Any], worker_id: str | None = None) -> SchedulePlan:
    priority = int(job.get("priority", 5))
    lane = str(job.get("lane", "experimental"))
    reason = f"scheduled for {lane} lane"
    return SchedulePlan(job_id=str(job.get("job_id", "unknown")), worker_id=worker_id, priority=priority, reason=reason, metadata=job)
