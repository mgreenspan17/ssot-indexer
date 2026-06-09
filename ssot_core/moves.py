from __future__ import annotations

from collections import defaultdict
from dataclasses import replace

from uuid import uuid7_str

from ssot_core.models import FileInstance, MoveDetectionResult, MoveEvent, MoveEventType


def detect_moves(
    previous_snapshot: list[FileInstance],
    current_snapshot: list[FileInstance],
) -> MoveDetectionResult:
    """Detect move vs copy events using hash identity and path existence transitions."""
    prev_by_hash: dict[str, list[FileInstance]] = defaultdict(list)
    curr_by_hash: dict[str, list[FileInstance]] = defaultdict(list)

    for item in previous_snapshot:
        prev_by_hash[item.blake3_hash].append(item)
    for item in current_snapshot:
        curr_by_hash[item.blake3_hash].append(item)

    move_events: list[MoveEvent] = []
    copy_events: list[MoveEvent] = []

    for blake3_hash, curr_instances in curr_by_hash.items():
        prev_instances = prev_by_hash.get(blake3_hash, [])
        if not prev_instances:
            continue

        prev_paths = {(i.provider, i.path, i.device_id): i for i in prev_instances}
        curr_paths = {(i.provider, i.path, i.device_id): i for i in curr_instances}

        disappeared = [prev_paths[key] for key in prev_paths.keys() - curr_paths.keys()]
        appeared = [curr_paths[key] for key in curr_paths.keys() - prev_paths.keys()]

        if not appeared:
            continue

        # If old path disappeared and new path appeared => move
        if disappeared:
            for old_item, new_item in zip(disappeared, appeared):
                move_events.append(
                    MoveEvent(
                        event_id=uuid7_str(),
                        canonical_id=new_item.canonical_id,
                        instance_id=new_item.instance_id,
                        event_type=MoveEventType.move,
                        blake3_hash=blake3_hash,
                        from_provider=old_item.provider,
                        from_path=old_item.path,
                        from_device_id=old_item.device_id,
                        to_provider=new_item.provider,
                        to_path=new_item.path,
                        to_device_id=new_item.device_id,
                    )
                )
            continue

        # Old path still exists and new path appears => copy
        anchor = prev_instances[0]
        for new_item in appeared:
            copy_events.append(
                MoveEvent(
                    event_id=uuid7_str(),
                    canonical_id=new_item.canonical_id,
                    instance_id=new_item.instance_id,
                    event_type=MoveEventType.copy,
                    blake3_hash=blake3_hash,
                    from_provider=anchor.provider,
                    from_path=anchor.path,
                    from_device_id=anchor.device_id,
                    to_provider=new_item.provider,
                    to_path=new_item.path,
                    to_device_id=new_item.device_id,
                )
            )

    return MoveDetectionResult(moves=tuple(move_events), copies=tuple(copy_events))


def update_paths_for_moves(
    instances: list[FileInstance],
    move_events: list[MoveEvent],
) -> list[FileInstance]:
    """Update instance paths for move events; copy events are not destructive updates."""
    by_id = {i.instance_id: i for i in instances}
    for event in move_events:
        if event.event_type != MoveEventType.move:
            continue
        if event.instance_id is None:
            continue
        existing = by_id.get(event.instance_id)
        if existing is None:
            continue
        by_id[event.instance_id] = replace(
            existing,
            provider=event.to_provider,
            path=event.to_path,
            device_id=event.to_device_id,
        )
    return list(by_id.values())


def log_move_events_for_audit(
    move_events: list[MoveEvent],
    audit_log: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Append move/copy events to an audit log structure."""
    for event in move_events:
        audit_log.append(
            {
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "blake3_hash": event.blake3_hash,
                "from": f"{event.from_provider}:{event.from_path}",
                "to": f"{event.to_provider}:{event.to_path}",
                "detected_at": event.detected_at,
            }
        )
    return audit_log
