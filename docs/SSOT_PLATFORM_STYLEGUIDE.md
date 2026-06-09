# SSOT Documentation Style Guide

This file defines formatting conventions used by the SSOT documentation set.

- Use concise section headers.
- Include diagrams (Mermaid preferred) for architecture or process flow.
- Use tables for schema, controls, and comparisons.
- Keep language vendor-neutral and model-agnostic.
- Distinguish current implementation from planned modules.

Maintenance rules:
- Every new subsystem must update `docs/INDEX.md`.
- Every subsystem doc must include: architecture, data model, API contracts, integration notes, test plan, rationale/tradeoffs.
- Planned modules must be labeled with status and migration path.
- Avoid references to specific assistants, proprietary orchestration tools, or single-vendor dependencies unless explicitly required by deployment context.
