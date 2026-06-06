from __future__ import annotations

from pathlib import Path

from scanner.factory import scan_provider


def test_source_tracking_fields_are_present_for_windows_scan(tmp_path: Path):
    sample = tmp_path / "sample.txt"
    sample.write_text("sample\n", encoding="utf-8")
    manifest = scan_provider("windows", str(tmp_path))
    assert manifest.source_id
    assert manifest.source_type == "windows"
    assert manifest.source_label
    assert manifest.source_device_uuid
    record = manifest.records[0]
    assert record.source_id == manifest.source_id
    assert record.source_type == manifest.source_type
    assert record.source_label == manifest.source_label
    assert record.source_device_uuid == manifest.source_device_uuid


def test_source_tracking_fields_are_backward_compatible_in_dict(tmp_path: Path):
    sample = tmp_path / "sample.txt"
    sample.write_text("sample\n", encoding="utf-8")
    manifest = scan_provider("windows", str(tmp_path))
    payload = manifest.to_dict()
    assert payload["source_id"]
    assert payload["records"][0]["source_type"] == "windows"
