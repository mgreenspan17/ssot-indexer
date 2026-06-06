# Cross-Platform Scanner Architecture

Assumptions:
- Linux local scanning already exists and remains valid.
- Cross-platform providers must converge on the same manifest contract.

Boundaries:
- The abstraction layer chooses scanners; providers implement platform specifics.

Integration notes:
- ssotctl routes explicit provider scans.
- scanner.service preserves existing scan_target behavior and delegates to the new factory when appropriate.

ASCII architecture:

scan_target / ssotctl scan
  -> scanner.factory
     -> local / ssh / rclone
     -> provider registry
        -> windows
        -> wsl
        -> gdrive
        -> onedrive
        -> dropbox
  -> ScanManifest

Testing strategy:
- provider registry discovery tests
- path translation tests
- pseudo-file manifest tests
- CLI serialization tests
