# System Governance and Modularity

## Design Principles

- Storage-agnostic rule engine
- Replaceable connectors
- Stable API contracts
- Vendor-neutral deployment model
- Model-agnostic intelligence interfaces

## Module Boundaries

| Module | Responsibility | Replaceability |
|---|---|---|
| scanner/connectors | source discovery and metadata pull | high |
| hashing | content identity primitives | medium |
| ssot_core | domain rules and classification | medium |
| persistence layer | SQL schema + transaction control | high |
| API layer | external contract surface | high |
| semantic layer | near-duplicate intelligence | high |
| forensic layer | event-chain capture and verification | high |
| global chat ingestion layer | message normalization, idea extraction, ranking | high |

## API Contract Strategy

- Contracts are behavior-based, not implementation-based.
- Providers must emit normalized events.
- Intelligence encoders must satisfy embedding protocol.
- Forensic recorder must emit append-only chain-compatible events.
- Chat adapters must emit canonical message payloads and deterministic source keys.
- Ranking engines must publish explainability metadata for each score output.

## Deployment Independence

Supported deployment patterns:
- single-node local
- enterprise VM cluster
- containerized environment
- hybrid edge + central index

## Vendor Neutrality

- No dependency on a single cloud or model provider.
- Connector and embedding contracts allow interchangeable implementations.
- Data export formats are open and auditable.
- Chat ingestion adapters are platform-specific but share a single canonical schema contract.

## Multi-Tenant Considerations

- namespace isolation per tenant
- tenant-scoped canonical IDs and indexes
- per-tenant key management and retention policies
- audit partitioning and access controls
- tenant-bound chat retention, legal hold, and workspace-scoped query policies

## Replaceability Checklist (Per Module)

| Module | Must Preserve |
|---|---|
| Semantic layer | embedding interface, similarity API contracts, cluster schema |
| DesktopCam layer | append-only event semantics, chain verification determinism |
| Chat ingestion layer | canonical_message schema, idempotency keys, ranking explainability |
