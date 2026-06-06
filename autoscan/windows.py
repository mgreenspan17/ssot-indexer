from __future__ import annotations

"""Mockable Windows autoscan trigger logic based on drive arrival events."""

from scanner.autoscan import AutoScanEvent


def detect_volume_events(previous_volumes: set[str], current_volumes: set[str]) -> list[AutoScanEvent]:
    new_volumes = sorted(current_volumes - previous_volumes)
    return [AutoScanEvent(platform="windows", mount_path=volume, provider_hint=None) for volume in new_volumes]
