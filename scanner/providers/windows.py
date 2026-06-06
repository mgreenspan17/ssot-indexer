from __future__ import annotations

import os
from pathlib import Path

from scanner.base import WINDOWS_EXCLUDED_DIRS, build_file_record, candidate_user_roots, iter_regular_files, manifest_from_records
from scanner.models import ScanManifest
from scanner.providers.base import ProviderScanner


class WindowsScanner(ProviderScanner):
    provider_name = "windows"

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
        records = [
            build_file_record(path, source=source, record_path=str(path))
            for path in iter_regular_files(root, excluded_dirs=WINDOWS_EXCLUDED_DIRS)
        ]
        return manifest_from_records(source, records)
