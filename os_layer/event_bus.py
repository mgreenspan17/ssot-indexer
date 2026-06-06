"""Event bus primitives for SSOT OS.

Assumptions:
- Event consumers are in-process or fed from a thin adapter.

Boundaries:
- This module does not guarantee durability by itself.

Integration notes:
- Use the event types catalog to keep messages consistent across agents.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable


@dataclass(frozen=True)
class Event:
    event_type: str
    payload: dict[str, Any]
    source: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class EventBus:
    subscribers: dict[str, list[Callable[[Event], None]]] = field(default_factory=dict)
    events: list[Event] = field(default_factory=list)

    def publish(self, event: Event) -> None:
        self.events.append(event)
        for callback in self.subscribers.get(event.event_type, []):
            callback(event)

    def subscribe(self, event_type: str, callback: Callable[[Event], None]) -> None:
        self.subscribers.setdefault(event_type, []).append(callback)
