from __future__ import annotations

from pathlib import Path

from scanner.providers.wsl import WSLScanner, windows_to_wsl_path


def test_wsl_scanner_path_translation_helper():
    translated = windows_to_wsl_path(r"D:\Archive")
    assert translated.translated == "/mnt/d/Archive"


def test_wsl_scanner_marks_source_tracking(tmp_path: Path):
    sample = tmp_path / "sample.txt"
    sample.write_text("sample\n", encoding="utf-8")
    manifest = WSLScanner().scan(str(tmp_path))
    assert manifest.source_type == "wsl"
