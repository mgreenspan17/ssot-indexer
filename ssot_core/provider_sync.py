from __future__ import annotations

import time
from collections.abc import Callable

from ssot_core.models import (
    DeltaApplyResult,
    FileInstance,
    ProviderDeltaEvent,
    ProviderSyncResult,
    ProviderSyncState,
    ProviderSyncStrategy,
    ReconciliationResult,
    SyncEventType,
)


def sync_provider(
    provider_id: str,
    state: ProviderSyncState,
    fetch_full_snapshot: Callable[[str], tuple[list[ProviderDeltaEvent], str | None]],
    fetch_incremental: Callable[[str, str], tuple[list[ProviderDeltaEvent], str | None]],
) -> ProviderSyncResult:
    """Sync a provider using full or incremental strategy depending on state cursor."""
    start = time.perf_counter()

    if state.cursor:
        strategy = ProviderSyncStrategy.incremental
        events, new_cursor = fetch_incremental(provider_id, state.cursor)
    else:
        strategy = ProviderSyncStrategy.full
        events, new_cursor = fetch_full_snapshot(provider_id)

    duration = time.perf_counter() - start
    return ProviderSyncResult(
        provider_id=provider_id,
        strategy_used=strategy,
        event_count=len(events),
        new_cursor=new_cursor,
        duration_seconds=round(duration, 6),
    )


def apply_provider_delta(
    provider_id: str,
    delta_events: list[ProviderDeltaEvent],
    known_instances: list[FileInstance],
) -> DeltaApplyResult:
    """Apply provider delta events to known instances using in-memory reconciliation rules."""
    by_source = {i.source_id: i for i in known_instances if i.provider == provider_id}
    upserts: list[FileInstance] = []
    deletions: list[str] = []
    moves: list[ProviderDeltaEvent] = []

    for event in delta_events:
        if event.provider_id != provider_id:
            continue

        current = by_source.get(event.source_id)

        if event.event_type == SyncEventType.deleted:
            if current is not None:
                deletions.append(current.instance_id)
            continue

        if event.event_type in {SyncEventType.moved, SyncEventType.renamed}:
            moves.append(event)

        if event.event_type in {
            SyncEventType.new,
            SyncEventType.modified,
            SyncEventType.moved,
            SyncEventType.renamed,
        }:
            if event.blake3_hash is None or event.size is None or event.mime_type is None:
                # Skip incomplete payloads for non-delete events.
                continue

            if current is None:
                upserts.append(
                    FileInstance.create(
                        source_id=event.source_id,
                        provider=provider_id,
                        path=event.path,
                        blake3_hash=event.blake3_hash,
                        size=event.size,
                        mime_type=event.mime_type,
                        modified_at=event.modified_at or "",
                        device_id=event.device_id,
                    )
                )
            else:
                upserts.append(
                    FileInstance(
                        instance_id=current.instance_id,
                        canonical_id=current.canonical_id,
                        version_id=current.version_id,
                        source_id=current.source_id,
                        provider=current.provider,
                        path=event.path,
                        blake3_hash=event.blake3_hash,
                        size=event.size,
                        mime_type=event.mime_type,
                        modified_at=event.modified_at or current.modified_at,
                        discovered_at=current.discovered_at,
                        deleted_at=None,
                        device_id=event.device_id or current.device_id,
                    )
                )

    return DeltaApplyResult(
        upserts=tuple(upserts),
        deletions=tuple(deletions),
        moves=tuple(moves),
    )


def reconcile_provider_state_with_ssot(
    provider_id: str,
    provider_snapshot: list[FileInstance],
    ssot_instances: list[FileInstance],
) -> ReconciliationResult:
    """Compare provider snapshot against SSOT instances and detect drift."""
    provider_by_source = {i.source_id: i for i in provider_snapshot}
    ssot_by_source = {i.source_id: i for i in ssot_instances if i.provider == provider_id}

    missing_in_provider = sorted(source_id for source_id in ssot_by_source if source_id not in provider_by_source)
    missing_in_ssot = sorted(source_id for source_id in provider_by_source if source_id not in ssot_by_source)

    hash_mismatches: list[str] = []
    for source_id in sorted(set(provider_by_source).intersection(ssot_by_source)):
        provider_instance = provider_by_source[source_id]
        ssot_instance = ssot_by_source[source_id]
        if provider_instance.blake3_hash != ssot_instance.blake3_hash:
            hash_mismatches.append(source_id)

    return ReconciliationResult(
        provider_id=provider_id,
        missing_in_provider=tuple(missing_in_provider),
        missing_in_ssot=tuple(missing_in_ssot),
        hash_mismatches=tuple(hash_mismatches),
    )
