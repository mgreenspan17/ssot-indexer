# SSOT Semantic + DesktopCam Architecture

## Purpose

This document defines the initial architecture for two permanent roadmap modules:

1. Semantic Similarity Layer (future intelligence)
2. DesktopCam Forensic Layer (immutable screen evidence)

## Semantic Similarity Layer

### Core Data Model

- `semantic_cluster`
  - `cluster_id` (UUID7)
  - `canonical_file_ids[]`
  - `similarity_scores` (pairwise map)
  - `representative_embedding`
  - `created_at`, `updated_at`

- `semantic_membership`
  - `cluster_id`
  - `file_id`
  - `canonical_file_id`
  - `similarity_score`

### Feature Extraction

- Perceptual hashes
  - `aHash`
  - `dHash`
  - `pHash` (DCT-based)
- Embeddings
  - `EmbeddingModel` protocol to support CLIP integrations
  - `ByteHistogramEmbeddingModel` as deterministic fallback

### Similarity / Clustering

- Pair score = weighted cosine + perceptual similarity
- APIs
  - `find_semantically_similar_files(file_id, fingerprints, threshold, top_k)`
  - `cluster_new_file(file_id, fingerprints, existing_clusters, threshold)`
  - `rebuild_semantic_clusters(fingerprints, threshold)`

### Integration Points

- Input from `files` + `versions` + provider metadata
- Output clusters feed:
  - duplicate review workflows
  - semantic search
  - timeline UI and DesktopCam frame grouping

## DesktopCam Forensic Layer

### Core Data Model

- `desktopcam_frame`
  - `frame_id` (UUID7)
  - `timestamp_uuid7`
  - `session_id`
  - `device_id`
  - `file_id`
  - `version_id`
  - `blake3_hash`
  - `bytes_size`

- `audit_event` (append-only)
  - `event_id` (UUID7)
  - `timestamp_uuid7`
  - `blake3_hash`
  - `frame_id`
  - `previous_event_hash`
  - `event_hash`

### Chain-of-Custody

- Each event hash is computed over:
  - timestamp UUID7
  - frame hash
  - frame id
  - previous event hash
- Verification scans chain from genesis event to latest event.

### Recorder API

- `start_desktopcam(recorder, max_frames=None)`
- `stop_desktopcam(recorder)`
- `verify_event_chain(recorder)`
- `export_forensic_bundle(recorder)`

### Crash Resilience

- Recorder supports per-event flush hooks for immediate durability
- Recovery helper returns valid event prefix length for partial chain repair

### Integration Points

- Captured frame becomes:
  - `CanonicalFile` (BLAKE3 identity)
  - `FileVersion` (lineage-ready)
  - `FileInstance` (provider = desktopcam)
- Forensic exports include session metadata, frame inventory, and event chain validity.

## Lineage and Versioning Notes

- Semantic cluster changes do not rewrite canonical identity.
- DesktopCam frames are immutable snapshots; edits create new versions, never in-place updates.
- Event chain is append-only and should be persisted with DB triggers preventing update/delete.
