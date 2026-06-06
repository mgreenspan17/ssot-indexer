# WSL Scanner

Assumptions:
- WSL paths use /mnt/<drive> for Windows-backed mounts.

Boundaries:
- The scanner emits WSL-style paths in the manifest.

Integration notes:
- Warp can later augment this with distro-aware mount discovery.
- Source tracking is derived per mount root so manifests remain attributable across /mnt/c, /mnt/d, and similar paths.

Path translation:
- Windows -> WSL: C:\\Users\\name -> /mnt/c/Users/name
- WSL -> Windows: /mnt/c/Users/name -> C:\\Users\\name

ASCII flow:
/mnt/c/path
  -> local walk in WSL-visible tree
  -> path translation metadata
  -> FileRecord
  -> ScanManifest
