# Source Tracking

Assumptions:
- Every FileRecord and ScanManifest carries source identity metadata.
- Source metadata is derived consistently by shared helpers in scanner/base.py.

Fields:
- source_id
- source_type
- source_label
- source_device_uuid

Source type rules:
- local
- windows
- wsl
- gdrive
- onedrive
- dropbox
- external
- network
- provider

ASCII flow:
provider/root
  -> source descriptor
     -> source_id
     -> source_type
     -> source_label
     -> source_device_uuid
  -> FileRecord + ScanManifest

Integration notes:
- Warp can replace hashed fallbacks with stable volume GUIDs, account IDs, or root-folder identifiers.
