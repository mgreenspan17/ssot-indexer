from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from canonical.store import CanonicalStoreManager


@dataclass(frozen=True)
class CanonicalStoreHealth:
    name: str = "canonical_store"

    def check(self) -> bool:
        manager = CanonicalStoreManager(Path("/ssot"), Path("/ssot/shortcuts"))
        return manager.canonical_path_for("sample").as_posix().endswith("/ssot/blake3/sample")

    def status(self) -> str:
        return "ok" if self.check() else "degraded"

    def summary(self) -> dict[str, str]:
        return {"name": self.name, "status": self.status(), "detail": "Canonical pathing is consistent"}


def check() -> dict[str, object]:
    health = CanonicalStoreHealth()
    return {"component": health.name, "healthy": health.check(), "detail": health.summary()["detail"]}


def status() -> str:
    return CanonicalStoreHealth().status()


def summary() -> str:
    return CanonicalStoreHealth().summary()["detail"]
