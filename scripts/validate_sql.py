from __future__ import annotations

from pathlib import Path


def main() -> int:
    migrations = sorted(Path("sql").glob("*.sql"))
    names = [migration.name for migration in migrations]
    if names != ["001_init.sql", "002_indexes.sql"]:
        raise SystemExit(f"unexpected migration order: {names}")
    for migration in migrations:
        text = migration.read_text(encoding="utf-8")
        if "create table" not in text and "create index" not in text:
            raise SystemExit(f"migration appears empty: {migration}")
    print("sql_valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
