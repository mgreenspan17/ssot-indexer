"""Governance validator for SSOT OS.

Assumptions:
- Governance documents are plain markdown containing the canonical lane and safety sections.

Boundaries:
- This module validates structure only; it does not authorize execution.

Integration notes:
- Validation should run before any enforcement or routing decision.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .governance_loader import GovernanceDocument

REQUIRED_SECTIONS = (
    "Lane Definitions",
    "Safety and Isolation Rules",
    "Phase Execution Rules",
    "Deadlock Prevention",
    "Agent Self-Diagnostic Rules",
    "Autonomy Scoring Model",
    "Agent-to-Agent Contracts",
    "Future-Agent Onboarding Rules",
    "Canonical Storage and Mirror Model",
)


@dataclass(frozen=True)
class GovernanceValidationResult:
    valid: bool
    missing_sections: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()


def _find_missing_sections(text: str, required_sections: Iterable[str]) -> tuple[str, ...]:
    missing: list[str] = []
    for section in required_sections:
        if section not in text:
            missing.append(section)
    return tuple(missing)


def validate_governance_document(document: GovernanceDocument) -> GovernanceValidationResult:
    missing = _find_missing_sections(document.text, REQUIRED_SECTIONS)
    if missing:
        return GovernanceValidationResult(
            valid=False,
            missing_sections=missing,
            notes=("Governance document is missing required sections.",),
        )
    return GovernanceValidationResult(valid=True, notes=("Governance document contains required sections.",))
