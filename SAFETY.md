# Safety

## Operating Principles

- Keep scanner operations read-only.
- Keep canonical store writes limited to canonicalization flows.
- Treat shortcuts as derived artifacts only.
- Never allow agent roles to bypass policy checks.

## Boundary Rules

- Read-only agents may inspect metadata, hashes, versions, and relationships.
- Write agents may ingest or canonicalize only through approved lifecycle tasks.
- No agent may mutate the canonical store without a verified BLAKE3 match.
