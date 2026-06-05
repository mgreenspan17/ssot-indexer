from __future__ import annotations

from dataclasses import dataclass
import json
import subprocess

from blake3 import blake3

from classify.classifier import classify_file
from hashing.blake3_utils import CHUNK_SIZE
from scanner.models import FileRecord, ScanManifest
from uuid.generator import uuid7_str


@dataclass(frozen=True)
class RcloneConfig:
    remote: str
    extra_args: tuple[str, ...] = ()


def _rclone_base(config: RcloneConfig) -> list[str]:
    return ["rclone", *config.extra_args]


def _lsjson(config: RcloneConfig, remote_root: str) -> list[dict[str, object]]:
    command = _rclone_base(config) + ["lsjson", f"{config.remote}:{remote_root}", "--recursive"]
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    return json.loads(completed.stdout)


def _hash_rclone_file(config: RcloneConfig, remote_path: str) -> str:
    command = _rclone_base(config) + ["cat", f"{config.remote}:{remote_path}"]
    process = subprocess.Popen(command, stdout=subprocess.PIPE)
    if process.stdout is None:
        raise RuntimeError("failed to open rclone stdout stream")
    hasher = blake3()
    while True:
        chunk = process.stdout.read(CHUNK_SIZE)
        if not chunk:
            break
        hasher.update(chunk)
    exit_code = process.wait()
    if exit_code != 0:
        raise subprocess.CalledProcessError(exit_code, process.args)
    return hasher.hexdigest()


def scan_rclone_directory(config: RcloneConfig, remote_root: str) -> ScanManifest:
    records: list[FileRecord] = []
    for item in _lsjson(config, remote_root):
        if item.get("IsDir"):
            continue
        remote_path = str(item.get("Path", ""))
        classification = classify_file(remote_path)
        records.append(
            FileRecord(
                uuid7=uuid7_str(),
                path=remote_path,
                source=f"rclone://{config.remote}/{remote_root}",
                size=int(item.get("Size", 0) or 0),
                mtime=0.0,
                mode=0,
                hash_algorithm="blake3",
                blake3=_hash_rclone_file(config, remote_path),
                category=classification.category,
                mime_type=classification.mime_type,
                shortcut_allowed=classification.shortcut_allowed,
            )
        )
    return ScanManifest(source=f"rclone://{config.remote}/{remote_root}", generated_at="", records=records)
