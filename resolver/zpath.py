from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ZPathResolution:
    uuid7: str
    canonical_path: str


def resolve_z_path(z_path: str, lookup: dict[str, str]) -> ZPathResolution:
    if not z_path.startswith("z://"):
        raise ValueError("z path must start with z://")
    uuid7_value = z_path.removeprefix("z://").strip()
    if not uuid7_value:
        raise ValueError("z path missing uuid7 value")
    if uuid7_value not in lookup:
        raise KeyError(f"unknown uuid7: {uuid7_value}")
    return ZPathResolution(uuid7=uuid7_value, canonical_path=str(Path(lookup[uuid7_value]).resolve()))