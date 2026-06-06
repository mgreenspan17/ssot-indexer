from __future__ import annotations

import os
from pathlib import Path

from scanner.base import build_file_record, build_source_descriptor, derive_cloud_root_id, iter_regular_files, manifest_from_records, path_metadata_payload
from scanner.models import ScanManifest
from scanner.providers.base import ProviderScanner


def _candidate_roots() -> list[Path]:
    user_profile = Path(os.environ.get("USERPROFILE", str(Path.home())))
    roots = [user_profile / "OneDrive"]
    roots.extend(candidate for candidate in user_profile.glob("OneDrive*") if candidate.is_dir())
    return roots


class OneDriveScanner(ProviderScanner):
    provider_name = "onedrive"
    capabilities = ("scan", "source_tracking", "placeholders", "selective_sync")
    description = "OneDrive sync-root scanner with placeholder awareness"

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
        descriptor = build_source_descriptor(
            "onedrive",
            root,
            source_label=root.name or "OneDrive",
            provider_account_id=derive_cloud_root_id("onedrive", root),
        )
        records = []
        for path in iter_regular_files(root):
            records.append(
                build_file_record(
                    path,
                    source=source,
                    source_descriptor=descriptor,
                    record_path=str(path),
                    metadata_payload=path_metadata_payload(
                        path,
                        provider_name=self.provider_name,
                        extra={
                            "placeholder": path.suffix.lower() in {".url", ".cloud"},
                            "selective_sync": "archive" in path.parts,
                        },
                    ),
                )
            )
        return manifest_from_records(source, records, descriptor)
