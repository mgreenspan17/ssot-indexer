from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class SSOTScanTask:
    target: str
    dry_run: bool = True


@dataclass(frozen=True)
class SSOTIngestTask:
    manifest_path: str
    canonicalize: bool = True


@dataclass(frozen=True)
class SSOTCanonicalizeTask:
    manifest_path: str
    storage_root: str = "/ssot"


def scan_task(target: str) -> dict[str, Any]:
    return asdict(SSOTScanTask(target=target))


def ingest_task(manifest_path: str) -> dict[str, Any]:
    return asdict(SSOTIngestTask(manifest_path=manifest_path))


def canonicalize_task(manifest_path: str) -> dict[str, Any]:
    return asdict(SSOTCanonicalizeTask(manifest_path=manifest_path))
