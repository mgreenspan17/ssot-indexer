from __future__ import annotations

from ssot_core.models import FileInstance, FileVersion, VersionChangeType
from ssot_core.versioning import classify_version_change, link_version_lineage


def _instance(path: str, blake3_hash: str, size: int, provider: str = "server") -> FileInstance:
    return FileInstance.create(
        source_id=f"{provider}:{path}",
        provider=provider,
        path=path,
        blake3_hash=blake3_hash,
        size=size,
        mime_type="text/plain",
        modified_at="2026-01-01T00:00:00+00:00",
        canonical_id="canon-1",
        version_id="ver-1",
    )


def test_classify_version_change_same_hash_new_path():
    old = _instance("/docs/a.txt", "hash1", 100)
    new = _instance("/archive/a.txt", "hash1", 100)
    result = classify_version_change(old, new)
    assert result.change_type == VersionChangeType.same_version_new_location


def test_classify_version_change_different_hash_same_path():
    old = _instance("/docs/a.txt", "hash1", 100)
    new = _instance("/docs/a.txt", "hash2", 120)
    result = classify_version_change(old, new)
    assert result.change_type == VersionChangeType.new_version_same_path


def test_classify_version_change_different_hash_and_path():
    old = _instance("/docs/a.txt", "hash1", 100)
    new = _instance("/new/b.txt", "hash3", 250, provider="gdrive")
    result = classify_version_change(old, new)
    assert result.change_type == VersionChangeType.new_canonical_object


def test_link_version_lineage_sets_parent():
    old = FileVersion.create(
        canonical_id="canon-1",
        blake3_hash="h1",
        size=100,
        provider="server",
        path="/docs/a.txt",
    )
    new = FileVersion.create(
        canonical_id="canon-1",
        blake3_hash="h2",
        size=120,
        provider="server",
        path="/docs/a.txt",
    )
    linked = link_version_lineage("canon-1", old, new)
    assert linked.parent_version_id == old.version_id
