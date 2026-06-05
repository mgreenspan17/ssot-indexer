from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SSOTAdapterResult:
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]


def adapt_manifest(manifest: dict[str, Any]) -> SSOTAdapterResult:
    nodes = []
    edges = []
    for record in manifest.get("records", []):
        uuid7 = record["uuid7"]
        nodes.append({"id": uuid7, "type": "file", "metadata": record})
        if record.get("blake3"):
            edges.append({"from": uuid7, "to": record["blake3"], "type": "HAS_HASH"})
    return SSOTAdapterResult(nodes=nodes, edges=edges)
