"""Dashboard file data adapter.

Assumptions:
- File inventory will later come from crawl outputs or an index-backed file browser.

Boundaries:
- Read-only adapter only; no filesystem mutation.

Integration notes:
- The dashboard can call these functions now and later swap the internals for live search/index queries.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def list_files(path: str) -> list[dict[str, Any]]:
    root = Path(path)
    return [
        {
            "path": str(root / "placeholder.txt"),
            "kind": "file",
            "size": 0,
            "modified_at": datetime.now(timezone.utc).isoformat(),
        }
    ]


def get_file_metadata(path: str) -> dict[str, Any]:
    file_path = Path(path)
    return {
        "path": str(file_path),
        "exists": False,
        "size": 0,
        "hash": None,
        "mime_type": "application/octet-stream",
        "last_seen": datetime.now(timezone.utc).isoformat(),
    }


def search_files(query: str) -> list[dict[str, Any]]:
    return [
        {
            "path": "/srv/data/ssot-ingestion/placeholder.txt",
            "score": 0.0,
            "matched_query": query,
        }
    ]
