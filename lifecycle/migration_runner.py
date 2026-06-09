from __future__ import annotations

from pathlib import Path


def run_migrations(dsn: str) -> list[str]:
    from indexer.postgres import PostgresConfig, PostgresRepository

    repository = PostgresRepository(PostgresConfig(dsn))
    applied: list[str] = []
    for migration in sorted(Path("sql").glob("*.sql")):
        repository.apply_sql(migration)
        applied.append(migration.name)
    return applied
