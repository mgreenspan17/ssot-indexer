from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Literal


SourceType = Literal["local", "windows", "wsl", "gdrive", "onedrive", "dropbox", "external", "network", "provider"]


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
    sha256: str = ""
    source_id: str = ""
    source_type: SourceType = "local"
    source_label: str | None = None
    source_device_uuid: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ScanManifest:
    source: str
    generated_at: str
    records: list[FileRecord]
    source_id: str = ""
    source_type: SourceType = "local"
    source_label: str | None = None
    source_device_uuid: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "generated_at": self.generated_at,
            "records": [record.to_dict() for record in self.records],
            "source_id": self.source_id,
            "source_type": self.source_type,
            "source_label": self.source_label,
            "source_device_uuid": self.source_device_uuid,
        }