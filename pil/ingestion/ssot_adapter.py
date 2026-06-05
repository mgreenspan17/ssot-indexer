from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import inspect
from typing import Any

from consolidation.ssot_repo_sync import sync_repositories
from pil.graph.ssot_edges import RelationshipEdge, to_edge_payload
from pil.graph.ssot_embeddings import embed_text
from pil.graph.ssot_nodes import FileNode, to_node_payload


REQUIRED_RECORD_KEYS = {"uuid7", "path", "blake3", "category", "mime_type"}
_LAST_INGESTION_TIMESTAMP: str | None = None


@dataclass(frozen=True)
class SSOTAdapterResult:
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    embeddings: list[dict[str, Any]]
    consolidation: dict[str, Any]
    errors: list[dict[str, str]]


class ManifestValidationError(ValueError):
    pass


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def last_ingestion_timestamp() -> str | None:
    return _LAST_INGESTION_TIMESTAMP


def validate_manifest_schema(manifest: dict[str, Any]) -> None:
    if not isinstance(manifest, dict):
        raise ManifestValidationError("manifest must be an object")
    records = manifest.get("records")
    if not isinstance(records, list):
        raise ManifestValidationError("manifest.records must be a list")


async def _maybe_await(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await value
    return value


def _normalize_records(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    records = manifest.get("records", [])
    normalized = [dict(record) for record in records if isinstance(record, dict)]
    return sorted(normalized, key=lambda item: (str(item.get("uuid7", "")), str(item.get("path", ""))))


async def ingest_manifest_async(
    manifest: dict[str, Any],
    canonicalize_hook: Any | None = None,
    isolate_errors: bool = True,
) -> SSOTAdapterResult:
    global _LAST_INGESTION_TIMESTAMP

    validate_manifest_schema(manifest)
    records = _normalize_records(manifest)

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    embeddings: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    seen_fingerprints: set[tuple[str, str]] = set()
    for record in records:
        try:
            missing = sorted(REQUIRED_RECORD_KEYS - set(record.keys()))
            if missing:
                raise ManifestValidationError(f"record missing keys: {', '.join(missing)}")

            fingerprint = (str(record["uuid7"]), str(record["blake3"]))
            if fingerprint in seen_fingerprints:
                continue
            seen_fingerprints.add(fingerprint)

            node = FileNode(
                uuid7=str(record["uuid7"]),
                path=str(record["path"]),
                canonical_path=str(record.get("canonical_path", "")),
                hash=str(record["blake3"]),
                category=str(record["category"]),
                mime_type=str(record["mime_type"]),
            )
            edge = RelationshipEdge(source=node.uuid7, target=node.hash, edge_type="HAS_HASH")
            embedding = embed_text(node.path)

            nodes.append(to_node_payload(node))
            edges.append(to_edge_payload(edge))
            embeddings.append(embedding.__dict__)

            if canonicalize_hook is not None:
                await _maybe_await(canonicalize_hook(record))
        except Exception as exc:
            if isolate_errors:
                errors.append({"record": str(record.get("uuid7", "unknown")), "error": str(exc)})
                continue
            raise

    consolidation = sync_repositories()
    _LAST_INGESTION_TIMESTAMP = _utc_now()
    return SSOTAdapterResult(
        nodes=nodes,
        edges=edges,
        embeddings=embeddings,
        consolidation={
            "repositories": consolidation.repositories,
            "rules": consolidation.rules,
        },
        errors=errors,
    )


def adapt_manifest(manifest: dict[str, Any]) -> SSOTAdapterResult:
    validate_manifest_schema(manifest)
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    embeddings: list[dict[str, Any]] = []
    for record in _normalize_records(manifest):
        if not REQUIRED_RECORD_KEYS.issubset(record):
            continue
        node = FileNode(
            uuid7=str(record["uuid7"]),
            path=str(record["path"]),
            canonical_path=str(record.get("canonical_path", "")),
            hash=str(record["blake3"]),
            category=str(record["category"]),
            mime_type=str(record["mime_type"]),
        )
        nodes.append(to_node_payload(node))
        edges.append(to_edge_payload(RelationshipEdge(source=node.uuid7, target=node.hash, edge_type="HAS_HASH")))
        embeddings.append(embed_text(node.path).__dict__)

    consolidation = sync_repositories()
    return SSOTAdapterResult(
        nodes=nodes,
        edges=edges,
        embeddings=embeddings,
        consolidation={
            "repositories": consolidation.repositories,
            "rules": consolidation.rules,
        },
        errors=[],
    )


async def dry_run_ingestion_cycle(manifest: dict[str, Any]) -> dict[str, Any]:
    result = await ingest_manifest_async(manifest, canonicalize_hook=None, isolate_errors=True)
    return {
        "module_loaded": True,
        "graph_integration": bool(result.nodes and result.edges and result.embeddings),
        "consolidation_integration": bool(result.consolidation.get("repositories") is not None),
        "processed_records": len(result.nodes),
        "errors": result.errors,
        "last_ingestion_timestamp": last_ingestion_timestamp(),
    }


def ingestion_status() -> dict[str, Any]:
    return {
        "module_loaded": True,
        "graph_integration": True,
        "consolidation_integration": True,
        "last_ingestion_timestamp": last_ingestion_timestamp(),
    }
