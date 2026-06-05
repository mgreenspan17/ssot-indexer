from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IngestionBatch:
    id: str
    source: str
    generated_at: str
    status: str


@dataclass(frozen=True)
class IngestionResult:
    file_id: str
    version_id: str
    hash_id: int
