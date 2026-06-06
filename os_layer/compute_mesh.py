"""Compute mesh primitives for SSOT OS.

Assumptions:
- Node and job metadata are provided by a scheduler or controller.

Boundaries:
- No remote execution is performed here.
- This module only models worker capacity and job assignment.

Integration notes:
- Warp can later replace placeholder registries with live agent discovery.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class WorkerNode:
    worker_id: str
    lane: str
    capabilities: tuple[str, ...] = ()
    score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MeshJob:
    job_id: str
    kind: str
    lane_hint: str
    payload: dict[str, Any]


@dataclass
class ComputeMesh:
    workers: dict[str, WorkerNode] = field(default_factory=dict)

    def register_worker(self, worker: WorkerNode) -> None:
        self.workers[worker.worker_id] = worker

    def choose_worker(self, job: MeshJob) -> WorkerNode | None:
        candidates = [worker for worker in self.workers.values() if worker.lane == job.lane_hint]
        if not candidates:
            return None
        return sorted(candidates, key=lambda worker: worker.score, reverse=True)[0]
