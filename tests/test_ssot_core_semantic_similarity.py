from __future__ import annotations

from ssot_core.models import SemanticFingerprint
from ssot_core.semantic_similarity import (
    ByteHistogramEmbeddingModel,
    SemanticSimilarityService,
    cluster_new_file,
    compute_ahash,
    compute_dhash,
    compute_phash,
    cosine_similarity,
    find_semantically_similar_files,
    rebuild_semantic_clusters,
)


def _image(seed: int, h: int = 16, w: int = 16) -> list[list[int]]:
    return [[(seed + (x * 7) + (y * 13)) % 256 for x in range(w)] for y in range(h)]


def _fingerprint(file_id: str, canonical_id: str, payload: bytes, image: list[list[int]]) -> SemanticFingerprint:
    model = ByteHistogramEmbeddingModel(bins=32)
    return SemanticFingerprint(
        file_id=file_id,
        canonical_file_id=canonical_id,
        version_id=None,
        blake3_hash=f"hash-{file_id}",
        size=len(payload),
        mime_type="image/png",
        a_hash=compute_ahash(image),
        d_hash=compute_dhash(image),
        p_hash=compute_phash(image),
        embedding=model.encode(payload, "image/png"),
    )


def test_perceptual_hashes_and_cosine_similarity():
    img1 = _image(10)
    img2 = _image(11)
    h1 = compute_ahash(img1)
    h2 = compute_ahash(img2)
    assert len(h1) == len(h2) == 16

    emb = ByteHistogramEmbeddingModel(bins=32)
    v1 = emb.encode(b"aaaabbbbcccc")
    v2 = emb.encode(b"aaaabbbbccccddd")
    score = cosine_similarity(v1, v2)
    assert 0.0 <= score <= 1.0


def test_find_semantically_similar_files_and_cluster_new_file():
    base = _fingerprint("f1", "c1", b"frame-a", _image(20))
    similar = _fingerprint("f2", "c2", b"frame-a-variant", _image(21))
    far = _fingerprint("f3", "c3", b"zzzzzzzzzz", _image(200))

    fingerprints = [base, similar, far]
    matches = find_semantically_similar_files("f1", fingerprints, threshold=0.40)
    assert any(match.canonical_file_id == "c2" for match in matches)

    clusters, new_cluster = cluster_new_file("f1", fingerprints, [], threshold=0.40)
    assert new_cluster is not None
    assert len(clusters) == 1
    assert set(new_cluster.canonical_file_ids) == {"c1", "c2"}


def test_rebuild_semantic_clusters_groups_related_canonicals():
    fingerprints = [
        _fingerprint("f1", "c1", b"group-a", _image(30)),
        _fingerprint("f2", "c2", b"group-a-2", _image(31)),
        _fingerprint("f3", "c3", b"group-b", _image(190)),
    ]

    clusters = rebuild_semantic_clusters(fingerprints, threshold=0.40)
    assert clusters
    assert any({"c1", "c2"}.issubset(set(cluster.canonical_file_ids)) for cluster in clusters)


def test_semantic_similarity_service_lifecycle():
    service = SemanticSimilarityService(threshold=0.40)
    fp1 = _fingerprint("f1", "c1", b"alpha", _image(55))
    fp2 = _fingerprint("f2", "c2", b"alpha-2", _image(56))
    service.upsert_fingerprint(fp1)
    service.upsert_fingerprint(fp2)

    matches = service.find_semantically_similar_files("f1")
    assert matches
    created = service.cluster_new_file("f1")
    assert created is not None
    clusters = service.rebuild_semantic_clusters()
    assert clusters
