# Dropbox Scanner

Assumptions:
- Dropbox sync root is locally visible when installed.

Boundaries:
- Smart Sync items fall back to metadata hashing if content is unavailable.

Integration notes:
- Warp can later add Dropbox API-backed file state enrichment.

Special handling:
- Smart Sync
- online-only files

ASCII flow:
Dropbox root
  -> walk synced items
  -> hash content or metadata
  -> ScanManifest
