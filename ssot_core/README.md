# SSOT Core Folder

Purpose:
- This folder contains the deterministic domain rule engine for identity, versioning, duplication, movement, provider sync, semantic clustering, and forensic event chaining.

Primary documents:
- `ARCHITECTURE.md` for the complete architecture and rule model.

Primary modules:
- `models.py` (domain entities)
- `versioning.py`, `duplicates.py`, `moves.py`, `provider_sync.py` (core rule sets)
- `semantic_similarity.py` (future intelligence module)
- `desktopcam.py` (forensic recorder module)
- `reporting.py` (operational and product reporting helpers)

Integration rule:
- Keep these modules storage-agnostic; persistence and transport layers should call into this package rather than embedding domain logic elsewhere.
