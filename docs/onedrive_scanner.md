# OneDrive Scanner

Assumptions:
- OneDrive exposes a local sync folder under the user profile.

Boundaries:
- Placeholder files still emit FileRecord entries using metadata fallback if needed.

Integration notes:
- Warp can later map Windows cloud attributes into richer placeholder flags.
- Source tracking is derived from the detected OneDrive root and carried into each record.

Special handling:
- cloud-only files
- placeholders
- selective sync roots
- metadata fallback hashing when content is not fully materialized

ASCII flow:
OneDrive root
  -> detect synced files
  -> hash content or metadata fallback
  -> ScanManifest
