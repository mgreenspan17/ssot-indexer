from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import json

from scanner.factory import scan_any_target
from scanner.local import scan_local_directory
from scanner.models import ScanManifest
from scanner.rclone import RcloneConfig, scan_rclone_directory
from scanner.ssh import SSHConfig, scan_ssh_directory


@dataclass(frozen=True)
class ScanResult:
    manifest: ScanManifest


def scan_target(target: str) -> ScanResult:
    if target.startswith("ssh://"):
        body = target.removeprefix("ssh://")
        host, _, path = body.partition("/")
        manifest = scan_ssh_directory(SSHConfig(host=host), f"/{path}")
        return ScanResult(manifest=manifest)
    if target.startswith("rclone://"):
        body = target.removeprefix("rclone://")
        remote, _, path = body.partition("/")
        manifest = scan_rclone_directory(RcloneConfig(remote=remote), path)
        return ScanResult(manifest=manifest)
    if target == "auto":
        return ScanResult(manifest=scan_any_target(target))
    if Path(target).exists():
        return ScanResult(manifest=scan_local_directory(target).manifest)
    return ScanResult(manifest=scan_any_target(target))


def manifest_to_json(manifest: ScanManifest) -> str:
    payload = manifest.to_dict()
    if not payload["generated_at"]:
        payload["generated_at"] = datetime.now(timezone.utc).isoformat()
    return json.dumps(payload, indent=2, sort_keys=True)
