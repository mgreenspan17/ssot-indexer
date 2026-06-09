from __future__ import annotations

from dataclasses import replace

from ssot_core.models import FileInstance, FileVersion, VersionChangeType, VersionClassification


def classify_version_change(old_record: FileInstance, new_record: FileInstance) -> VersionClassification:
    """Classify version changes using hash, size, timestamps, provider and path."""
    same_hash = old_record.blake3_hash == new_record.blake3_hash
    same_size = old_record.size == new_record.size
    same_path = old_record.path == new_record.path
    same_provider = old_record.provider == new_record.provider

    if same_hash and same_size:
        if same_path and same_provider:
            return VersionClassification(
                change_type=VersionChangeType.unchanged,
                reason="Content identity unchanged at same provider/path",
                canonical_id=old_record.canonical_id,
            )
        return VersionClassification(
            change_type=VersionChangeType.same_version_new_location,
            reason="Same content identity found at a new provider/path",
            canonical_id=old_record.canonical_id,
        )

    if same_path and same_provider:
        return VersionClassification(
            change_type=VersionChangeType.new_version_same_path,
            reason="Path unchanged but content identity changed",
            canonical_id=old_record.canonical_id,
        )

    return VersionClassification(
        change_type=VersionChangeType.new_canonical_object,
        reason="Content and location changed; treat as new canonical object",
        canonical_id=None,
    )


def link_version_lineage(
    canonical_id: str,
    old_version: FileVersion,
    new_version: FileVersion,
) -> FileVersion:
    """Attach new_version as a child of old_version in the same canonical lineage."""
    if old_version.canonical_id != canonical_id:
        raise ValueError("old_version canonical_id does not match lineage canonical_id")
    if new_version.canonical_id != canonical_id:
        raise ValueError("new_version canonical_id does not match lineage canonical_id")
    return replace(new_version, parent_version_id=old_version.version_id)
