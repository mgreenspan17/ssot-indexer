"""Self-diagnostic loop for SSOT OS.

Assumptions:
- Health checks are pure functions that return structured data.

Boundaries:
- The diagnostics loop does not remediate; it reports and escalates.

Integration notes:
- Warp and Copilot can call this before and after high-impact changes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from health_checks.agent_check import check as agent_check
from health_checks.database_check import check as database_check
from health_checks.filesystem_check import check as filesystem_check
from health_checks.governance_check import check as governance_check
from health_checks.registry_check import check as registry_check


@dataclass(frozen=True)
class DiagnosticsReport:
    healthy: bool
    checks: dict[str, dict[str, Any]]
    events: tuple[dict[str, Any], ...] = ()


DEFAULT_CHECKS: tuple[tuple[str, Callable[[], dict[str, Any]]], ...] = (
    ("governance", governance_check),
    ("agent", agent_check),
    ("registry", registry_check),
    ("database", database_check),
    ("filesystem", filesystem_check),
)


def run_diagnostics(checks: tuple[tuple[str, Callable[[], dict[str, Any]]], ...] = DEFAULT_CHECKS) -> DiagnosticsReport:
    results: dict[str, dict[str, Any]] = {}
    events: list[dict[str, Any]] = []
    healthy = True
    for name, check in checks:
        result = check()
        results[name] = result
        if not bool(result.get("healthy", False)):
            healthy = False
            events.append({"type": "health_failure", "check": name, "detail": result})
    return DiagnosticsReport(healthy=healthy, checks=results, events=tuple(events))
