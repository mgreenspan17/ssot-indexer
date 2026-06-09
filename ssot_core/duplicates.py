from __future__ import annotations

from collections import defaultdict
from dataclasses import replace

from ssot_core.models import CanonicalFile, DuplicateGroup, FileInstance


def find_duplicates_for_hash(
    blake3_hash: str,
    instances: list[FileInstance],
    *,
    size: int | None = None,
    mime_type: str | None = None,
) -> list[FileInstance]:
    """Return instances matching the hash and optional size/mime constraints."""
    matches = [i for i in instances if i.blake3_hash == blake3_hash and i.deleted_at is None]
    if size is not None:
        matches = [i for i in matches if i.size == size]
    if mime_type is not None:
        matches = [i for i in matches if i.mime_type == mime_type]
    return matches


def unify_duplicates_into_canonical(
    canonical_id: str,
    instances: list[FileInstance],
) -> tuple[CanonicalFile, list[FileInstance]]:
    """Attach duplicate instances to a canonical object without altering content identity."""
    if not instances:
        raise ValueError("instances cannot be empty")

    first = instances[0]
    canonical = CanonicalFile(
        canonical_id=canonical_id,
        blake3_hash=first.blake3_hash,
        size=first.size,
        mime_type=first.mime_type,
        latest_version_id=first.version_id,
    )

    normalized = [replace(i, canonical_id=canonical_id) for i in instances]
    return canonical, normalized


def report_duplicate_groups(instances: list[FileInstance]) -> list[DuplicateGroup]:
    """Build duplicate groups keyed by (hash, size, mime_type)."""
    groups: dict[tuple[str, int, str], list[FileInstance]] = defaultdict(list)
    for instance in instances:
        if instance.deleted_at is not None:
            continue
        key = (instance.blake3_hash, instance.size, instance.mime_type)
        groups[key].append(instance)

    duplicate_groups: list[DuplicateGroup] = []
    for (blake3_hash, size, mime_type), grouped_instances in groups.items():
        if len(grouped_instances) <= 1:
            continue
        canonical_candidates = {i.canonical_id for i in grouped_instances if i.canonical_id}
        canonical_id = next(iter(canonical_candidates), None)
        duplicate_groups.append(
            DuplicateGroup.from_instances(
                blake3_hash=blake3_hash,
                size=size,
                mime_type=mime_type,
                instances=grouped_instances,
                canonical_id=canonical_id,
            )
        )

    duplicate_groups.sort(key=lambda g: len(g.instance_ids), reverse=True)
    return duplicate_groups
