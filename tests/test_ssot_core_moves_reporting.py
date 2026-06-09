from __future__ import annotations

from ssot_core.models import (
    FileInstance,
    FileVersion,
    MoveEvent,
    MoveEventType,
    ProviderSyncState,
    ProviderSyncStrategy,
)
from ssot_core.moves import detect_moves, log_move_events_for_audit, update_paths_for_moves
from ssot_core.reporting import (
    build_duplicate_report,
    build_provider_sync_status_dashboard,
    build_version_history_view,
    summarize_hashing_performance,
)


def _instance(source_id: str, provider: str, path: str, h: str, device: str | None = None) -> FileInstance:
    return FileInstance.create(
        source_id=source_id,
        provider=provider,
        path=path,
        blake3_hash=h,
        size=10,
        mime_type="text/plain",
        modified_at="2026-01-01T00:00:00+00:00",
        device_id=device,
    )


def test_detect_moves_and_copies():
    prev = [
        _instance("1", "server", "/a.txt", "h1", "d1"),
        _instance("2", "server", "/b.txt", "h2", "d1"),
    ]
    curr = [
        _instance("1", "server", "/archive/a.txt", "h1", "d1"),
        _instance("2", "server", "/b.txt", "h2", "d1"),
        _instance("3", "dropbox", "/shared/b.txt", "h2", "d2"),
    ]
    result = detect_moves(prev, curr)
    assert len(result.moves) == 1
    assert len(result.copies) == 1


def test_update_paths_for_moves_applies_move_events():
    inst = _instance("1", "server", "/a.txt", "h1", "d1")
    move = MoveEvent(
        event_id="evt1",
        canonical_id=None,
        instance_id=inst.instance_id,
        event_type=MoveEventType.move,
        blake3_hash="h1",
        from_provider="server",
        from_path="/a.txt",
        from_device_id="d1",
        to_provider="server",
        to_path="/archive/a.txt",
        to_device_id="d1",
    )
    updated = update_paths_for_moves([inst], [move])
    assert updated[0].path == "/archive/a.txt"


def test_log_move_events_for_audit_appends_records():
    event = MoveEvent(
        event_id="evt1",
        canonical_id=None,
        instance_id=None,
        event_type=MoveEventType.copy,
        blake3_hash="h1",
        from_provider="server",
        from_path="/a.txt",
        from_device_id=None,
        to_provider="gdrive",
        to_path="/a.txt",
        to_device_id=None,
    )
    log = log_move_events_for_audit([event], [])
    assert log[0]["event_type"] == "copy"


def test_reporting_helpers_generate_dashboard_outputs():
    perf = summarize_hashing_performance(total_bytes=1024 * 1024 * 10, total_files=50, elapsed_seconds=2.0)
    assert perf["files_per_second"] == 25.0

    versions = [
        FileVersion.create("canon1", "h1", 10, "server", "/a.txt"),
        FileVersion.create("canon1", "h2", 20, "server", "/a.txt"),
    ]
    history = build_version_history_view("canon1", versions)
    assert history["version_count"] == 2

    states = [
        ProviderSyncState("server", ProviderSyncStrategy.full, None, "2026-01-01T00:00:00+00:00", None),
        ProviderSyncState("gdrive", ProviderSyncStrategy.incremental, "cursor1", "2026-01-01T00:00:00+00:00", "429"),
    ]
    dashboard = build_provider_sync_status_dashboard(states)
    assert dashboard["provider_count"] == 2

    # Basic report smoke check
    assert build_duplicate_report([]) == "No duplicate groups detected."
