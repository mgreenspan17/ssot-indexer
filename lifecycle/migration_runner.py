from __future__ import annotations

from pathlib import Path

from indexer.postgres import PostgresConfig, PostgresRepository


def run_migrations(dsn: str) -> list[str]:
    repository = PostgresRepository(PostgresConfig(dsn))
    applied: list[str] = []
    for migration in sorted(Path("sql").glob("*.sql")):
        repository.apply_sql(migration)
        applied.append(migration.name)
    return applied
