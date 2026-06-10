# notion_ingest.py
# Use case: build auditable, dry-run Notion JSON/JSONL ingest plans for the SSOT schema.

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import json
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from hashing.provenance import (
    MerkleNodeRecord,
    blake3_hex_bytes,
    blake3_hex_json,
    blake3_hex_text,
    build_merkle_tree,
    canonical_json_dumps,
)


@dataclass(frozen=True)
class PreparedInsert:
    table: str
    row: Dict[str, Any]


@dataclass(frozen=True)
class ArtifactPlan:
    artifact_path: str
    artifact_type: str
    artifact_file_blake3: str
    byte_size: int
    line_count: int
    record_count: int
    batch_id: str
    batch_merkle_root: str
    raw_artifact: PreparedInsert
    ingest_batch: PreparedInsert
    merkle_tree: PreparedInsert
    merkle_nodes: List[PreparedInsert]
    object_snapshots: List[PreparedInsert]
    object_current: List[PreparedInsert]
    parent_edges: List[PreparedInsert]
    block_snapshots: List[PreparedInsert]
    status_events: List[PreparedInsert]


@dataclass(frozen=True)
class IngestPlan:
    tenant_id: str
    workspace_id: str
    run_id: str
    crawl_run: PreparedInsert
    artifacts: List[ArtifactPlan] = field(default_factory=list)
    crawl_run_merkle_root: str = ""

    @property
    def raw_artifacts(self) -> List[PreparedInsert]:
        return [artifact.raw_artifact for artifact in self.artifacts]

    @property
    def ingest_batches(self) -> List[PreparedInsert]:
        return [artifact.ingest_batch for artifact in self.artifacts]

    @property
    def merkle_trees(self) -> List[PreparedInsert]:
        return [artifact.merkle_tree for artifact in self.artifacts]

    @property
    def merkle_nodes(self) -> List[PreparedInsert]:
        nodes: List[PreparedInsert] = []
        for artifact in self.artifacts:
            nodes.extend(artifact.merkle_nodes)
        return nodes

    @property
    def object_snapshots(self) -> List[PreparedInsert]:
        rows: List[PreparedInsert] = []
        for artifact in self.artifacts:
            rows.extend(artifact.object_snapshots)
        return rows

    @property
    def object_current_rows(self) -> List[PreparedInsert]:
        rows: List[PreparedInsert] = []
        for artifact in self.artifacts:
            rows.extend(artifact.object_current)
        return rows

    @property
    def parent_edges(self) -> List[PreparedInsert]:
        rows: List[PreparedInsert] = []
        for artifact in self.artifacts:
            rows.extend(artifact.parent_edges)
        return rows

    @property
    def block_snapshots(self) -> List[PreparedInsert]:
        rows: List[PreparedInsert] = []
        for artifact in self.artifacts:
            rows.extend(artifact.block_snapshots)
        return rows

    @property
    def status_events(self) -> List[PreparedInsert]:
        rows: List[PreparedInsert] = []
        for artifact in self.artifacts:
            rows.extend(artifact.status_events)
        return rows


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_row_id(prefix: str, payload: Dict[str, Any]) -> str:
    return f"{prefix}-{blake3_hex_json(payload)[:24]}"


def _artifact_kind(path: Path) -> str:
    lowered = path.name.lower()
    if lowered.endswith(".jsonl"):
        return "jsonl"
    if lowered.endswith(".json"):
        return "json"
    return "binary"


def _read_artifact_bytes(path: Path) -> bytes:
    return path.read_bytes()


def _load_json_documents(path: Path) -> Tuple[List[Dict[str, Any]], int]:
    if path.suffix.lower() == ".jsonl":
        records: List[Dict[str, Any]] = []
        line_count = 0
        with path.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                if not raw_line.strip():
                    continue
                line_count += 1
                payload = json.loads(raw_line)
                if not isinstance(payload, dict):
                    raise ValueError(f"Expected JSON object in JSONL line from {path}")
                records.append(payload)
        return records, line_count

    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, list):
        if not all(isinstance(item, dict) for item in payload):
            raise ValueError(f"Expected list of JSON objects in {path}")
        return list(payload), len(payload)
    if isinstance(payload, dict):
        return [payload], 1
    raise ValueError(f"Unsupported JSON payload in {path}")


def _infer_run_id(documents: Sequence[Dict[str, Any]], fallback: str) -> str:
    for document in documents:
        run_id = document.get("run_id")
        if isinstance(run_id, str) and run_id:
            return run_id
    return fallback


def _canonical_record_payload(
    tenant_id: str,
    workspace_id: str,
    run_id: str,
    artifact_path: Path,
    document: Dict[str, Any],
    record_index: int,
) -> Dict[str, Any]:
    payload = {
        "tenant_id": tenant_id,
        "workspace_id": workspace_id,
        "run_id": run_id,
        "artifact_path": str(artifact_path),
        "record_index": record_index,
        "document": document,
    }
    return payload


def _build_object_snapshot_rows(
    tenant_id: str,
    workspace_id: str,
    run_id: str,
    artifact_id: str,
    batch_id: str,
    artifact_path: Path,
    document: Dict[str, Any],
    record_index: int,
    record_blake3: str,
) -> Tuple[List[PreparedInsert], List[PreparedInsert], List[PreparedInsert], List[PreparedInsert]]:
    object_snapshots: List[PreparedInsert] = []
    object_current_rows: List[PreparedInsert] = []
    parent_edges: List[PreparedInsert] = []
    block_snapshots: List[PreparedInsert] = []

    observed_at = document.get("timestamp") or document.get("observed_at") or _now_iso()

    if "page_id" in document:
        page_id = str(document.get("page_id"))
        object_type = str(document.get("object", "page"))
        source_version = str(document.get("updated_at") or document.get("last_edited_time") or record_index)
        raw_json_blake3 = blake3_hex_json(document)
        normalized_content_blake3 = blake3_hex_json(
            {
                "page_id": page_id,
                "title": document.get("page_title") or document.get("title"),
                "url": document.get("url"),
                "object": object_type,
            }
        )
        structure_blake3 = blake3_hex_json(
            {
                "keys": sorted(document.keys()),
                "artifact": artifact_path.name,
                "record_index": record_index,
            }
        )
        snapshot_id = _stable_row_id("snapshot", {"page_id": page_id, "source_version": source_version, "artifact": artifact_path.name, "record_index": record_index})
        snapshot_row = {
            "snapshot_id": snapshot_id,
            "tenant_id": tenant_id,
            "workspace_id": workspace_id,
            "run_id": run_id,
            "artifact_id": artifact_id,
            "batch_id": batch_id,
            "object_type": object_type,
            "object_id": page_id,
            "parent_id": document.get("parent_id"),
            "source_version": source_version,
            "record_blake3": record_blake3,
            "raw_json_blake3": raw_json_blake3,
            "normalized_content_blake3": normalized_content_blake3,
            "structure_blake3": structure_blake3,
            "observed_at": observed_at,
            "raw_payload": document,
        }
        object_snapshots.append(PreparedInsert("notion_index.object_snapshot", snapshot_row))
        object_current_rows.append(
            PreparedInsert(
                "notion_index.object_current",
                {
                    "object_id": page_id,
                    "tenant_id": tenant_id,
                    "workspace_id": workspace_id,
                    "latest_snapshot_id": snapshot_id,
                    "object_type": object_type,
                    "parent_id": document.get("parent_id"),
                    "current_version": source_version,
                    "current_hash": record_blake3,
                    "archived": bool(document.get("archived", False)),
                    "latest_seen_at": observed_at,
                    "updated_at": observed_at,
                },
            )
        )

        parent_id = document.get("parent_id")
        if isinstance(parent_id, str) and parent_id:
            parent_edges.append(
                PreparedInsert(
                    "notion_index.parent_edge",
                    {
                        "edge_id": _stable_row_id("edge", {"parent_id": parent_id, "child_id": page_id, "artifact": artifact_path.name, "record_index": record_index}),
                        "tenant_id": tenant_id,
                        "workspace_id": workspace_id,
                        "run_id": run_id,
                        "parent_id": parent_id,
                        "child_id": page_id,
                        "parent_type": document.get("parent_type"),
                        "child_type": object_type,
                        "edge_type": "contains",
                        "effective_at": observed_at,
                        "record_blake3": record_blake3,
                    },
                )
            )

    blocks = document.get("blocks")
    if isinstance(blocks, list) and "page_id" in document:
        page_id = str(document.get("page_id"))
        for block_index, block in enumerate(blocks):
            if not isinstance(block, dict):
                raise ValueError(f"Expected block object in {artifact_path}")
            block_id = str(block.get("id") or block.get("block_id") or f"{page_id}:{block_index}")
            block_record_blake3 = blake3_hex_json(
                {
                    "tenant_id": tenant_id,
                    "workspace_id": workspace_id,
                    "run_id": run_id,
                    "artifact_path": str(artifact_path),
                    "page_id": page_id,
                    "block": block,
                    "record_index": record_index,
                    "block_index": block_index,
                }
            )
            block_snapshot_id = _stable_row_id("block", {"page_id": page_id, "block_id": block_id, "artifact": artifact_path.name, "record_index": record_index, "block_index": block_index})
            block_snapshots.append(
                PreparedInsert(
                    "notion_index.block_snapshot",
                    {
                        "block_snapshot_id": block_snapshot_id,
                        "tenant_id": tenant_id,
                        "workspace_id": workspace_id,
                        "run_id": run_id,
                        "artifact_id": artifact_id,
                        "batch_id": batch_id,
                        "page_id": page_id,
                        "block_id": block_id,
                        "parent_block_id": block.get("parent_block_id"),
                        "block_type": str(block.get("type", "unknown")),
                        "depth": int(block.get("depth", 0)),
                        "position": int(block.get("position", block_index)),
                        "record_blake3": block_record_blake3,
                        "raw_json_blake3": blake3_hex_json(block),
                        "normalized_content_blake3": blake3_hex_json(
                            {
                                "type": block.get("type", "unknown"),
                                "text": block.get("text") or block.get("rich_text"),
                                "has_children": block.get("has_children", False),
                            }
                        ),
                        "structure_blake3": blake3_hex_json(
                            {
                                "keys": sorted(block.keys()),
                                "block_index": block_index,
                                "record_index": record_index,
                            }
                        ),
                        "observed_at": observed_at,
                        "raw_payload": block,
                    },
                )
            )
            parent_edges.append(
                PreparedInsert(
                    "notion_index.parent_edge",
                    {
                        "edge_id": _stable_row_id("edge", {"parent_id": page_id, "child_id": block_id, "artifact": artifact_path.name, "record_index": record_index, "block_index": block_index}),
                        "tenant_id": tenant_id,
                        "workspace_id": workspace_id,
                        "run_id": run_id,
                        "parent_id": page_id,
                        "child_id": block_id,
                        "parent_type": "page",
                        "child_type": "block",
                        "edge_type": "contains",
                        "effective_at": observed_at,
                        "record_blake3": block_record_blake3,
                    },
                )
            )

    return object_snapshots, object_current_rows, parent_edges, block_snapshots


def _build_artifact_plan(
    tenant_id: str,
    workspace_id: str,
    run_id: str,
    artifact_path: Path,
    artifact_index: int,
) -> ArtifactPlan:
    artifact_bytes = _read_artifact_bytes(artifact_path)
    artifact_kind = _artifact_kind(artifact_path)
    documents, line_count = _load_json_documents(artifact_path)
    inferred_run_id = _infer_run_id(documents, run_id)
    artifact_id = _stable_row_id(
        "artifact",
        {
            "tenant": tenant_id,
            "workspace": workspace_id,
            "run": inferred_run_id,
            "path": str(artifact_path),
            "index": artifact_index,
        },
    )
    batch_id = _stable_row_id(
        "batch",
        {
            "tenant": tenant_id,
            "workspace": workspace_id,
            "run": inferred_run_id,
            "artifact": artifact_path.name,
        },
    )

    record_hashes: List[str] = []
    object_snapshots: List[PreparedInsert] = []
    object_current_rows: List[PreparedInsert] = []
    parent_edges: List[PreparedInsert] = []
    block_snapshots: List[PreparedInsert] = []
    status_events: List[PreparedInsert] = []

    for record_index, document in enumerate(documents):
        canonical_record = _canonical_record_payload(
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            run_id=inferred_run_id,
            artifact_path=artifact_path,
            document=document,
            record_index=record_index,
        )
        record_hash = blake3_hex_json(canonical_record)
        record_hashes.append(record_hash)

        snaps, currents, edges, blocks = _build_object_snapshot_rows(
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            run_id=inferred_run_id,
            artifact_id=artifact_id,
            batch_id=batch_id,
            artifact_path=artifact_path,
            document=document,
            record_index=record_index,
            record_blake3=record_hash,
        )
        object_snapshots.extend(snaps)
        object_current_rows.extend(currents)
        parent_edges.extend(edges)
        block_snapshots.extend(blocks)

        if "status" in document and "run_id" in document:
            status_events.append(
                PreparedInsert(
                    "notion_index.status_event",
                    {
                        "status_event_id": _stable_row_id("status", {"artifact": artifact_path.name, "record_index": record_index, "run_id": inferred_run_id}),
                        "tenant_id": tenant_id,
                        "workspace_id": workspace_id,
                        "run_id": inferred_run_id,
                        "event_type": str(document.get("stage") or document.get("status") or "status"),
                        "severity": str(document.get("severity") or "info"),
                        "message": str(document.get("stage_detail") or document.get("status") or document.get("message") or "Notion run status"),
                        "payload_json": document,
                        "status_hash": blake3_hex_json(document),
                        "observed_at": document.get("updated_at") or document.get("observed_at") or _now_iso(),
                    },
                )
            )

    merkle_tree = build_merkle_tree(record_hashes)
    batch_row = {
        "batch_id": batch_id,
        "run_id": inferred_run_id,
        "tenant_id": tenant_id,
        "workspace_id": workspace_id,
        "artifact_id": artifact_id,
        "batch_seq": artifact_index,
        "validation_status": "dry-run" if artifact_kind else "unknown",
        "record_count": len(record_hashes),
        "ingest_batch_merkle_root": merkle_tree.root_hash,
        "verified_at": None,
        "created_at": _now_iso(),
    }
    raw_artifact_row = {
        "artifact_id": artifact_id,
        "run_id": inferred_run_id,
        "tenant_id": tenant_id,
        "workspace_id": workspace_id,
        "artifact_type": artifact_kind,
        "source_path": str(artifact_path),
        "storage_path": None,
        "artifact_file_blake3": blake3_hex_bytes(artifact_bytes),
        "byte_size": len(artifact_bytes),
        "line_count": line_count,
        "record_count": len(record_hashes),
        "mime_type": "application/jsonl" if artifact_kind == "jsonl" else "application/json" if artifact_kind == "json" else None,
        "created_at": _now_iso(),
    }
    tree_row = {
        "tree_id": _stable_row_id("tree", {"batch": batch_id, "artifact": artifact_path.name}),
        "run_id": inferred_run_id,
        "batch_id": batch_id,
        "tenant_id": tenant_id,
        "workspace_id": workspace_id,
        "tree_type": "ingest_batch",
        "algorithm": "blake3",
        "leaf_count": len(record_hashes),
        "root_hash": merkle_tree.root_hash,
        "computed_at": _now_iso(),
    }
    merkle_node_rows = [
        PreparedInsert(
            "notion_index.merkle_node",
            {
                "node_id": _stable_row_id("node", {"tree": tree_row["tree_id"], "level": node.level, "position": node.position, "kind": node.node_kind}),
                "tree_id": tree_row["tree_id"],
                "level": node.level,
                "position": node.position,
                "node_kind": node.node_kind,
                "node_hash": node.node_hash,
                "left_hash": node.left_hash,
                "right_hash": node.right_hash,
                "record_blake3": node.record_blake3,
                "created_at": _now_iso(),
            },
        )
        for node in merkle_tree.nodes
    ]
    crawl_run = PreparedInsert(
        "notion_index.crawl_run",
        {
            "run_id": inferred_run_id,
            "tenant_id": tenant_id,
            "workspace_id": workspace_id,
            "status": "dry-run",
            "scheduler_name": "notion-shared-scheduler",
            "bounds_json": {
                "search_page_size": 100,
                "max_page_count": len(documents),
            },
            "pages_discovered": sum(1 for document in documents if "page_id" in document),
            "pages_indexed": sum(1 for document in documents if document.get("page_id") and not document.get("blocks")),
            "blocks_indexed": sum(len(document.get("blocks", [])) for document in documents if isinstance(document.get("blocks"), list)),
            "api_calls": 0,
            "crawl_run_merkle_root": None,
            "started_at": _now_iso(),
            "finished_at": None,
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
        },
    )

    return ArtifactPlan(
        artifact_path=str(artifact_path),
        artifact_type=artifact_kind,
        artifact_file_blake3=raw_artifact_row["artifact_file_blake3"],
        byte_size=raw_artifact_row["byte_size"],
        line_count=line_count,
        record_count=len(record_hashes),
        batch_id=batch_id,
        batch_merkle_root=merkle_tree.root_hash,
        raw_artifact=PreparedInsert("notion_index.raw_artifact", raw_artifact_row),
        ingest_batch=PreparedInsert("notion_index.ingest_batch", batch_row),
        merkle_tree=PreparedInsert("notion_index.merkle_tree", tree_row),
        merkle_nodes=merkle_node_rows,
        object_snapshots=object_snapshots,
        object_current=object_current_rows,
        parent_edges=parent_edges,
        block_snapshots=block_snapshots,
        status_events=status_events,
    )


def build_ingest_plan(
    artifact_paths: Sequence[str],
    tenant_id: str = "default-tenant",
    workspace_id: str = "default-workspace",
    run_id: Optional[str] = None,
) -> IngestPlan:
    normalized_paths = [Path(path) for path in artifact_paths]
    if not normalized_paths:
        raise ValueError("At least one artifact path is required")

    missing = [str(path) for path in normalized_paths if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Missing artifact paths: " + ", ".join(missing)
        )

    inferred_run_id = run_id or ""
    if not inferred_run_id:
        for path in normalized_paths:
            if path.suffix.lower() in {".json", ".jsonl"}:
                documents, _ = _load_json_documents(path)
                inferred_run_id = _infer_run_id(documents, inferred_run_id)
                if inferred_run_id:
                    break
    if not inferred_run_id:
        inferred_run_id = _stable_row_id("run", {"tenant": tenant_id, "workspace": workspace_id, "artifacts": [str(path) for path in normalized_paths]})

    artifacts: List[ArtifactPlan] = []
    for index, path in enumerate(normalized_paths, start=1):
        artifacts.append(_build_artifact_plan(tenant_id, workspace_id, inferred_run_id, path, index))

    crawl_run_root = build_merkle_tree([artifact.batch_merkle_root for artifact in artifacts]).root_hash
    crawl_run_row = dict(artifacts[0].ingest_batch.row)
    crawl_run_row = {
        "run_id": inferred_run_id,
        "tenant_id": tenant_id,
        "workspace_id": workspace_id,
        "status": "dry-run",
        "scheduler_name": "notion-shared-scheduler",
        "bounds_json": {
            "artifact_count": len(artifacts),
            "search_page_size": 100,
        },
        "pages_discovered": sum(artifact.ingest_batch.row["record_count"] for artifact in artifacts),
        "pages_indexed": sum(len(artifact.object_current) for artifact in artifacts),
        "blocks_indexed": sum(len(artifact.block_snapshots) for artifact in artifacts),
        "api_calls": 0,
        "crawl_run_merkle_root": crawl_run_root,
        "started_at": _now_iso(),
        "finished_at": None,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    }

    return IngestPlan(
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        run_id=inferred_run_id,
        crawl_run=PreparedInsert("notion_index.crawl_run", crawl_run_row),
        artifacts=artifacts,
        crawl_run_merkle_root=crawl_run_root,
    )


def format_dry_run_summary(plan: IngestPlan) -> str:
    lines = [
        "Notion ingest dry-run summary",
        f"tenant_id: {plan.tenant_id}",
        f"workspace_id: {plan.workspace_id}",
        f"run_id: {plan.run_id}",
        f"crawl_run_merkle_root: {plan.crawl_run_merkle_root}",
        f"artifacts: {len(plan.artifacts)}",
        f"raw_artifacts: {len(plan.raw_artifacts)}",
        f"ingest_batches: {len(plan.ingest_batches)}",
        f"object_snapshots: {len(plan.object_snapshots)}",
        f"object_current_rows: {len(plan.object_current_rows)}",
        f"parent_edges: {len(plan.parent_edges)}",
        f"block_snapshots: {len(plan.block_snapshots)}",
        f"status_events: {len(plan.status_events)}",
        f"merkle_nodes: {len(plan.merkle_nodes)}",
    ]
    for artifact in plan.artifacts:
        lines.append(
            f"artifact: {artifact.artifact_path} | type={artifact.artifact_type} | records={artifact.record_count} | root={artifact.batch_merkle_root}"
        )
    return "\n".join(lines)
