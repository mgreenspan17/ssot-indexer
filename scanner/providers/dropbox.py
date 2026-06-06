from __future__ import annotations

import os
from pathlib import Path

from scanner.base import build_file_record, build_source_descriptor, derive_cloud_root_id, iter_regular_files, manifest_from_records, path_metadata_payload
from scanner.models import ScanManifest
from scanner.providers.base import ProviderScanner


def _candidate_roots() -> list[Path]:
    user_profile = Path(os.environ.get("USERPROFILE", str(Path.home())))
    return [user_profile / "Dropbox"]


class DropboxScanner(ProviderScanner):
    provider_name = "dropbox"
    capabilities = ("scan", "source_tracking", "smart_sync", "online_only")
    description = "Dropbox scanner with Smart Sync awareness"

    def detect(self, target: str | None = None) -> bool:
        if target:
            return "dropbox" in target.lower()
        return any(path.exists() for path in _candidate_roots())

    def default_target(self) -> Path | None:
        for path in _candidate_roots():
            if path.exists():
                return path
        return None

    def scan(self, target: str | None = None) -> ScanManifest:
        root = Path(target) if target else self.default_target()
        if root is None:
            raise FileNotFoundError("Dropbox root not detected")
        source = f"dropbox://{root}"
        descriptor = build_source_descriptor(
            "dropbox",
            root,
            source_label=root.name or "Dropbox",
            provider_account_id=derive_cloud_root_id("dropbox", root),
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
                            "smart_sync": path.suffix.lower() in {".url", ".dropbox"},
                            "online_only": path.suffix.lower() == ".dropbox",
                        },
                    ),
                )
            )
        return manifest_from_records(source, records, descriptor)
