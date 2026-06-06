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
from scanner.models import FileRecord, ScanManifest
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


def iter_regular_files(root: str | Path, excluded_dirs: Iterable[str] | None = None) -> list[Path]:
    root_path = Path(root)
    records: list[Path] = []
    excluded = {name.lower() for name in (excluded_dirs or ())}
    for current_root, dirs, files in os.walk(root_path):
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


def manifest_from_records(source: str, records: list[FileRecord]) -> ScanManifest:
    return ScanManifest(source=source, generated_at=datetime.now(timezone.utc).isoformat(), records=records)


def _hash_with_fallback(path: Path, fallback_payload: dict[str, Any]) -> tuple[str, str]:
    try:
        hash_result = hash_file(path)
        return hash_result.algorithm, hash_result.digest
    except OSError:
        payload = json.dumps(fallback_payload, sort_keys=True).encode("utf-8")
        hash_result = hash_bytes(payload)
        return hash_result.algorithm, hash_result.digest


def build_file_record(
    path: Path,
    *,
    source: str,
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
    algorithm, digest = _hash_with_fallback(path, fallback_payload)
    mime_type = mime_type_override or classification.mime_type
    return FileRecord(
        uuid7=uuid7_str(),
        path=record_path or str(path.resolve()),
        source=source,
        size=stat_result.st_size,
        mtime=stat_result.st_mtime,
        mode=stat_result.st_mode,
        hash_algorithm=algorithm,
        blake3=digest,
        category=classification.category,
        mime_type=mime_type,
        shortcut_allowed=classification.shortcut_allowed,
    )
