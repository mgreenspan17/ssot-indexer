from __future__ import annotations

from ssot_core.models import DuplicateGroup, FileVersion, ProviderSyncState


def summarize_hashing_performance(total_bytes: int, total_files: int, elapsed_seconds: float) -> dict[str, float]:
    """Return basic throughput metrics for dashboard widgets."""
    if elapsed_seconds <= 0:
        return {
            "elapsed_seconds": 0.0,
            "bytes_per_second": 0.0,
            "files_per_second": 0.0,
            "mb_per_second": 0.0,
        }
    bytes_per_second = total_bytes / elapsed_seconds
    return {
        "elapsed_seconds": round(elapsed_seconds, 3),
        "bytes_per_second": round(bytes_per_second, 2),
        "files_per_second": round(total_files / elapsed_seconds, 2),
        "mb_per_second": round(bytes_per_second / (1024 * 1024), 3),
    }


def build_duplicate_report(groups: list[DuplicateGroup]) -> str:
    """Generate a human-readable summary of duplicate clusters."""
    if not groups:
        return "No duplicate groups detected."

    lines = ["Duplicate Groups", "================"]
    for i, group in enumerate(groups, start=1):
        lines.append(
            f"{i}. hash={group.blake3_hash} size={group.size} mime={group.mime_type} "
            f"instances={len(group.instance_ids)} providers={sorted(set(group.providers))}"
        )
    return "\n".join(lines)


def build_version_history_view(canonical_id: str, versions: list[FileVersion]) -> dict[str, object]:
    """Return a lineage payload suitable for CLI/API rendering."""
    lineage = [
        {
            "version_id": version.version_id,
            "parent_version_id": version.parent_version_id,
            "created_at": version.created_at,
            "provider": version.provider,
            "path": version.path,
            "blake3_hash": version.blake3_hash,
            "size": version.size,
        }
        for version in sorted(versions, key=lambda v: v.created_at)
        if version.canonical_id == canonical_id
    ]
    return {
        "canonical_id": canonical_id,
        "version_count": len(lineage),
        "lineage": lineage,
    }


def build_provider_sync_status_dashboard(states: list[ProviderSyncState]) -> dict[str, object]:
    """Build a provider status summary structure for API/CLI dashboarding."""
    providers = [
        {
            "provider_id": state.provider_id,
            "strategy": state.strategy.value,
            "cursor": state.cursor,
            "last_sync_at": state.last_sync_at,
            "last_error": state.last_error,
            "retries": state.retries,
            "healthy": state.last_error is None,
        }
        for state in sorted(states, key=lambda s: s.provider_id)
    ]
    return {
        "provider_count": len(providers),
        "healthy_count": sum(1 for p in providers if p["healthy"]),
        "providers": providers,
    }
