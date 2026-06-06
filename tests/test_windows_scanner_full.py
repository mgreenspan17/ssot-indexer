from __future__ import annotations

from pathlib import Path

from scanner.base import normalize_windows_path
from scanner.providers.windows import WindowsScanner


def test_windows_scanner_normalizes_long_paths():
    normalized = normalize_windows_path(r"C:\Users\manni\Documents")
    assert normalized.startswith("\\\\?\\")


def test_windows_scanner_marks_source_tracking(tmp_path: Path):
    sample = tmp_path / "sample.txt"
    sample.write_text("sample\n", encoding="utf-8")
    manifest = WindowsScanner().scan(str(tmp_path))
    assert manifest.source_type == "windows"
    assert manifest.records[0].source_type == "windows"
