from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from canonical.store import CanonicalStoreManager
from indexer.ingest import ManifestIngestor
from indexer.postgres import PostgresConfig, PostgresRepository
from scanner.service import scan_target


@dataclass
class SSOTOrchestrator:
    dsn: str | None = None
    storage_root: Path = Path("/ssot")
    shortcut_root: Path = Path("/ssot/shortcuts")

    def repository(self) -> PostgresRepository:
        if not self.dsn:
            raise ValueError("dsn is required for Postgres operations")
        return PostgresRepository(PostgresConfig(self.dsn))

    def scan(self, target: str):
        return scan_target(target).manifest

    def ingest_and_canonicalize(self, target: str) -> list[dict[str, object]]:
        manifest = self.scan(target)
        repository = self.repository()
        ingestor = ManifestIngestor(repository)
        results = ingestor.ingest(manifest)
        canonical_store = CanonicalStoreManager(self.storage_root, self.shortcut_root, repository)
        output: list[dict[str, object]] = []
        for record, ingestion in zip(manifest.records, results, strict=True):
            canonical = canonical_store.materialize(record, ingestion)
            output.append(
                {
                    "file_id": ingestion.file_id,
                    "version_id": ingestion.version_id,
                    "canonical_path": canonical.canonical_path,
                    "shortcut_path": canonical.shortcut_path,
                    "verified": canonical.verified,
                }
            )
        return output
