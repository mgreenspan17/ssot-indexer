from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class FileNode:
    uuid7: str
    path: str
    canonical_path: str
    hash: str
    category: str
    mime_type: str


@dataclass(frozen=True)
class ConceptNode:
    id: str
    label: str


def to_node_payload(node: object) -> dict[str, Any]:
    return asdict(node)  # type: ignore[arg-type]
