from __future__ import annotations

from dataclasses import dataclass

from shortcuts.generator import create_shortcut


@dataclass(frozen=True)
class ShortcutHealth:
    name: str = "shortcut"

    def check(self) -> bool:
        return callable(create_shortcut)

    def status(self) -> str:
        return "ok" if self.check() else "degraded"

    def summary(self) -> dict[str, str]:
        return {"name": self.name, "status": self.status(), "detail": "Shortcut generator is available"}


def check() -> dict[str, object]:
    health = ShortcutHealth()
    return {"component": health.name, "healthy": health.check(), "detail": health.summary()["detail"]}


def status() -> str:
    return ShortcutHealth().status()


def summary() -> str:
    return ShortcutHealth().summary()["detail"]
