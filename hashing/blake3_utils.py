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


@dataclass(frozen=True)
class DualHashResult:
    blake3_digest: str
    sha256_digest: str
    algorithm: str
    size: int


def dual_hash_file(path: str | Path) -> DualHashResult:
    """Read a file once and compute both BLAKE3 and SHA-256 simultaneously."""
    import hashlib

    file_path = Path(path)
    b3_hasher = blake3()
    sha_hasher = hashlib.sha256()
    size = 0
    with file_path.open("rb") as handle:
        while True:
            chunk = handle.read(CHUNK_SIZE)
            if not chunk:
                break
            size += len(chunk)
            b3_hasher.update(chunk)
            sha_hasher.update(chunk)
    return DualHashResult(
        blake3_digest=b3_hasher.hexdigest(),
        sha256_digest=sha_hasher.hexdigest(),
        algorithm="blake3+sha256",
        size=size,
    )