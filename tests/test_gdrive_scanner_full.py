from __future__ import annotations

import json
from pathlib import Path

from scanner.providers.gdrive import GoogleDriveScanner


def test_gdrive_scanner_tracks_pseudo_files_and_source(tmp_path: Path):
    root = tmp_path / "Google Drive"
    root.mkdir()
    pseudo = root / "sheet.gsheet"
    pseudo.write_text(json.dumps({"sheet_id": "abc"}), encoding="utf-8")
    manifest = GoogleDriveScanner().scan(str(root))
    assert manifest.source_type == "gdrive"
    assert manifest.records[0].mime_type == "application/vnd.google-apps.spreadsheet"
