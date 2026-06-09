from __future__ import annotations

from uuid import uuid7_str

from ssot_core.duplicates import (
    find_duplicates_for_hash,
    report_duplicate_groups,
    unify_duplicates_into_canonical,
)
from ssot_core.models import FileInstance


def _instance(provider: str, path: str, source_id: str, h: str = "hash1") -> FileInstance:
    return FileInstance.create(
        source_id=source_id,
        provider=provider,
        path=path,
        blake3_hash=h,
        size=100,
        mime_type="application/pdf",
        modified_at="2026-01-01T00:00:00+00:00",
    )


def test_find_duplicates_for_hash_across_providers():
    instances = [
        _instance("server", "/docs/a.pdf", "s1"),
        _instance("gdrive", "/drive/a.pdf", "g1"),
        _instance("dropbox", "/drop/a.pdf", "d1"),
        _instance("onedrive", "/one/a.pdf", "o1", h="hash2"),
    ]
    matches = find_duplicates_for_hash("hash1", instances, size=100, mime_type="application/pdf")
    assert len(matches) == 3


def test_unify_duplicates_into_canonical_sets_same_canonical_id():
    instances = [
        _instance("server", "/docs/a.pdf", "s1"),
        _instance("gdrive", "/drive/a.pdf", "g1"),
    ]
    canonical_id = uuid7_str()
    canonical, unified = unify_duplicates_into_canonical(canonical_id, instances)
    assert canonical.canonical_id == canonical_id
    assert {item.canonical_id for item in unified} == {canonical_id}


def test_report_duplicate_groups_builds_cluster_rows():
    instances = [
        _instance("server", "/docs/a.pdf", "s1", h="h1"),
        _instance("gdrive", "/drive/a.pdf", "g1", h="h1"),
        _instance("dropbox", "/drop/a.pdf", "d1", h="h1"),
        _instance("server", "/docs/b.pdf", "s2", h="h2"),
    ]
    groups = report_duplicate_groups(instances)
    assert len(groups) == 1
    assert len(groups[0].instance_ids) == 3
