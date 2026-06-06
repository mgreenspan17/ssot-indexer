# Google Drive Scanner

Assumptions:
- Google Drive for Desktop exposes local sync roots or pseudo-file descriptors.

Boundaries:
- Pseudo-files are hashed from metadata when content is not materialized.

Integration notes:
- Warp can later replace metadata fallback with Google Drive API enrichment.

Special handling:
- .gdoc, .gsheet, .gslides, .gdraw, .gform, .gsite
- .gshortcut
- offline or online-only descriptors

ASCII flow:
Google Drive root
  -> scan local entries
  -> pseudo-file detection
  -> metadata hash fallback when needed
  -> ScanManifest
