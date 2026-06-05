from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from scanner.service import scan_target


@dataclass(frozen=True)
class ScannerHealth:
    name: str = "scanner"

    def check(self) -> bool:
        with TemporaryDirectory() as temp_dir:
            sample = Path(temp_dir) / "health.txt"
            sample.write_text("health check\n", encoding="utf-8")
            result = scan_target(temp_dir)
        return bool(result.manifest.records)

    def status(self) -> str:
        return "ok" if self.check() else "degraded"

    def summary(self) -> dict[str, str]:
        return {"name": self.name, "status": self.status(), "detail": "Scanner dry-run completed"}


def check() -> dict[str, object]:
    health = ScannerHealth()
    return {"component": health.name, "healthy": health.check(), "detail": health.summary()["detail"]}


def status() -> str:
    return ScannerHealth().status()


def summary() -> str:
    return ScannerHealth().summary()["detail"]
