# Windows Scanner

Assumptions:
- Native Windows paths are scanned directly from NTFS-visible roots.

Boundaries:
- System directories are excluded.
- The scanner emits the same ScanManifest schema as Linux.

Integration notes:
- Warp can later enrich this scanner with ADS, file-owner metadata, or USN Journal support.

Behavior:
- Walks NTFS-visible paths.
- Normalizes long paths with the extended-path prefix.
- Hashes file content with BLAKE3.
- Carries source tracking metadata into FileRecord and ScanManifest.
- Preserves symlink and placeholder hints in metadata fallback payloads.

ASCII flow:
Windows path
  -> filesystem walk
  -> metadata + hash + classify
  -> FileRecord
  -> ScanManifest

Troubleshooting:
- If a path is inaccessible, verify permissions.
- If long-path access is required, prefer rooted user directories or enable long path support in Windows policy.
- If OneDrive placeholders appear without content, metadata fallback hashing is expected until live Windows APIs are wired in.
