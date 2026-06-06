from __future__ import annotations

import os
from pathlib import Path

from scanner.base import build_file_record, is_wsl_path, iter_regular_files, manifest_from_records, windows_to_wsl_path, wsl_to_windows_path
from scanner.models import ScanManifest
from scanner.providers.base import ProviderScanner


class WSLScanner(ProviderScanner):
    provider_name = "wsl"

    def detect(self, target: str | None = None) -> bool:
        if target is not None:
            return is_wsl_path(target)
        return bool(os.environ.get("WSL_DISTRO_NAME"))

    def scan(self, target: str | None = None) -> ScanManifest:
        root_text = target or "/mnt/c"
        root = Path(root_text)
        source = f"wsl://{root_text}"
        records = [
            build_file_record(path, source=source, record_path=str(path).replace("\\", "/"))
            for path in iter_regular_files(root)
        ]
        return manifest_from_records(source, records)


__all__ = ["WSLScanner", "windows_to_wsl_path", "wsl_to_windows_path"]
