from __future__ import annotations

import json
from pathlib import Path

from cli.ssotctl import main


def test_ssotctl_scan_windows_stdout(tmp_path: Path, capsys):
    sample = tmp_path / "sample.txt"
    sample.write_text("sample\n", encoding="utf-8")
    exit_code = main(["scan", "windows", str(tmp_path)])
    assert exit_code == 0
    output = capsys.readouterr().out
    payload = json.loads(output)
    assert payload["source"].startswith("windows://")


def test_ssotctl_scan_provider_file_output(tmp_path: Path, monkeypatch):
    root = tmp_path / "Dropbox"
    root.mkdir()
    sample = root / "dropbox.txt"
    sample.write_text("dropbox\n", encoding="utf-8")
    output_path = tmp_path / "manifest.json"
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    exit_code = main(["scan", "provider", "dropbox", "--json", str(output_path)])
    assert exit_code == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["source"].startswith("dropbox://")
