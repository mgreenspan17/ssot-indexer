from __future__ import annotations

from pathlib import Path

from autoscan.linux import detect_mount_events as detect_linux_mount_events
from autoscan.windows import detect_volume_events
from autoscan.wsl import detect_mount_events as detect_wsl_mount_events
from scanner.autoscan import AutoScanEvent, AutoScanManager


def test_autoscan_enable_disable_status(tmp_path: Path):
    state_path = tmp_path / "autoscan-state.json"
    manager = AutoScanManager(state_path=state_path)
    enabled = manager.enable()
    assert enabled["enabled"] is True
    assert manager.status()["enabled"] is True
    disabled = manager.disable()
    assert disabled["enabled"] is False


def test_autoscan_handle_event_submits_manifest(tmp_path: Path):
    sample = tmp_path / "sample.txt"
    sample.write_text("sample\n", encoding="utf-8")
    manager = AutoScanManager(state_path=tmp_path / "state.json")
    submitted_payloads: list[dict[str, object]] = []

    def submit_manifest(payload: dict[str, object]) -> bool:
        submitted_payloads.append(payload)
        return True

    result = manager.handle_event(AutoScanEvent(platform="windows", mount_path=str(tmp_path)), submit_manifest=submit_manifest)
    assert result.submitted is True
    assert result.record_count == 1
    assert submitted_payloads


def test_linux_autoscan_detects_new_mounts():
    events = detect_linux_mount_events({"/mnt/a"}, {"/mnt/a", "/media/Google Drive"})
    assert len(events) == 1
    assert events[0].provider_hint == "gdrive"


def test_windows_autoscan_detects_new_volumes():
    events = detect_volume_events({"C:\\"}, {"C:\\", "E:\\"})
    assert len(events) == 1
    assert events[0].mount_path == "E:\\"


def test_wsl_autoscan_detects_new_mnt_roots():
    events = detect_wsl_mount_events({"/mnt/c"}, {"/mnt/c", "/mnt/d"})
    assert len(events) == 1
    assert events[0].mount_path == "/mnt/d"
