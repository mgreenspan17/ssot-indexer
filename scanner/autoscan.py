from __future__ import annotations

"""Autoscan orchestration for mount-triggered scans.

Assumptions:
- Autoscan watchers may be platform-specific, but the orchestration layer is shared.
- Submission to the ingestion worker can be injected as a callback.

Boundaries:
- This module coordinates scans; it does not install system services by itself.

Integration notes:
- Warp can wire linux.py/windows.py/wsl.py to real event sources later.
- The ingestion submission callback can be replaced with the real worker enqueue function.
"""

from dataclasses import asdict, dataclass
from pathlib import Path
import json
import logging
from typing import Any, Callable

from scanner.factory import scan_any_target


logger = logging.getLogger(__name__)
AUTOSCAN_STATE_PATH = Path(".ssot_autoscan_state.json")


@dataclass(frozen=True)
class AutoScanStatus:
    enabled: bool
    state_path: str


@dataclass(frozen=True)
class AutoScanEvent:
    platform: str
    mount_path: str
    provider_hint: str | None = None


@dataclass(frozen=True)
class AutoScanResult:
    mount_path: str
    provider: str
    source_id: str
    submitted: bool
    record_count: int


class AutoScanManager:
    def __init__(self, state_path: Path | None = None):
        self.state_path = state_path or AUTOSCAN_STATE_PATH

    def _write_state(self, enabled: bool) -> dict[str, Any]:
        payload = {"enabled": enabled, "state_path": str(self.state_path)}
        self.state_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return payload

    def enable(self) -> dict[str, Any]:
        return self._write_state(True)

    def disable(self) -> dict[str, Any]:
        return self._write_state(False)

    def status(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return asdict(AutoScanStatus(enabled=False, state_path=str(self.state_path)))
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def handle_event(
        self,
        event: AutoScanEvent,
        *,
        submit_manifest: Callable[[dict[str, Any]], bool] | None = None,
    ) -> AutoScanResult:
        manifest = scan_any_target(event.mount_path)
        submitter = submit_manifest or (lambda payload: True)
        submitted = submitter(manifest.to_dict())
        logger.info("autoscan processed mount %s provider=%s submitted=%s", event.mount_path, manifest.source_type, submitted)
        return AutoScanResult(
            mount_path=event.mount_path,
            provider=manifest.source_type,
            source_id=manifest.source_id,
            submitted=submitted,
            record_count=len(manifest.records),
        )
