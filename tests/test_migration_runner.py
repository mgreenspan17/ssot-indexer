from __future__ import annotations

from pathlib import Path
import sys
from types import ModuleType

from lifecycle.migration_runner import run_migrations


class _FakeRepository:
    def __init__(self) -> None:
        self.applied: list[str] = []

    def apply_sql(self, sql_path: Path) -> None:
        self.applied.append(Path(sql_path).name)


def test_run_migrations_applies_sorted_sql_files(monkeypatch):
    fake_repo = _FakeRepository()

    class _FakePostgresRepository:
        def __init__(self, _config):
            pass

        def apply_sql(self, sql_path):
            fake_repo.apply_sql(sql_path)

    class _FakePostgresConfig:
        def __init__(self, dsn):
            self.dsn = dsn

    sql_files = [Path("sql/010_last.sql"), Path("sql/001_init.sql"), Path("sql/002_indexes.sql")]

    fake_postgres = ModuleType("indexer.postgres")
    fake_postgres.PostgresRepository = _FakePostgresRepository  # type: ignore[attr-defined]
    fake_postgres.PostgresConfig = _FakePostgresConfig  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "indexer.postgres", fake_postgres)
    monkeypatch.setattr(Path, "glob", lambda self, pattern: sql_files)

    applied = run_migrations("postgresql://test")

    assert applied == ["001_init.sql", "002_indexes.sql", "010_last.sql"]
    assert fake_repo.applied == ["001_init.sql", "002_indexes.sql", "010_last.sql"]
