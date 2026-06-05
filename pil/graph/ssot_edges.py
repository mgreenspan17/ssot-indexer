from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class RelationshipEdge:
    source: str
    target: str
    edge_type: str


@dataclass(frozen=True)
class TaskEdge:
    source: str
    target: str
    edge_type: str = "RELATED_TO_TASK"


def to_edge_payload(edge: object) -> dict[str, Any]:
    return asdict(edge)  # type: ignore[arg-type]
