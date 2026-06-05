from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256


@dataclass(frozen=True)
class EmbeddingVector:
    identifier: str
    vector: list[float]


def embed_text(text: str) -> EmbeddingVector:
    digest = sha256(text.encode("utf-8")).digest()
    vector = [round(byte / 255.0, 6) for byte in digest[:16]]
    return EmbeddingVector(identifier=sha256(text.encode("utf-8")).hexdigest(), vector=vector)
