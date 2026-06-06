from __future__ import annotations

import json
from pathlib import Path

from scanner.factory import scan_any_target, scan_provider
from scanner.providers.gdrive import GoogleDriveScanner
from scanner.providers.registry import list_provider_names
from scanner.providers.wsl import windows_to_wsl_path, wsl_to_windows_path
from scanner.service import manifest_to_json


def test_provider_registry_lists_expected_providers():
    providers = set(list_provider_names())
    assert {"windows", "wsl", "gdrive", "onedrive", "dropbox"}.issubset(providers)


def test_wsl_path_translation_round_trip():
    translated = windows_to_wsl_path(r"C:\Users\manni\docs")
    assert translated.translated == "/mnt/c/Users/manni/docs"
    round_trip = wsl_to_windows_path(translated.translated)
    assert round_trip.translated == r"C:\Users\manni\docs"


def test_windows_provider_scans_manifest(tmp_path: Path):
    sample = tmp_path / "sample.py"
    sample.write_text("print('ok')\n", encoding="utf-8")
    manifest = scan_provider("windows", str(tmp_path))
    assert manifest.source.startswith("windows://")
    assert len(manifest.records) == 1
    assert manifest.records[0].path.endswith("sample.py")


def test_gdrive_scanner_handles_pseudo_files(tmp_path: Path):
    root = tmp_path / "Google Drive"
    root.mkdir()
    pseudo = root / "notes.gdoc"
    pseudo.write_text(json.dumps({"doc_id": "123"}), encoding="utf-8")
    manifest = GoogleDriveScanner().scan(str(root))
    assert len(manifest.records) == 1
    assert manifest.records[0].mime_type == "application/vnd.google-apps.document"


def test_cloud_provider_scans_by_name(tmp_path: Path, monkeypatch):
    one = tmp_path / "OneDrive"
    one.mkdir()
    file_path = one / "cloud.txt"
    file_path.write_text("hello\n", encoding="utf-8")
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    manifest = scan_provider("onedrive")
    assert manifest.source.startswith("onedrive://")
    assert manifest.records[0].path.endswith("cloud.txt")


def test_factory_dispatches_by_path_pattern(monkeypatch):
    calls: list[tuple[str, str | None]] = []

    def fake_scan_provider(name: str, target: str | None = None):
        calls.append((name, target))
        class _Manifest:
            source = name
            generated_at = "now"
            records = []
        return _Manifest()

    monkeypatch.setattr("scanner.factory.scan_provider", fake_scan_provider)
    manifest = scan_any_target("/mnt/c/Users/manni/Documents")
    assert manifest.source == "wsl"
    assert calls == [("wsl", "/mnt/c/Users/manni/Documents")]


def test_manifest_serialization_from_provider(tmp_path: Path):
    sample = tmp_path / "sample.txt"
    sample.write_text("sample\n", encoding="utf-8")
    manifest = scan_provider("windows", str(tmp_path))
    payload = manifest_to_json(manifest)
    data = json.loads(payload)
    assert data["records"][0]["path"].endswith("sample.txt")
