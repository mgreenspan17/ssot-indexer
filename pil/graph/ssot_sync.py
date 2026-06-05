from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pil.ingestion.ssot_adapter import adapt_manifest
from pil.graph.ssot_embeddings import embed_text


@dataclass(frozen=True)
class SyncResult:
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    embeddings: list[dict[str, Any]]


def sync_manifest(manifest: dict[str, Any]) -> SyncResult:
    adapted = adapt_manifest(manifest)
    embeddings = []
    for record in manifest.get("records", []):
        embeddings.append(embed_text(record.get("path", "")).__dict__)
    return SyncResult(nodes=adapted.nodes, edges=adapted.edges, embeddings=embeddings)
