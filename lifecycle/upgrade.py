from __future__ import annotations

from pathlib import Path

from scripts.bump_version import bump


def upgrade_version(part: str = "patch") -> str:
    current = Path("VERSION").read_text(encoding="utf-8").strip()
    new_version = bump(current, part)
    Path("VERSION").write_text(f"{new_version}\n", encoding="utf-8")
    return new_version
