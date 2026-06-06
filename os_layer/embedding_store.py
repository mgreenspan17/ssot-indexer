"""Embedding store for SSOT OS.

Assumptions:
- Embeddings may be stored as vectors or serialized lists.

Boundaries:
- The store is intentionally backend-agnostic.

Integration notes:
- GPU node integration can later back this store with a vector database.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EmbeddingStore:
    vectors: dict[str, list[float]] = field(default_factory=dict)
    metadata: dict[str, dict[str, Any]] = field(default_factory=dict)

    def write(self, key: str, vector: list[float], *, meta: dict[str, Any] | None = None) -> None:
        self.vectors[key] = vector
        if meta is not None:
            self.metadata[key] = meta

    def read(self, key: str) -> list[float] | None:
        return self.vectors.get(key)
