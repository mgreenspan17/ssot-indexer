from __future__ import annotations

from pathlib import Path

from scanner.providers.onedrive import OneDriveScanner


def test_onedrive_scanner_marks_placeholder_source(tmp_path: Path, monkeypatch):
    root = tmp_path / "OneDrive"
    root.mkdir()
    placeholder = root / "cloud.cloud"
    placeholder.write_text("placeholder\n", encoding="utf-8")
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    manifest = OneDriveScanner().scan()
    assert manifest.source_type == "onedrive"
    assert manifest.records[0].source_id == manifest.source_id
