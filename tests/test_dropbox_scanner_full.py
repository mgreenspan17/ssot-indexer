from __future__ import annotations

from pathlib import Path

from scanner.providers.dropbox import DropboxScanner


def test_dropbox_scanner_marks_smart_sync_source(tmp_path: Path, monkeypatch):
    root = tmp_path / "Dropbox"
    root.mkdir()
    placeholder = root / "remote.dropbox"
    placeholder.write_text("dropbox\n", encoding="utf-8")
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    manifest = DropboxScanner().scan()
    assert manifest.source_type == "dropbox"
    assert manifest.records[0].source_device_uuid == manifest.source_device_uuid
