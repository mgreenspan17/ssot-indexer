from autoscan.linux import detect_mount_events as detect_linux_mount_events
from autoscan.windows import detect_volume_events as detect_windows_volume_events
from autoscan.wsl import detect_mount_events as detect_wsl_mount_events

__all__ = [
    "detect_linux_mount_events",
    "detect_windows_volume_events",
    "detect_wsl_mount_events",
]
