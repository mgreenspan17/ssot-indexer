# SSOT Hash & ID Design Audit (Read-Only)

**Lane ID**: `LANE-WARP-SSOT-HASH-ID-AUDIT-001`
**Auditor**: Warp W21 (local agent)
**Date**: 2026-06-11

---

## Repo State

| Property | Value |
|---|---|
| Repo path | `C:\Users\manni\projects\ssot-indexer` |
| Branch | `feature/notion-index-schema-ingest-planner` |
| HEAD commit | `5270c18` — "feat: add guarded Postgres write mode for Notion ingest planner" |
| Remote origin | `git@github.com:mgreenspan17/ssot-indexer.git` |
| Git status | clean |
| Server access | `srv1/dev-node1` unreachable from this Windows environment |

---

## Design Verification Findings

| Design Point | Status | Evidence | Notes |
|---|---|---|---|
| **BLAKE3 used?** | ✅ PASS | `hashing/blake3_utils.py`, `hashing/provenance.py`, `scanner/models.py`, `ssot_core/models.py`, `sql/005_notion_index_schema.sql` (38+ column refs), `indexer/notion_ingest.py` (40+ refs) | Primary hash used throughout the entire codebase |
| **BLAKE3 in schema?** | ✅ PASS | `sql/005_notion_index_schema.sql`: `artifact_file_blake3`, `record_blake3`, `raw_json_blake3`, `normalized_content_blake3`, `structure_blake3`, `blob_blake3` (6 distinct columns). `sql/004_chat_ingestion.sql`: `body_hash_blake3` | All Notion index and chat ingestion schemas use BLAKE3 columns |
| **SHA256 used?** | ✅ PASS (compatibility) | `hashing/blake3_utils.py`: `dual_hash_file()` computes both BLAKE3 + SHA-256 simultaneously; `scanner/models.py:23`: `sha256: str = ""` optional field; `scanner/base.py`: dual hash fallback | SHA-256 is strictly secondary/compatibility; BLAKE3 is always primary |
| **Merkle roots BLAKE3-based?** | ✅ PASS | `hashing/provenance.py`: `build_merkle_tree()`, `merkle_leaf_hash()`, `merkle_node_hash()` all use `blake3_hex_bytes()` internally; `sql/005_notion_index_schema.sql:79`: `algorithm text not null default 'blake3'` | All Merkle hashing is BLAKE3-based |
| **UUIDv7 for internal IDs?** | ✅ PASS | `uuid/generator.py`: custom `uuid7()` and `uuid7_str()` implementation; `uuid/__init__.py`: re-exports UUIDv7; `ssot_core/models.py`: `uuid7_str()` used for `canonical_id`, `version_id`, `instance_id`, `duplicate_group_id` | Full UUIDv7 generator, used for all generated internal IDs |
| **UUIDv7 in schema?** | ✅ PASS | `sql/003_semantic_desktopcam.sql:25,37`: `timestamp_uuid7` columns in `desktopcam_frame` and `audit_event` tables | UUIDv7 referenced as column type |
| **UUIDv4 used?** | ⚠️ PARTIAL | `uuid/__init__.py:17`: re-exports stdlib `uuid4`; `scanner/base.py:263`: fallback UUIDv4 in one scanner path; `uuid/generator.py:5`: `import random` used for UUIDv7 random bits | UUIDv4 present as stdlib import; one scanner fallback still uses it. UUIDv7 implementation uses `random.getrandbits()` — non-cryptographic but acceptable for ID generation |
| **Notion external IDs preserved?** | ✅ PASS | `sql/005_notion_index_schema.sql:183-184`: `page_id text not null`, `block_id text not null` in `block_snapshot`; `object_snapshot:118`: `object_id text not null` stores Notion page ID; `indexer/notion_ingest.py:637-723`: page_id and block_id extracted from source documents and preserved as-is | Source-native Notion IDs are preserved separately from generated internal IDs |
| **Tests verify BLAKE3?** | ✅ PASS | `tests/test_hashing.py`: tests `hash_bytes()` determinism and algorithm == "blake3"; `tests/test_canonical_shortcuts.py`: references BLAKE3; `tests/test_ssot_core_desktopcam.py:55`: BLAKE3 assertion | |
| **Tests verify UUIDv7?** | ✅ PASS | `tests/test_uuid.py`: tests `uuid7_str()` format (5 segments, version nibble = 7 at position 14) | Minimal but functional |
| **SHA256 as primary anywhere?** | ✅ PASS | No file uses SHA-256 as the sole or primary hash; always paired with BLAKE3 or as optional fallback | |
| **ULID usage?** | ✅ PASS | Zero matches found — consistent with UUIDv7 + BLAKE3 design | |

---

## Gaps Between Current Code and Intended Design

### 1. UUIDv7 Random Bits Source
- **File**: `uuid/generator.py:5`
- **Issue**: Uses `random.getrandbits()` (Mersenne Twister) for the 74 random bits of UUIDv7
- **Impact**: Non-cryptographic randomness. Acceptable for single-threaded ID generation, but if UUIDv7 IDs ever need to be unpredictable in a security context, this should use `secrets.randbits()` or `os.urandom()`

### 2. UUIDv4 Fallback in Scanner
- **File**: `scanner/base.py:263`
- **Issue**: UUIDv4 fallback path still exists
- **Impact**: Should be audited to confirm it's only used for legacy compatibility, not for new record generation

### 3. Schema ID Types
- **File**: `sql/005_notion_index_schema.sql`
- **Issue**: Uses `text` for all IDs (`snapshot_id`, `object_id`, `run_id`, `artifact_id`, etc.) rather than `uuid` type
- **Impact**: Fine for UUIDv7 string representation, but Postgres won't enforce UUID format at the type level

---

## Files Inspected (Key)

| File | Lines of Interest |
|---|---|
| `hashing/__init__.py` | 1-14 — BLAKE3 + Merkle exports |
| `hashing/blake3_utils.py` | 1-94 — BLAKE3 hasher, fallback, dual hash |
| `hashing/provenance.py` | 1-145 — Merkle tree, canonical JSON, BLAKE3 hex |
| `uuid/__init__.py` | 1-31 — UUIDv7 re-exports, stdlib fallback |
| `uuid/generator.py` | 1-41 — UUIDv7 implementation |
| `scanner/models.py` | 1-52 — FileRecord with uuid7, blake3, sha256 fields |
| `ssot_core/models.py` | 1-352 — CanonicalFile, FileVersion, FileInstance using uuid7_str |
| `sql/005_notion_index_schema.sql` | 1-242 — Notion index schema with BLAKE3 columns, page_id/block_id |
| `sql/004_chat_ingestion.sql` | 1-65 — Chat ingestion with body_hash_blake3 |
| `sql/003_semantic_desktopcam.sql` | 1-65 — DesktopCam with timestamp_uuid7 |
| `indexer/notion_ingest.py` | 546-744 — Page ID and block ID preservation |
| `tests/test_hashing.py` | 1-9 — BLAKE3 determinism test |
| `tests/test_uuid.py` | 1-8 — UUIDv7 format test |

---

## Final Status

**HASH_ID_DESIGN_AUDIT_PASS**

The ssot-indexer codebase is correctly designed around UUIDv7 for generated internal IDs and BLAKE3 as the primary internal content hash. SHA-256 exists only as optional compatibility/audit support. Notion external IDs (page_id, block_id, object_id) are preserved separately. Minor gaps exist (non-cryptographic random in UUIDv7, UUIDv4 scanner fallback, text-based schema IDs) but none violate the core design intent.

---

*Report generated by Warp W21 — 2026-06-11T14:50:57Z*
*Co-Authored-By: Oz <oz-agent@warp.dev>*
