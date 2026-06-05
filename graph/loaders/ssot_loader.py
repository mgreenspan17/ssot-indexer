from __future__ import annotations

from typing import Any


def load_file_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "uuid7": record.get("uuid7", ""),
        "hash": record.get("blake3", ""),
        "canonical_path": record.get("canonical_path", ""),
        "metadata": record,
        "relationships": [],
        "versions": record.get("versions", []),
        "shortcuts": record.get("shortcuts", []),
    }
