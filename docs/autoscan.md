# Autoscan

Assumptions:
- Autoscan reacts to mount or volume arrival events.
- The orchestration layer is shared and platform backends are mockable.

Flow:
mount event
  -> platform backend detects new mount
  -> scanner.autoscan builds AutoScanEvent
  -> scan_any_target(mount)
  -> ScanManifest
  -> ingestion submit callback
  -> log result

Backends:
- autoscan/linux.py
- autoscan/windows.py
- autoscan/wsl.py

CLI:
- ssotctl autoscan enable
- ssotctl autoscan disable
- ssotctl autoscan status

Integration notes:
- Warp can later connect linux.py to udev/systemd path units.
- Warp can later connect windows.py to Win32 volume notifications.
- Warp can later connect wsl.py to inotify on /mnt/*.
