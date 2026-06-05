from __future__ import annotations

from pathlib import Path


def check_consistency() -> dict[str, bool]:
    return {
        "version_file": Path("VERSION").exists(),
        "migrations_present": all(Path("sql").joinpath(name).exists() for name in ("001_init.sql", "002_indexes.sql")),
    }
