from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import random


UUID7_EPOCH_BITS = 48
UUID7_VERSION = 0x7


@dataclass(frozen=True)
class UUID7Value:
    value: str

    @property
    def text(self) -> str:
        return self.value


def _milliseconds_since_epoch(moment: datetime | None = None) -> int:
    current = moment or datetime.now(timezone.utc)
    return int(current.timestamp() * 1000)


def uuid7(moment: datetime | None = None) -> UUID7Value:
    timestamp_ms = _milliseconds_since_epoch(moment) & ((1 << UUID7_EPOCH_BITS) - 1)
    rand_a = random.getrandbits(12)
    rand_b = random.getrandbits(62)
    high = (timestamp_ms << 16) | (UUID7_VERSION << 12) | rand_a
    low = rand_b
    value_int = (high << 64) | low
    value_hex = f"{value_int:032x}"
    formatted = (
        f"{value_hex[0:8]}-{value_hex[8:12]}-{value_hex[12:16]}-{value_hex[16:20]}-{value_hex[20:32]}"
    )
    return UUID7Value(formatted)


def uuid7_str(moment: datetime | None = None) -> str:
    return uuid7(moment).text