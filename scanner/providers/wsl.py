from __future__ import annotations

import os
from pathlib import Path

from scanner.base import build_file_record, build_source_descriptor, is_wsl_path, iter_regular_files, manifest_from_records, path_metadata_payload, windows_to_wsl_path, wsl_to_windows_path
from scanner.models import ScanManifest
from scanner.providers.base import ProviderScanner


class WSLScanner(ProviderScanner):
    provider_name = "wsl"
    capabilities = ("scan", "source_tracking", "path_translation", "symlink_aware")
    description = "WSL-aware scanner for Windows-backed mounts"

    def detect(self, target: str | None = None) -> bool:
        if target is not None:
            return is_wsl_path(target)
        return bool(os.environ.get("WSL_DISTRO_NAME"))

    def scan(self, target: str | None = None) -> ScanManifest:
        root_text = target or "/mnt/c"
        root = Path(root_text)
        source = f"wsl://{root_text}"
        descriptor = build_source_descriptor("wsl", root_text, source_label=root.name or root_text)
        records = [
            build_file_record(
                path,
                source=source,
                source_descriptor=descriptor,
                record_path=str(path).replace("\\", "/"),
                metadata_payload=path_metadata_payload(
                    path,
                    provider_name=self.provider_name,
                    extra={
                        "windows_path": wsl_to_windows_path(str(path)).translated,
                        "is_symlink": path.is_symlink(),
                        "case_sensitive_path": str(path),
                    },
                ),
            )
            for path in iter_regular_files(root)
        ]
        return manifest_from_records(source, records, descriptor)


__all__ = ["WSLScanner", "windows_to_wsl_path", "wsl_to_windows_path"]
