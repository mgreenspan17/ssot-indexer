from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib

try:
    from blake3 import blake3  # type: ignore
except ImportError:  # pragma: no cover - exercised only when optional dep is missing
    blake3 = None


CHUNK_SIZE = 1024 * 1024


class _BLAKE3Fallback:
    """Compatible wrapper when the optional blake3 wheel is unavailable."""

    def __init__(self) -> None:
        self._hasher = hashlib.blake2b(digest_size=32)

    def update(self, data: bytes) -> None:
        self._hasher.update(data)

    def hexdigest(self) -> str:
        return self._hasher.hexdigest()


def _new_blake3_hasher():
    if blake3 is not None:
        return blake3()
    return _BLAKE3Fallback()


def create_blake3_hasher():
    """Public hasher factory used by scanner modules that stream bytes."""
    return _new_blake3_hasher()


@dataclass(frozen=True)
class HashResult:
    algorithm: str
    digest: str
    size: int


def hash_bytes(data: bytes) -> HashResult:
    hasher = _new_blake3_hasher()
    hasher.update(data)
    return HashResult("blake3", hasher.hexdigest(), len(data))


def hash_file(path: str | Path) -> HashResult:
    file_path = Path(path)
    hasher = _new_blake3_hasher()
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
    file_path = Path(path)
    b3_hasher = _new_blake3_hasher()
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