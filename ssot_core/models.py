from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from uuid import uuid7_str


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class VersionChangeType(str, Enum):
    unchanged = "unchanged"
    same_version_new_location = "same_version_new_location"
    new_version_same_path = "new_version_same_path"
    new_canonical_object = "new_canonical_object"


class ProviderSyncStrategy(str, Enum):
    full = "full"
    incremental = "incremental"


class SyncEventType(str, Enum):
    new = "new"
    moved = "moved"
    renamed = "renamed"
    deleted = "deleted"
    modified = "modified"


class MoveEventType(str, Enum):
    move = "move"
    copy = "copy"


class DesktopCamState(str, Enum):
    stopped = "stopped"
    running = "running"


@dataclass(frozen=True)
class CanonicalFile:
    canonical_id: str
    blake3_hash: str
    size: int
    mime_type: str
    created_at: str = field(default_factory=utc_now_iso)
    latest_version_id: str | None = None

    @classmethod
    def create(cls, blake3_hash: str, size: int, mime_type: str) -> "CanonicalFile":
        return cls(
            canonical_id=uuid7_str(),
            blake3_hash=blake3_hash,
            size=size,
            mime_type=mime_type,
        )


@dataclass(frozen=True)
class FileVersion:
    version_id: str
    canonical_id: str
    parent_version_id: str | None
    blake3_hash: str
    size: int
    provider: str
    path: str
    created_at: str = field(default_factory=utc_now_iso)

    @classmethod
    def create(
        cls,
        canonical_id: str,
        blake3_hash: str,
        size: int,
        provider: str,
        path: str,
        parent_version_id: str | None = None,
    ) -> "FileVersion":
        return cls(
            version_id=uuid7_str(),
            canonical_id=canonical_id,
            parent_version_id=parent_version_id,
            blake3_hash=blake3_hash,
            size=size,
            provider=provider,
            path=path,
        )


@dataclass(frozen=True)
class FileInstance:
    instance_id: str
    canonical_id: str | None
    version_id: str | None
    source_id: str
    provider: str
    path: str
    blake3_hash: str
    size: int
    mime_type: str
    modified_at: str
    discovered_at: str = field(default_factory=utc_now_iso)
    deleted_at: str | None = None
    device_id: str | None = None

    @classmethod
    def create(
        cls,
        source_id: str,
        provider: str,
        path: str,
        blake3_hash: str,
        size: int,
        mime_type: str,
        modified_at: str,
        canonical_id: str | None = None,
        version_id: str | None = None,
        device_id: str | None = None,
    ) -> "FileInstance":
        return cls(
            instance_id=uuid7_str(),
            canonical_id=canonical_id,
            version_id=version_id,
            source_id=source_id,
            provider=provider,
            path=path,
            blake3_hash=blake3_hash,
            size=size,
            mime_type=mime_type,
            modified_at=modified_at,
            device_id=device_id,
        )

    def with_path(self, path: str) -> "FileInstance":
        return replace(self, path=path)


@dataclass(frozen=True)
class DuplicateGroup:
    duplicate_group_id: str
    canonical_id: str | None
    blake3_hash: str
    size: int
    mime_type: str
    instance_ids: tuple[str, ...]
    providers: tuple[str, ...]
    paths: tuple[str, ...]

    @classmethod
    def from_instances(
        cls,
        blake3_hash: str,
        size: int,
        mime_type: str,
        instances: list[FileInstance],
        canonical_id: str | None = None,
    ) -> "DuplicateGroup":
        return cls(
            duplicate_group_id=uuid7_str(),
            canonical_id=canonical_id,
            blake3_hash=blake3_hash,
            size=size,
            mime_type=mime_type,
            instance_ids=tuple(i.instance_id for i in instances),
            providers=tuple(i.provider for i in instances),
            paths=tuple(i.path for i in instances),
        )


@dataclass(frozen=True)
class ProviderSyncState:
    provider_id: str
    strategy: ProviderSyncStrategy
    cursor: str | None
    last_sync_at: str | None
    last_error: str | None
    retries: int = 0


@dataclass(frozen=True)
class ProviderDeltaEvent:
    provider_id: str
    event_type: SyncEventType
    source_id: str
    path: str
    blake3_hash: str | None
    size: int | None
    mime_type: str | None
    modified_at: str | None
    previous_path: str | None = None
    device_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MoveEvent:
    event_id: str
    canonical_id: str | None
    instance_id: str | None
    event_type: MoveEventType
    blake3_hash: str
    from_provider: str
    from_path: str
    from_device_id: str | None
    to_provider: str
    to_path: str
    to_device_id: str | None
    detected_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class MoveDetectionResult:
    moves: tuple[MoveEvent, ...]
    copies: tuple[MoveEvent, ...]


@dataclass(frozen=True)
class VersionClassification:
    change_type: VersionChangeType
    reason: str
    canonical_id: str | None


@dataclass(frozen=True)
class DeltaApplyResult:
    upserts: tuple[FileInstance, ...]
    deletions: tuple[str, ...]
    moves: tuple[ProviderDeltaEvent, ...]


@dataclass(frozen=True)
class ProviderSyncResult:
    provider_id: str
    strategy_used: ProviderSyncStrategy
    event_count: int
    new_cursor: str | None
    duration_seconds: float


@dataclass(frozen=True)
class ReconciliationResult:
    provider_id: str
    missing_in_provider: tuple[str, ...]
    missing_in_ssot: tuple[str, ...]
    hash_mismatches: tuple[str, ...]


@dataclass(frozen=True)
class SemanticFingerprint:
    file_id: str
    canonical_file_id: str
    version_id: str | None
    blake3_hash: str
    size: int
    mime_type: str
    a_hash: str
    d_hash: str
    p_hash: str
    embedding: tuple[float, ...]
    created_at: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class SemanticCluster:
    cluster_id: str
    canonical_file_ids: tuple[str, ...]
    similarity_scores: dict[str, float]
    representative_embedding: tuple[float, ...]
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)

    @classmethod
    def create(
        cls,
        canonical_file_ids: list[str],
        similarity_scores: dict[str, float],
        representative_embedding: tuple[float, ...],
    ) -> "SemanticCluster":
        now = utc_now_iso()
        return cls(
            cluster_id=uuid7_str(),
            canonical_file_ids=tuple(canonical_file_ids),
            similarity_scores=similarity_scores,
            representative_embedding=representative_embedding,
            created_at=now,
            updated_at=now,
        )


@dataclass(frozen=True)
class DesktopCamFrame:
    frame_id: str
    timestamp_uuid7: str
    captured_at: str
    blake3_hash: str
    bytes_size: int
    canonical_file_id: str
    version_id: str
    provider: str = "desktopcam"
    mime_type: str = "image/png"

    @classmethod
    def create(
        cls,
        timestamp_uuid7: str,
        blake3_hash: str,
        bytes_size: int,
        canonical_file_id: str,
        version_id: str,
        mime_type: str = "image/png",
    ) -> "DesktopCamFrame":
        return cls(
            frame_id=uuid7_str(),
            timestamp_uuid7=timestamp_uuid7,
            captured_at=utc_now_iso(),
            blake3_hash=blake3_hash,
            bytes_size=bytes_size,
            canonical_file_id=canonical_file_id,
            version_id=version_id,
            mime_type=mime_type,
        )


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    timestamp_uuid7: str
    blake3_hash: str
    frame_id: str
    previous_event_hash: str | None
    event_hash: str
    created_at: str = field(default_factory=utc_now_iso)

    @classmethod
    def create(
        cls,
        timestamp_uuid7: str,
        blake3_hash: str,
        frame_id: str,
        previous_event_hash: str | None,
        event_hash: str,
    ) -> "AuditEvent":
        return cls(
            event_id=uuid7_str(),
            timestamp_uuid7=timestamp_uuid7,
            blake3_hash=blake3_hash,
            frame_id=frame_id,
            previous_event_hash=previous_event_hash,
            event_hash=event_hash,
        )


@dataclass(frozen=True)
class DesktopCamSession:
    session_id: str
    device_id: str
    fps: int
    state: DesktopCamState
    started_at: str | None
    stopped_at: str | None
    frame_count: int
    last_error: str | None = None


@dataclass(frozen=True)
class ForensicBundle:
    session: DesktopCamSession
    frames: tuple[DesktopCamFrame, ...]
    events: tuple[AuditEvent, ...]
    chain_valid: bool
