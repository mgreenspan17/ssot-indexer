from __future__ import annotations

import json
import os
from pathlib import Path

from scanner.base import GOOGLE_PSEUDO_MIME_TYPES, build_file_record, iter_regular_files, manifest_from_records
from scanner.models import ScanManifest
from scanner.providers.base import ProviderScanner


def _candidate_roots() -> list[Path]:
    user_profile = Path(os.environ.get("USERPROFILE", str(Path.home())))
    return [
        user_profile / "Google Drive",
        user_profile / "My Drive",
        user_profile / "Shared drives",
    ]


class GoogleDriveScanner(ProviderScanner):
    provider_name = "gdrive"

    def detect(self, target: str | None = None) -> bool:
        if target:
            return "google drive" in target.lower() or Path(target).suffix.lower() in GOOGLE_PSEUDO_MIME_TYPES
        return any(path.exists() for path in _candidate_roots())

    def default_target(self) -> Path | None:
        for path in _candidate_roots():
            if path.exists():
                return path
        return None

    def scan(self, target: str | None = None) -> ScanManifest:
        root = Path(target) if target else self.default_target()
        if root is None:
            raise FileNotFoundError("Google Drive root not detected")
        source = f"gdrive://{root}"
        records = []
        for path in iter_regular_files(root):
            suffix = path.suffix.lower()
            metadata_payload = {
                "path": str(path),
                "provider": self.provider_name,
                "offline": False,
                "pseudo_file": suffix in GOOGLE_PSEUDO_MIME_TYPES,
            }
            if suffix in GOOGLE_PSEUDO_MIME_TYPES:
                try:
                    metadata_payload["descriptor"] = json.loads(path.read_text(encoding="utf-8"))
                except Exception:
                    metadata_payload["descriptor"] = path.read_text(encoding="utf-8", errors="ignore")
            records.append(
                build_file_record(
                    path,
                    source=source,
                    record_path=str(path),
                    mime_type_override=GOOGLE_PSEUDO_MIME_TYPES.get(suffix),
                    metadata_payload=metadata_payload,
                )
            )
        return manifest_from_records(source, records)
