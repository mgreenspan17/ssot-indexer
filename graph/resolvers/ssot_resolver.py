from __future__ import annotations

from typing import Any


def resolve_file(uuid7: str | None = None, hash: str | None = None, canonical_path: str | None = None) -> dict[str, Any]:
    identifier = uuid7 or hash or canonical_path
    if identifier is None:
        raise ValueError("one of uuid7, hash, or canonical_path is required")
    return {
        "uuid7": uuid7 or identifier,
        "hash": hash or "",
        "canonical_path": canonical_path or "",
        "metadata": {},
        "relationships": [],
        "versions": [],
        "shortcuts": [],
    }
