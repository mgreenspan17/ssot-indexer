from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shlex
import subprocess

from blake3 import blake3

from classify.classifier import classify_file
from hashing.blake3_utils import CHUNK_SIZE
from scanner.models import FileRecord, ScanManifest
from uuid.generator import uuid7_str


@dataclass(frozen=True)
class SSHConfig:
    host: str
    user: str | None = None
    port: int = 22
    identity_file: str | None = None


def _ssh_base(config: SSHConfig) -> list[str]:
    command = ["ssh", "-p", str(config.port)]
    if config.identity_file:
        command.extend(["-i", config.identity_file])
    destination = f"{config.user}@{config.host}" if config.user else config.host
    command.append(destination)
    return command


def _run_text(command: list[str]) -> str:
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    return completed.stdout


def _remote_find(config: SSHConfig, remote_root: str) -> list[str]:
    remote_command = f"find {shlex.quote(remote_root)} -type f -print"
    output = _run_text(_ssh_base(config) + [remote_command])
    return [line.strip() for line in output.splitlines() if line.strip()]


def _remote_stat(config: SSHConfig, remote_path: str) -> tuple[int, float, int]:
    remote_command = f"stat -c '%s %Y %a' {shlex.quote(remote_path)}"
    output = _run_text(_ssh_base(config) + [remote_command]).strip()
    size_text, mtime_text, mode_text = output.split()
    return int(size_text), float(mtime_text), int(mode_text, 8)


def _hash_remote_file(config: SSHConfig, remote_path: str) -> str:
    remote_command = f"cat -- {shlex.quote(remote_path)}"
    process = subprocess.Popen(_ssh_base(config) + [remote_command], stdout=subprocess.PIPE)
    if process.stdout is None:
        raise RuntimeError("failed to open ssh stdout stream")
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


def scan_ssh_directory(config: SSHConfig, remote_root: str) -> ScanManifest:
    records: list[FileRecord] = []
    for remote_path in _remote_find(config, remote_root):
        size, mtime, mode = _remote_stat(config, remote_path)
        classification = classify_file(Path(remote_path).name)
        records.append(
            FileRecord(
                uuid7=uuid7_str(),
                path=remote_path,
                source=f"ssh://{config.host}{remote_root}",
                size=size,
                mtime=mtime,
                mode=mode,
                hash_algorithm="blake3",
                blake3=_hash_remote_file(config, remote_path),
                category=classification.category,
                mime_type=classification.mime_type,
                shortcut_allowed=classification.shortcut_allowed,
            )
        )
    return ScanManifest(source=f"ssh://{config.host}{remote_root}", generated_at="", records=records)
