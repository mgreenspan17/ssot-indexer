# Deployment Guide

## Deployment Modes

- Developer workstation
- Single-tenant enterprise node
- Multi-tenant centralized service
- Hybrid edge collectors + central SSOT core

## Minimum Components

1. Ingestion services and connectors
2. Postgres database
3. `ssot_core` rule layer
4. API/reporting surface
5. Observability stack (logs/metrics/alerts)
6. Optional chat ingestion adapters and embedding backend

## Reference Deployment Flow

1. Provision database and apply migrations (`001`, `002`, `003`, optional `004`).
2. Configure connector credentials and provider sync state.
3. Start ingestion pipeline with checkpoint paths.
4. Validate canonical/version outputs.
5. Enable semantic and/or forensic modules as needed.
6. Configure scheduled reconciliation and chain verification jobs.
7. Enable chat adapters, classification jobs, and ranking/search endpoints if required.

## Operational Checks

- stage checkpoint freshness
- db connectivity and row growth
- provider lag and error rates
- duplicate/move event quality
- event-chain verification status
- chat adapter lag, classification throughput, ranking drift metrics

## Upgrade Strategy

- backward-compatible schema migration sequencing
- canary provider rollout
- replay verification in staging before production cutover
