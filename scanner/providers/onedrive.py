from __future__ import annotations

import os
from pathlib import Path

from scanner.base import build_file_record, iter_regular_files, manifest_from_records
from scanner.models import ScanManifest
from scanner.providers.base import ProviderScanner


def _candidate_roots() -> list[Path]:
    user_profile = Path(os.environ.get("USERPROFILE", str(Path.home())))
    roots = [user_profile / "OneDrive"]
    roots.extend(candidate for candidate in user_profile.glob("OneDrive*") if candidate.is_dir())
    return roots


class OneDriveScanner(ProviderScanner):
    provider_name = "onedrive"

    def detect(self, target: str | None = None) -> bool:
        if target:
            return "onedrive" in target.lower()
        return any(path.exists() for path in _candidate_roots())

    def default_target(self) -> Path | None:
        for path in _candidate_roots():
            if path.exists():
                return path
        return None

    def scan(self, target: str | None = None) -> ScanManifest:
        root = Path(target) if target else self.default_target()
        if root is None:
            raise FileNotFoundError("OneDrive root not detected")
        source = f"onedrive://{root}"
        records = []
        for path in iter_regular_files(root):
            records.append(
                build_file_record(
                    path,
                    source=source,
                    record_path=str(path),
                    metadata_payload={
                        "path": str(path),
                        "provider": self.provider_name,
                        "placeholder": path.suffix.lower() in {".url", ".cloud"},
                    },
                )
            )
        return manifest_from_records(source, records)
