from __future__ import annotations

import os
from pathlib import Path

from scanner.base import WINDOWS_EXCLUDED_DIRS, build_file_record, build_source_descriptor, candidate_user_roots, iter_regular_files, manifest_from_records, normalize_windows_path, path_metadata_payload
from scanner.models import ScanManifest
from scanner.providers.base import ProviderScanner


class WindowsScanner(ProviderScanner):
    provider_name = "windows"
    capabilities = ("scan", "source_tracking", "long_paths", "windows_metadata")
    description = "Native Windows and NTFS-aware scanner"

    def detect(self, target: str | None = None) -> bool:
        if target is None:
            return os.name == "nt"
        return len(target) >= 2 and target[1] == ":"

    def default_target(self) -> Path | None:
        roots = candidate_user_roots(Path.home())
        return roots[0] if roots else Path.home()

    def scan(self, target: str | None = None) -> ScanManifest:
        root = Path(target) if target else (self.default_target() or Path.home())
        source = f"windows://{root}"
        descriptor = build_source_descriptor("windows", root, source_label=root.name or str(root))
        records = [
            build_file_record(
                path,
                source=source,
                source_descriptor=descriptor,
                record_path=normalize_windows_path(path),
                metadata_payload=path_metadata_payload(
                    path,
                    provider_name=self.provider_name,
                    extra={
                        "hidden": path.name.startswith("."),
                        "system_like": any(part.lower() in WINDOWS_EXCLUDED_DIRS for part in path.parts),
                        "onedrive_placeholder": path.suffix.lower() in {".cloud", ".url"},
                        "is_symlink": path.is_symlink(),
                    },
                ),
            )
            for path in iter_regular_files(root, excluded_dirs=WINDOWS_EXCLUDED_DIRS)
        ]
        return manifest_from_records(source, records, descriptor)
