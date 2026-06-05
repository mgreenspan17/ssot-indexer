from __future__ import annotations

from pathlib import Path


def rollback_version(previous_version: str) -> str:
    Path("VERSION").write_text(f"{previous_version}\n", encoding="utf-8")
    return previous_version
