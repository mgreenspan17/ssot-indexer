from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class FileUpdatedEvent:
    uuid7: str
    path: str
    timestamp: str = _timestamp()


@dataclass(frozen=True)
class NewHashEvent:
    digest: str
    algorithm: str = "blake3"
    timestamp: str = _timestamp()


@dataclass(frozen=True)
class NewVersionEvent:
    file_id: str
    version_id: str
    timestamp: str = _timestamp()


def to_event_payload(event: object) -> dict[str, Any]:
    return asdict(event)  # type: ignore[arg-type]
