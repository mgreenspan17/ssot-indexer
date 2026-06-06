from __future__ import annotations

"""Scanner factory that auto-selects local, remote, or provider-specific scanners."""

from pathlib import Path

from scanner.base import is_windows_path, is_wsl_path
from scanner.local import scan_local_directory
from scanner.models import ScanManifest
from scanner.providers.registry import get_provider_scanner, list_provider_names


def scan_provider(name: str, target: str | None = None) -> ScanManifest:
    scanner = get_provider_scanner(name)
    return scanner.scan(target)


def scan_any_target(target: str) -> ScanManifest:
    target_path = Path(target)
    if target in list_provider_names():
        return scan_provider(target)
    if is_windows_path(target):
        return scan_provider("windows", target)
    if is_wsl_path(target):
        return scan_provider("wsl", target)
    lowered = target.lower()
    if "google drive" in lowered:
        return scan_provider("gdrive", target)
    if "onedrive" in lowered:
        return scan_provider("onedrive", target)
    if "dropbox" in lowered:
        return scan_provider("dropbox", target)
    if target_path.exists():
        return scan_local_directory(target).manifest
    raise FileNotFoundError(f"unsupported scan target: {target}")
