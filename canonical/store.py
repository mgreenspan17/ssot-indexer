from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil

from hashing.blake3_utils import hash_file
from indexer.models import IngestionResult
from indexer.postgres import PostgresRepository
from scanner.models import FileRecord
from shortcuts.generator import create_shortcut


@dataclass(frozen=True)
class CanonicalResult:
    canonical_path: str
    verified: bool
    shortcut_path: str | None


@dataclass
class CanonicalStoreManager:
    storage_root: Path
    shortcut_root: Path
    repository: PostgresRepository | None = None

    def canonical_path_for(self, blake3_digest: str) -> Path:
        return self.storage_root / "blake3" / blake3_digest

    def materialize(self, record: FileRecord, ingestion: IngestionResult) -> CanonicalResult:
        source_path = Path(record.path)
        canonical_path = self.canonical_path_for(record.blake3)
        canonical_path.parent.mkdir(parents=True, exist_ok=True)

        if canonical_path.exists():
            verified = hash_file(canonical_path).digest == record.blake3
        else:
            shutil.copy2(source_path, canonical_path)
            verified = hash_file(canonical_path).digest == record.blake3

        if not verified:
            raise ValueError(f"canonical integrity check failed for {record.path}")

        shortcut_path: str | None = None
        if record.shortcut_allowed and record.category != "system":
            self.shortcut_root.mkdir(parents=True, exist_ok=True)
            shortcut_target = self.shortcut_root / record.uuid7
            create_shortcut(shortcut_target, canonical_path)
            shortcut_path = str(shortcut_target)

        if self.repository is not None:
            self.repository.record_canonical_store(record.uuid7, ingestion.version_id, record.blake3, str(canonical_path), verified)
            if shortcut_path is not None:
                self.repository.record_shortcut(record.uuid7, ingestion.version_id, shortcut_path, str(canonical_path), "symlink")

        return CanonicalResult(canonical_path=str(canonical_path), verified=verified, shortcut_path=shortcut_path)
