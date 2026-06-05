from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from blake3 import blake3


CHUNK_SIZE = 1024 * 1024


@dataclass(frozen=True)
class HashResult:
    algorithm: str
    digest: str
    size: int


def hash_bytes(data: bytes) -> HashResult:
    hasher = blake3()
    hasher.update(data)
    return HashResult("blake3", hasher.hexdigest(), len(data))


def hash_file(path: str | Path) -> HashResult:
    file_path = Path(path)
    hasher = blake3()
    size = 0
    with file_path.open("rb") as handle:
        while True:
            chunk = handle.read(CHUNK_SIZE)
            if not chunk:
                break
            size += len(chunk)
            hasher.update(chunk)
    return HashResult("blake3", hasher.hexdigest(), size)