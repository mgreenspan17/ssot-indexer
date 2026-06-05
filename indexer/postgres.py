from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import psycopg2
from psycopg2.extras import Json

from indexer.models import IngestionBatch, IngestionResult
from scanner.models import FileRecord, ScanManifest
from uuid.generator import uuid7_str


@dataclass(frozen=True)
class PostgresConfig:
    dsn: str


@dataclass
class PostgresRepository:
    config: PostgresConfig

    @contextmanager
    def connection(self):
        conn = psycopg2.connect(self.config.dsn)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def apply_sql(self, sql_path: str | Path) -> None:
        statement = Path(sql_path).read_text(encoding="utf-8")
        with self.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(statement)

    def create_batch(self, manifest: ScanManifest) -> IngestionBatch:
        batch_id = uuid7_str()
        with self.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    insert into ingestion_batches (id, source, generated_at, status, manifest)
                    values (%s, %s, %s, %s, %s)
                    on conflict (id) do update set source = excluded.source
                    returning id
                    """,
                    (batch_id, manifest.source, manifest.generated_at, "pending", Json(manifest.to_dict())),
                )
        return IngestionBatch(id=batch_id, source=manifest.source, generated_at=manifest.generated_at, status="pending")

    def ingest_record(self, batch: IngestionBatch, record: FileRecord) -> IngestionResult:
        version_id = uuid7_str()
        with self.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    insert into files (id, path, source, canonical_hash, category, mime_type, shortcut_allowed, current_version_id)
                    values (%s, %s, %s, %s, %s, %s, %s, %s)
                    on conflict (id) do update set
                        path = excluded.path,
                        source = excluded.source,
                        canonical_hash = excluded.canonical_hash,
                        category = excluded.category,
                        mime_type = excluded.mime_type,
                        shortcut_allowed = excluded.shortcut_allowed,
                        current_version_id = excluded.current_version_id
                    """,
                    (record.uuid7, record.path, record.source, record.blake3, record.category, record.mime_type, record.shortcut_allowed, version_id),
                )
                cursor.execute(
                    """
                    insert into hashes (algorithm, digest, size)
                    values (%s, %s, %s)
                    on conflict (algorithm, digest) do update set size = excluded.size
                    returning id
                    """,
                    (record.hash_algorithm, record.blake3, record.size),
                )
                hash_id = cursor.fetchone()[0]
                cursor.execute(
                    "select coalesce(max(version_number), 0) + 1 from versions where file_id = %s",
                    (record.uuid7,),
                )
                version_number = cursor.fetchone()[0]
                cursor.execute(
                    """
                    insert into versions (
                        id, file_id, ingestion_batch_id, version_number, hash_id, size, mtime, mode
                    ) values (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (version_id, record.uuid7, batch.id, version_number, hash_id, record.size, record.mtime, record.mode),
                )
                cursor.execute(
                    """
                    insert into locations (file_id, version_id, path, source, is_canonical)
                    values (%s, %s, %s, %s, %s)
                    """,
                    (record.uuid7, version_id, record.path, record.source, False),
                )
                cursor.execute(
                    """
                    insert into metadata (version_id, data)
                    values (%s, %s)
                    """,
                    (version_id, Json({"size": record.size, "mtime": record.mtime, "mode": record.mode})),
                )
                cursor.execute(
                    """
                    insert into classifications (version_id, category, mime_type, shortcut_allowed)
                    values (%s, %s, %s, %s)
                    """,
                    (version_id, record.category, record.mime_type, record.shortcut_allowed),
                )
                cursor.execute("update files set current_version_id = %s where id = %s", (version_id, record.uuid7))
        return IngestionResult(file_id=record.uuid7, version_id=version_id, hash_id=int(hash_id))

    def mark_batch_complete(self, batch_id: str) -> None:
        with self.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("update ingestion_batches set status = %s where id = %s", ("complete", batch_id))

    def record_canonical_store(self, file_id: str, version_id: str, hash_digest: str, canonical_path: str, verified: bool) -> None:
        with self.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    insert into canonical_store (file_id, version_id, hash, canonical_path, verified)
                    values (%s, %s, %s, %s, %s)
                    on conflict (canonical_path) do update set verified = excluded.verified
                    """,
                    (file_id, version_id, hash_digest, canonical_path, verified),
                )

    def record_shortcut(self, file_id: str, version_id: str, shortcut_path: str, target_path: str, shortcut_kind: str) -> None:
        with self.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    insert into shortcuts (file_id, version_id, shortcut_path, target_path, shortcut_kind)
                    values (%s, %s, %s, %s, %s)
                    on conflict (shortcut_path) do update set target_path = excluded.target_path
                    """,
                    (file_id, version_id, shortcut_path, target_path, shortcut_kind),
                )
