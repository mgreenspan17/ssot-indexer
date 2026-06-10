# provenance.py
# Use case: deterministic Notion ingest hashing, canonical JSON serialization, and Merkle roots.

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import json
from typing import Any, List, Optional, Sequence

from hashing.blake3_utils import create_blake3_hasher


def _json_default(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="surrogateescape")
    if hasattr(value, "model_dump"):
        return value.model_dump()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def canonical_json_dumps(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=_json_default,
    )


def blake3_hex_bytes(data: bytes) -> str:
    hasher = create_blake3_hasher()
    hasher.update(data)
    return hasher.hexdigest()


def blake3_hex_text(text: str) -> str:
    return blake3_hex_bytes(text.encode("utf-8"))


def blake3_hex_json(value: Any) -> str:
    return blake3_hex_text(canonical_json_dumps(value))


def _decode_hex_or_text(value: str) -> bytes:
    try:
        return bytes.fromhex(value)
    except ValueError:
        return value.encode("utf-8")


def _domain_hash(domain: str, payload: bytes) -> str:
    return blake3_hex_bytes(domain.encode("utf-8") + b"|" + payload)


def merkle_leaf_hash(record_hash: str) -> str:
    return _domain_hash("notion-index:leaf", _decode_hex_or_text(record_hash))


def merkle_node_hash(left_hash: str, right_hash: str) -> str:
    payload = _decode_hex_or_text(left_hash) + _decode_hex_or_text(right_hash)
    return _domain_hash("notion-index:node", payload)


def merkle_root_from_hashes(record_hashes: Sequence[str]) -> str:
    tree = build_merkle_tree(record_hashes)
    return tree.root_hash


@dataclass(frozen=True)
class MerkleNodeRecord:
    level: int
    position: int
    node_kind: str
    node_hash: str
    left_hash: Optional[str]
    right_hash: Optional[str]
    record_blake3: Optional[str]


@dataclass(frozen=True)
class MerkleTreeResult:
    root_hash: str
    nodes: List[MerkleNodeRecord]


def build_merkle_tree(record_hashes: Sequence[str]) -> MerkleTreeResult:
    if not record_hashes:
        empty_root = _domain_hash("notion-index:empty", b"")
        return MerkleTreeResult(root_hash=empty_root, nodes=[])

    nodes: List[MerkleNodeRecord] = []
    current_level = [merkle_leaf_hash(record_hash) for record_hash in record_hashes]

    for position, (record_hash, leaf_hash) in enumerate(zip(record_hashes, current_level)):
        nodes.append(
            MerkleNodeRecord(
                level=0,
                position=position,
                node_kind="leaf",
                node_hash=leaf_hash,
                left_hash=None,
                right_hash=None,
                record_blake3=record_hash,
            )
        )

    level = 1
    while len(current_level) > 1:
        next_level: List[str] = []
        pair_position = 0
        index = 0
        while index < len(current_level):
            left_hash = current_level[index]
            if index + 1 < len(current_level):
                right_hash = current_level[index + 1]
            else:
                right_hash = left_hash
            node_hash = merkle_node_hash(left_hash, right_hash)
            nodes.append(
                MerkleNodeRecord(
                    level=level,
                    position=pair_position,
                    node_kind="node",
                    node_hash=node_hash,
                    left_hash=left_hash,
                    right_hash=right_hash,
                    record_blake3=None,
                )
            )
            next_level.append(node_hash)
            pair_position += 1
            index += 2
        current_level = next_level
        level += 1

    return MerkleTreeResult(root_hash=current_level[0], nodes=nodes)


def merkle_root_from_values(values: Sequence[Any]) -> str:
    return merkle_root_from_hashes([blake3_hex_json(value) for value in values])
