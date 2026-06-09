from __future__ import annotations

from ssot_core.models import (
    FileInstance,
    ProviderDeltaEvent,
    ProviderSyncState,
    ProviderSyncStrategy,
    SyncEventType,
)
from ssot_core.provider_sync import (
    apply_provider_delta,
    reconcile_provider_state_with_ssot,
    sync_provider,
)


def test_sync_provider_uses_full_without_cursor():
    state = ProviderSyncState(
        provider_id="gdrive",
        strategy=ProviderSyncStrategy.full,
        cursor=None,
        last_sync_at=None,
        last_error=None,
    )

    def fetch_full(provider_id: str):
        return ([], "cursor-1")

    def fetch_incremental(provider_id: str, cursor: str):
        raise AssertionError("incremental should not run")

    result = sync_provider("gdrive", state, fetch_full, fetch_incremental)
    assert result.strategy_used == ProviderSyncStrategy.full
    assert result.new_cursor == "cursor-1"


def test_apply_provider_delta_handles_new_modify_delete():
    known = [
        FileInstance.create(
            source_id="g1",
            provider="gdrive",
            path="/a.txt",
            blake3_hash="h1",
            size=10,
            mime_type="text/plain",
            modified_at="2026-01-01T00:00:00+00:00",
        )
    ]
    events = [
        ProviderDeltaEvent(
            provider_id="gdrive",
            event_type=SyncEventType.modified,
            source_id="g1",
            path="/a.txt",
            blake3_hash="h2",
            size=20,
            mime_type="text/plain",
            modified_at="2026-01-02T00:00:00+00:00",
        ),
        ProviderDeltaEvent(
            provider_id="gdrive",
            event_type=SyncEventType.new,
            source_id="g2",
            path="/b.txt",
            blake3_hash="h3",
            size=30,
            mime_type="text/plain",
            modified_at="2026-01-03T00:00:00+00:00",
        ),
        ProviderDeltaEvent(
            provider_id="gdrive",
            event_type=SyncEventType.deleted,
            source_id="g1",
            path="/a.txt",
            blake3_hash=None,
            size=None,
            mime_type=None,
            modified_at=None,
        ),
    ]
    applied = apply_provider_delta("gdrive", events, known)
    assert len(applied.upserts) == 2
    assert len(applied.deletions) == 1


def test_reconcile_provider_state_with_ssot_detects_drift():
    provider_snapshot = [
        FileInstance.create(
            source_id="g1",
            provider="gdrive",
            path="/a.txt",
            blake3_hash="h1",
            size=10,
            mime_type="text/plain",
            modified_at="2026-01-01T00:00:00+00:00",
        ),
        FileInstance.create(
            source_id="g2",
            provider="gdrive",
            path="/b.txt",
            blake3_hash="h2",
            size=20,
            mime_type="text/plain",
            modified_at="2026-01-01T00:00:00+00:00",
        ),
    ]
    ssot_instances = [
        FileInstance.create(
            source_id="g1",
            provider="gdrive",
            path="/a.txt",
            blake3_hash="h9",
            size=10,
            mime_type="text/plain",
            modified_at="2026-01-01T00:00:00+00:00",
        ),
        FileInstance.create(
            source_id="g3",
            provider="gdrive",
            path="/c.txt",
            blake3_hash="h3",
            size=30,
            mime_type="text/plain",
            modified_at="2026-01-01T00:00:00+00:00",
        ),
    ]
    reconciliation = reconcile_provider_state_with_ssot("gdrive", provider_snapshot, ssot_instances)
    assert reconciliation.hash_mismatches == ("g1",)
    assert reconciliation.missing_in_ssot == ("g2",)
    assert reconciliation.missing_in_provider == ("g3",)
