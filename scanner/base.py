from __future__ import annotations

"""Shared scanner primitives for cross-platform and provider-backed scans.

Assumptions:
- All scanners emit the existing FileRecord and ScanManifest dataclasses.
- File content may be unavailable for cloud placeholders; metadata hashing is an acceptable fallback.

Boundaries:
- This module does not perform provider autodiscovery.
- It only offers reusable path, hashing, and record-building helpers.

Integration notes:
- Provider modules should rely on these helpers to keep manifests consistent.
- Warp can later replace metadata fallback hashing with provider-native content fetches.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
from stat import S_ISREG
from typing import Any, Iterable

from classify.classifier import classify_file
from hashing.blake3_utils import hash_bytes, hash_file
from scanner.models import FileRecord, ScanManifest, SourceType
from uuid.generator import uuid7_str


WINDOWS_EXCLUDED_DIRS = {
    "$recycle.bin",
    "program files",
    "program files (x86)",
    "programdata",
    "system volume information",
    "windows",
}
USER_HINT_DIRS = ("Desktop", "Documents", "Downloads", "Pictures", "Music", "Videos")
GOOGLE_PSEUDO_MIME_TYPES = {
    ".gdoc": "application/vnd.google-apps.document",
    ".gsheet": "application/vnd.google-apps.spreadsheet",
    ".gslides": "application/vnd.google-apps.presentation",
    ".gdraw": "application/vnd.google-apps.drawing",
    ".gform": "application/vnd.google-apps.form",
    ".gsite": "application/vnd.google-apps.site",
    ".gshortcut": "application/vnd.google-apps.shortcut",
}


@dataclass(frozen=True)
class PathTranslation:
    original: str
    translated: str
    environment: str


@dataclass(frozen=True)
class SourceDescriptor:
    source_id: str
    source_type: SourceType
    source_label: str | None
    source_device_uuid: str | None


def normalize_windows_path(path: str | Path) -> str:
    value = str(path)
    if not is_windows_path(value):
        return value
    if value.startswith("\\\\?\\"):
        return value
    if value.startswith("\\\\"):
        suffix = value.lstrip("\\")
        return f"\\\\?\\UNC\\{suffix}"
    return f"\\\\?\\{value}"


def is_windows_path(value: str) -> bool:
    if value.startswith("\\\\"):
        return True
    return len(value) >= 2 and value[1] == ":"


def is_wsl_path(value: str) -> bool:
    path = PurePosixPath(value)
    return len(path.parts) >= 3 and path.parts[1] == "mnt"


def windows_to_wsl_path(value: str) -> PathTranslation:
    path = PureWindowsPath(value)
    drive = path.drive.rstrip(":").lower()
    suffix = "/".join(path.parts[1:])
    translated = f"/mnt/{drive}"
    if suffix:
        translated = f"{translated}/{suffix}"
    return PathTranslation(original=value, translated=translated.replace("\\", "/"), environment="wsl")


def wsl_to_windows_path(value: str) -> PathTranslation:
    path = PurePosixPath(value)
    if not is_wsl_path(value):
        return PathTranslation(original=value, translated=value, environment="windows")
    drive = path.parts[2].upper()
    if len(path.parts) > 3:
        suffix = "\\".join(path.parts[3:])
        translated = f"{drive}:\\{suffix}"
    else:
        translated = f"{drive}:\\"
    return PathTranslation(original=value, translated=translated, environment="windows")


def candidate_user_roots(home: Path | None = None) -> list[Path]:
    base = home or Path.home()
    candidates = [base / name for name in USER_HINT_DIRS if (base / name).exists()]
    return candidates or [base]


def _stable_source_hash(payload: dict[str, Any]) -> str:
    return hash_bytes(json.dumps(payload, sort_keys=True).encode("utf-8")).digest


def determine_source_type(provider_name: str, root: str | Path) -> SourceType:
    normalized = provider_name.lower()
    if normalized in {"windows", "wsl", "gdrive", "onedrive", "dropbox"}:
        return normalized  # type: ignore[return-value]
    root_path = str(root)
    if root_path.startswith("\\\\"):
        return "network"
    if root_path.startswith("/mnt/") or root_path.startswith("/media/") or root_path.startswith("/run/media/"):
        return "external"
    if normalized in {"local", "ssh", "rclone"}:
        return "local"
    return "provider"


def build_source_descriptor(
    provider_name: str,
    root: str | Path,
    *,
    source_label: str | None = None,
    provider_account_id: str | None = None,
    source_device_uuid: str | None = None,
) -> SourceDescriptor:
    root_text = str(root)
    source_type = determine_source_type(provider_name, root_text)
    device_uuid = source_device_uuid or provider_account_id
    if device_uuid is None:
        try:
            stat_result = Path(root_text).stat()
            device_uuid = _stable_source_hash({"provider": provider_name, "device": stat_result.st_dev})
        except OSError:
            device_uuid = _stable_source_hash({"provider": provider_name, "root": root_text})
    source_id = _stable_source_hash(
        {
            "provider": provider_name,
            "root": root_text,
            "device_uuid": device_uuid,
            "label": source_label,
        }
    )
    label = source_label or Path(root_text).name or root_text
    return SourceDescriptor(
        source_id=source_id,
        source_type=source_type,
        source_label=label,
        source_device_uuid=device_uuid,
    )


def derive_cloud_root_id(provider_name: str, root: str | Path) -> str:
    return _stable_source_hash({"provider": provider_name, "root": str(root), "kind": "cloud-root"})


def path_metadata_payload(path: Path, *, provider_name: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "path": str(path),
        "provider": provider_name,
        "is_symlink": path.is_symlink(),
    }
    try:
        stat_result = path.stat()
        payload.update(
            {
                "size": stat_result.st_size,
                "mtime": stat_result.st_mtime,
                "mode": stat_result.st_mode,
            }
        )
    except OSError:
        payload["stat_error"] = True
    if extra:
        payload.update(extra)
    return payload


def iter_regular_files(root: str | Path, excluded_dirs: Iterable[str] | None = None) -> list[Path]:
    root_path = Path(root)
    records: list[Path] = []
    excluded = {name.lower() for name in (excluded_dirs or ())}
    system_exclusions = {"containerd", "docker", "lost+found"}
    excluded.update(system_exclusions)
    for current_root, dirs, files in os.walk(root_path):
        if excluded:
            dirs[:] = [name for name in dirs if name.lower() not in excluded]
        for file_name in files:
            path = Path(current_root) / file_name
            try:
                stat_result = path.stat()
            except OSError:
                continue
            if S_ISREG(stat_result.st_mode):
                records.append(path)
    return records


def manifest_from_records(source: str, records: list[FileRecord], descriptor: SourceDescriptor | None = None) -> ScanManifest:
    source_descriptor = descriptor or build_source_descriptor("local", source)
    return ScanManifest(
        source=source,
        generated_at=datetime.now(timezone.utc).isoformat(),
        records=records,
        source_id=source_descriptor.source_id,
        source_type=source_descriptor.source_type,
        source_label=source_descriptor.source_label,
        source_device_uuid=source_descriptor.source_device_uuid,
    )


def _hash_with_fallback(path: Path, fallback_payload: dict[str, Any]) -> tuple[str, str, str]:
    try:
        from hashing.blake3_utils import dual_hash_file
        hash_result = dual_hash_file(path)
        return hash_result.algorithm, hash_result.blake3_digest, hash_result.sha256_digest
    except OSError:
        import hashlib
        payload = json.dumps(fallback_payload, sort_keys=True).encode("utf-8")
        hash_result = hash_bytes(payload)
        sha256_digest = hashlib.sha256(payload).hexdigest()
        return "fallback", hash_result.digest, sha256_digest


def build_file_record(
    path: Path,
    *,
    source: str,
    source_descriptor: SourceDescriptor | None = None,
    record_path: str | None = None,
    mime_type_override: str | None = None,
    metadata_payload: dict[str, Any] | None = None,
) -> FileRecord:
    stat_result = path.stat()
    fallback_payload = metadata_payload or {
        "path": str(path),
        "size": stat_result.st_size,
        "mtime": stat_result.st_mtime,
    }
    classification = classify_file(path)
    algorithm, blake3_digest, sha256_digest = _hash_with_fallback(path, fallback_payload)
    mime_type = mime_type_override or classification.mime_type
    descriptor = source_descriptor or build_source_descriptor("local", source)
    return FileRecord(
        uuid7=uuid7_str(),
        path=record_path or str(path.resolve()),
        source=source,
        size=stat_result.st_size,
        mtime=stat_result.st_mtime,
        mode=stat_result.st_mode,
        hash_algorithm=algorithm,
        blake3=blake3_digest,
        sha256=sha256_digest,
        category=classification.category,
        mime_type=mime_type,
        shortcut_allowed=classification.shortcut_allowed,
        source_id=descriptor.source_id,
        source_type=descriptor.source_type,
        source_label=descriptor.source_label,
        source_device_uuid=descriptor.source_device_uuid,
    )
