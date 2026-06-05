from pathlib import Path

from scanner.local import scan_local_directory


def test_scan_local_directory(tmp_path: Path):
    sample = tmp_path / "sample.txt"
    sample.write_text("sample\n", encoding="utf-8")
    result = scan_local_directory(tmp_path)
    assert len(result.manifest.records) == 1
    assert result.manifest.records[0].path.endswith("sample.txt")
