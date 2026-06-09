from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Protocol

from ssot_core.models import SemanticCluster, SemanticFingerprint


class EmbeddingModel(Protocol):
    def encode(self, payload: bytes, mime_type: str | None = None) -> tuple[float, ...]:
        """Return a normalized embedding vector."""


class ByteHistogramEmbeddingModel:
    """Lightweight embedding model used as a CLIP-compatible fallback interface."""

    def __init__(self, bins: int = 64) -> None:
        if bins <= 0:
            raise ValueError("bins must be positive")
        self.bins = bins

    def encode(self, payload: bytes, mime_type: str | None = None) -> tuple[float, ...]:
        if not payload:
            return tuple(0.0 for _ in range(self.bins))

        histogram = [0.0 for _ in range(self.bins)]
        for b in payload:
            index = int((b / 256.0) * self.bins)
            if index >= self.bins:
                index = self.bins - 1
            histogram[index] += 1.0

        norm = math.sqrt(sum(v * v for v in histogram))
        if norm == 0:
            return tuple(0.0 for _ in range(self.bins))
        return tuple(v / norm for v in histogram)


@dataclass(frozen=True)
class SimilarityMatch:
    file_id: str
    canonical_file_id: str
    score: float


class SemanticSimilarityService:
    """Stateful semantic clustering service for SSOT integration points."""

    def __init__(self, threshold: float = 0.80) -> None:
        self.threshold = threshold
        self.fingerprints: list[SemanticFingerprint] = []
        self.clusters: list[SemanticCluster] = []

    def upsert_fingerprint(self, fingerprint: SemanticFingerprint) -> None:
        self.fingerprints = [
            existing for existing in self.fingerprints if existing.file_id != fingerprint.file_id
        ]
        self.fingerprints.append(fingerprint)

    def find_semantically_similar_files(self, file_id: str) -> list[SimilarityMatch]:
        return find_semantically_similar_files(
            file_id,
            self.fingerprints,
            threshold=self.threshold,
        )

    def cluster_new_file(self, file_id: str) -> SemanticCluster | None:
        self.clusters, created = cluster_new_file(
            file_id,
            self.fingerprints,
            self.clusters,
            threshold=self.threshold,
        )
        return created

    def rebuild_semantic_clusters(self) -> list[SemanticCluster]:
        self.clusters = rebuild_semantic_clusters(self.fingerprints, threshold=self.threshold)
        return self.clusters


def _resize_grayscale_matrix(matrix: list[list[int]], out_h: int, out_w: int) -> list[list[float]]:
    if not matrix or not matrix[0]:
        raise ValueError("matrix must be non-empty")

    in_h = len(matrix)
    in_w = len(matrix[0])
    out: list[list[float]] = []
    for y in range(out_h):
        row: list[float] = []
        src_y = min(int((y / out_h) * in_h), in_h - 1)
        for x in range(out_w):
            src_x = min(int((x / out_w) * in_w), in_w - 1)
            row.append(float(matrix[src_y][src_x]))
        out.append(row)
    return out


def _bits_to_hex(bits: list[int]) -> str:
    out = []
    for i in range(0, len(bits), 4):
        nibble = bits[i : i + 4]
        value = 0
        for bit in nibble:
            value = (value << 1) | bit
        out.append(format(value, "x"))
    return "".join(out)


def hamming_distance(hash_a: str, hash_b: str) -> int:
    if len(hash_a) != len(hash_b):
        raise ValueError("hash lengths must match")
    bits_a = bin(int(hash_a, 16))[2:].zfill(len(hash_a) * 4)
    bits_b = bin(int(hash_b, 16))[2:].zfill(len(hash_b) * 4)
    return sum(1 for a, b in zip(bits_a, bits_b) if a != b)


def compute_ahash(grayscale_matrix: list[list[int]], size: int = 8) -> str:
    resized = _resize_grayscale_matrix(grayscale_matrix, size, size)
    mean_val = sum(sum(row) for row in resized) / (size * size)
    bits = [1 if value >= mean_val else 0 for row in resized for value in row]
    return _bits_to_hex(bits)


def compute_dhash(grayscale_matrix: list[list[int]], width: int = 9, height: int = 8) -> str:
    resized = _resize_grayscale_matrix(grayscale_matrix, height, width)
    bits: list[int] = []
    for row in resized:
        for x in range(width - 1):
            bits.append(1 if row[x] >= row[x + 1] else 0)
    return _bits_to_hex(bits)


def _dct_1d(values: list[float]) -> list[float]:
    n = len(values)
    out = [0.0 for _ in range(n)]
    factor = math.pi / (2.0 * n)
    for k in range(n):
        alpha = math.sqrt(1.0 / n) if k == 0 else math.sqrt(2.0 / n)
        total = 0.0
        for i, value in enumerate(values):
            total += value * math.cos((2 * i + 1) * k * factor)
        out[k] = alpha * total
    return out


def _dct_2d(matrix: list[list[float]]) -> list[list[float]]:
    rows = [_dct_1d(row) for row in matrix]
    transposed = list(map(list, zip(*rows)))
    cols = [_dct_1d(col) for col in transposed]
    return list(map(list, zip(*cols)))


def compute_phash(grayscale_matrix: list[list[int]], size: int = 32, low_freq: int = 8) -> str:
    resized = _resize_grayscale_matrix(grayscale_matrix, size, size)
    dct = _dct_2d(resized)
    low = [dct[y][x] for y in range(low_freq) for x in range(low_freq)]
    # Drop DC component from threshold computation.
    median_source = low[1:] if len(low) > 1 else low
    median = sorted(median_source)[len(median_source) // 2]
    bits = [1 if coeff >= median else 0 for coeff in low]
    return _bits_to_hex(bits)


def cosine_similarity(vec_a: tuple[float, ...], vec_b: tuple[float, ...]) -> float:
    if len(vec_a) != len(vec_b):
        raise ValueError("embedding dimensions must match")
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return max(-1.0, min(1.0, dot / (norm_a * norm_b)))


def _perceptual_similarity(a: SemanticFingerprint, b: SemanticFingerprint) -> float:
    h_a = hamming_distance(a.a_hash, b.a_hash)
    h_d = hamming_distance(a.d_hash, b.d_hash)
    h_p = hamming_distance(a.p_hash, b.p_hash)
    max_bits = max(len(a.a_hash), len(a.d_hash), len(a.p_hash)) * 4
    if max_bits == 0:
        return 0.0
    normalized = 1.0 - ((h_a + h_d + h_p) / (3.0 * max_bits))
    return max(0.0, min(1.0, normalized))


def _semantic_score(a: SemanticFingerprint, b: SemanticFingerprint) -> float:
    embed = cosine_similarity(a.embedding, b.embedding)
    perceptual = _perceptual_similarity(a, b)
    return (0.7 * embed) + (0.3 * perceptual)


def find_semantically_similar_files(
    file_id: str,
    fingerprints: list[SemanticFingerprint],
    *,
    threshold: float = 0.80,
    top_k: int = 20,
) -> list[SimilarityMatch]:
    target = next((f for f in fingerprints if f.file_id == file_id), None)
    if target is None:
        return []

    matches: list[SimilarityMatch] = []
    for candidate in fingerprints:
        if candidate.file_id == file_id:
            continue
        score = _semantic_score(target, candidate)
        if score >= threshold:
            matches.append(
                SimilarityMatch(
                    file_id=candidate.file_id,
                    canonical_file_id=candidate.canonical_file_id,
                    score=round(score, 6),
                )
            )

    matches.sort(key=lambda m: m.score, reverse=True)
    return matches[:top_k]


def cluster_new_file(
    file_id: str,
    fingerprints: list[SemanticFingerprint],
    existing_clusters: list[SemanticCluster],
    *,
    threshold: float = 0.80,
) -> tuple[list[SemanticCluster], SemanticCluster | None]:
    target = next((f for f in fingerprints if f.file_id == file_id), None)
    if target is None:
        return existing_clusters, None

    similar = find_semantically_similar_files(file_id, fingerprints, threshold=threshold)
    candidate_ids = {target.canonical_file_id}
    score_map: dict[str, float] = {}

    for match in similar:
        candidate_ids.add(match.canonical_file_id)
        key = "|".join(sorted([target.canonical_file_id, match.canonical_file_id]))
        score_map[key] = max(score_map.get(key, 0.0), match.score)

    if len(candidate_ids) == 1:
        # No cluster action needed.
        return existing_clusters, None

    members = sorted(candidate_ids)
    vectors = [f.embedding for f in fingerprints if f.canonical_file_id in candidate_ids]
    representative = _mean_embedding(vectors)
    new_cluster = SemanticCluster.create(members, score_map, representative)

    filtered = [
        c for c in existing_clusters if set(c.canonical_file_ids).isdisjoint(candidate_ids)
    ]
    filtered.append(new_cluster)
    return filtered, new_cluster


def rebuild_semantic_clusters(
    fingerprints: list[SemanticFingerprint],
    *,
    threshold: float = 0.80,
) -> list[SemanticCluster]:
    parent = {f.canonical_file_id: f.canonical_file_id for f in fingerprints}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        root_a = find(a)
        root_b = find(b)
        if root_a != root_b:
            parent[root_b] = root_a

    for idx, left in enumerate(fingerprints):
        for right in fingerprints[idx + 1 :]:
            score = _semantic_score(left, right)
            if score >= threshold:
                union(left.canonical_file_id, right.canonical_file_id)

    by_root: dict[str, list[str]] = {}
    for fingerprint in fingerprints:
        root = find(fingerprint.canonical_file_id)
        by_root.setdefault(root, []).append(fingerprint.canonical_file_id)

    clusters: list[SemanticCluster] = []
    for ids in by_root.values():
        unique_ids = sorted(set(ids))
        if len(unique_ids) <= 1:
            continue

        group_fingerprints = [f for f in fingerprints if f.canonical_file_id in unique_ids]
        vectors = [f.embedding for f in group_fingerprints]
        representative = _mean_embedding(vectors)

        scores: dict[str, float] = {}
        for i, left in enumerate(group_fingerprints):
            for right in group_fingerprints[i + 1 :]:
                key = "|".join(sorted([left.canonical_file_id, right.canonical_file_id]))
                scores[key] = round(_semantic_score(left, right), 6)

        clusters.append(SemanticCluster.create(unique_ids, scores, representative))

    clusters.sort(key=lambda c: len(c.canonical_file_ids), reverse=True)
    return clusters


def _mean_embedding(vectors: list[tuple[float, ...]]) -> tuple[float, ...]:
    if not vectors:
        return tuple()

    dim = len(vectors[0])
    accum = [0.0 for _ in range(dim)]
    for vector in vectors:
        if len(vector) != dim:
            raise ValueError("all embeddings in cluster must have same dimensions")
        for i, value in enumerate(vector):
            accum[i] += value

    count = float(len(vectors))
    mean = [v / count for v in accum]
    norm = math.sqrt(sum(v * v for v in mean))
    if norm == 0:
        return tuple(mean)
    return tuple(v / norm for v in mean)
