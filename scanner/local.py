from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from stat import S_ISREG

from classify.classifier import classify_file
from hashing.blake3_utils import hash_file
from scanner.base import build_source_descriptor
from scanner.models import FileRecord, ScanManifest
from uuid.generator import uuid7_str


@dataclass(frozen=True)
class LocalScanResult:
    manifest: ScanManifest


def scan_local_directory(root: str | Path) -> LocalScanResult:
    root_path = Path(root)
    records: list[FileRecord] = []
    descriptor = build_source_descriptor("local", root_path, source_label=root_path.name or str(root_path))
    for path in root_path.rglob("*"):
        try:
            stat_result = path.stat()
        except OSError:
            continue
        if not S_ISREG(stat_result.st_mode):
            continue
        classification = classify_file(path)
        hash_result = hash_file(path)
        records.append(
            FileRecord(
                uuid7=uuid7_str(),
                path=str(path.resolve()),
                source=str(root_path.resolve()),
                size=stat_result.st_size,
                mtime=stat_result.st_mtime,
                mode=stat_result.st_mode,
                hash_algorithm=hash_result.algorithm,
                blake3=hash_result.digest,
                category=classification.category,
                mime_type=classification.mime_type,
                shortcut_allowed=classification.shortcut_allowed,
                source_id=descriptor.source_id,
                source_type=descriptor.source_type,
                source_label=descriptor.source_label,
                source_device_uuid=descriptor.source_device_uuid,
            )
        )
    manifest = ScanManifest(
        source=str(root_path.resolve()),
        generated_at=datetime.now(timezone.utc).isoformat(),
        records=records,
        source_id=descriptor.source_id,
        source_type=descriptor.source_type,
        source_label=descriptor.source_label,
        source_device_uuid=descriptor.source_device_uuid,
    )
    return LocalScanResult(manifest=manifest)