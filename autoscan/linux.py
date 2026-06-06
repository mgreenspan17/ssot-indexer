from __future__ import annotations

"""Mockable Linux autoscan trigger logic based on mount set diffs."""

from pathlib import Path

from scanner.autoscan import AutoScanEvent


def detect_mount_events(previous_mounts: set[str], current_mounts: set[str]) -> list[AutoScanEvent]:
    new_mounts = sorted(current_mounts - previous_mounts)
    return [AutoScanEvent(platform="linux", mount_path=mount, provider_hint=_hint_provider(mount)) for mount in new_mounts]


def _hint_provider(mount: str) -> str | None:
    name = Path(mount).name.lower()
    if "google" in name:
        return "gdrive"
    if "one" in name:
        return "onedrive"
    if "dropbox" in name:
        return "dropbox"
    return None
