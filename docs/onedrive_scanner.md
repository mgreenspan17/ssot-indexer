# OneDrive Scanner

Assumptions:
- OneDrive exposes a local sync folder under the user profile.

Boundaries:
- Placeholder files still emit FileRecord entries using metadata fallback if needed.

Integration notes:
- Warp can later map Windows cloud attributes into richer placeholder flags.

Special handling:
- cloud-only files
- placeholders
- selective sync roots

ASCII flow:
OneDrive root
  -> detect synced files
  -> hash content or metadata fallback
  -> ScanManifest
