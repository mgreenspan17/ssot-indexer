from scanner.local import LocalScanResult, scan_local_directory
from scanner.models import FileRecord, ScanManifest, SourceType
from scanner.factory import scan_any_target, scan_provider
from scanner.providers.registry import detect_provider_scanner, get_provider_metadata, get_provider_scanner, list_provider_names
from scanner.service import ScanResult, manifest_to_json, scan_target

try:
	from scanner.rclone import RcloneConfig, scan_rclone_directory
except Exception:  # pragma: no cover - optional external/runtime dependency
	RcloneConfig = None  # type: ignore[assignment]
	scan_rclone_directory = None  # type: ignore[assignment]

try:
	from scanner.ssh import SSHConfig, scan_ssh_directory
except Exception:  # pragma: no cover - optional external/runtime dependency
	SSHConfig = None  # type: ignore[assignment]
	scan_ssh_directory = None  # type: ignore[assignment]

