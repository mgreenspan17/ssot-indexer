from __future__ import annotations

"""Mockable WSL autoscan trigger logic based on /mnt subtree changes."""

from scanner.autoscan import AutoScanEvent


def detect_mount_events(previous_mounts: set[str], current_mounts: set[str]) -> list[AutoScanEvent]:
    new_mounts = sorted(current_mounts - previous_mounts)
    return [AutoScanEvent(platform="wsl", mount_path=mount, provider_hint="wsl") for mount in new_mounts if mount.startswith("/mnt/")]
