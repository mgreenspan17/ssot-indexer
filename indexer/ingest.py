from __future__ import annotations

from dataclasses import dataclass

from indexer.models import IngestionResult
from indexer.postgres import PostgresRepository
from scanner.models import ScanManifest


@dataclass
class ManifestIngestor:
    repository: PostgresRepository

    def ingest(self, manifest: ScanManifest) -> list[IngestionResult]:
        batch = self.repository.create_batch(manifest)
        results = [self.repository.ingest_record(batch, record) for record in manifest.records]
        self.repository.mark_batch_complete(batch.id)
        return results
