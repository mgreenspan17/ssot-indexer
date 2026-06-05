from __future__ import annotations

from dataclasses import dataclass

from orchestrator.service import SSOTOrchestrator


@dataclass(frozen=True)
class OrchestratorHealth:
    name: str = "orchestrator"

    def check(self) -> bool:
        orchestrator = SSOTOrchestrator()
        return orchestrator.storage_root.as_posix().endswith("/ssot")

    def status(self) -> str:
        return "ok" if self.check() else "degraded"

    def summary(self) -> dict[str, str]:
        return {"name": self.name, "status": self.status(), "detail": "Orchestrator configuration is loadable"}


def check() -> dict[str, object]:
    health = OrchestratorHealth()
    return {"component": health.name, "healthy": health.check(), "detail": health.summary()["detail"]}


def status() -> str:
    return OrchestratorHealth().status()


def summary() -> str:
    return OrchestratorHealth().summary()["detail"]
