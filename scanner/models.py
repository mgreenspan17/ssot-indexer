from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class FileRecord:
    uuid7: str
    path: str
    source: str
    size: int
    mtime: float
    mode: int
    hash_algorithm: str
    blake3: str
    category: str
    mime_type: str
    shortcut_allowed: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ScanManifest:
    source: str
    generated_at: str
    records: list[FileRecord]

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "generated_at": self.generated_at,
            "records": [record.to_dict() for record in self.records],
        }