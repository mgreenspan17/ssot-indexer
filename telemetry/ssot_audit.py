from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class AuditRecord:
    actor: str
    action: str
    target: str
    timestamp: str = datetime.now(timezone.utc).isoformat()


def audit_payload(actor: str, action: str, target: str) -> dict[str, Any]:
    return asdict(AuditRecord(actor=actor, action=action, target=target))
