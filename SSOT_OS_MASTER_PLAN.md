# SSOT OS Master Plan

Version: 1.0.0
Status: Draft Canonical Plan
Canonical source: /srv/data/ssot-governance/SSOT_OS_MASTER_PLAN.md
Registry mirror: /registry/ssot-os-master-plan
Checksum: <PENDING>

## Table of Contents

- [1. Purpose and Scope](#1-purpose-and-scope)
- [2. Governance Policy](#2-governance-policy)
- [3. Lane Definitions](#3-lane-definitions)
- [4. Safety and Isolation Rules](#4-safety-and-isolation-rules)
- [5. Escalation Rules](#5-escalation-rules)
- [6. Phase Execution Rules](#6-phase-execution-rules)
- [7. Deadlock Prevention](#7-deadlock-prevention)
- [8. Autonomy Scoring Model](#8-autonomy-scoring-model)
- [9. Agent-to-Agent Contracts](#9-agent-to-agent-contracts)
- [10. Future Agent Onboarding](#10-future-agent-onboarding)
- [11. Canonical Storage and Registry Mirror](#11-canonical-storage-and-registry-mirror)
- [12. OS Layer Initialization Blueprint](#12-os-layer-initialization-blueprint)
- [13. Crawl Pipeline Architecture](#13-crawl-pipeline-architecture)
- [14. Recovery and Drift Detection](#14-recovery-and-drift-detection)
- [15. Versioning and Sync Policy](#15-versioning-and-sync-policy)
- [16. How to Validate Governance Integrity](#16-how-to-validate-governance-integrity)
- [17. How to Onboard New Agents](#17-how-to-onboard-new-agents)
- [18. How to Recover From Drift](#18-how-to-recover-from-drift)
- [19. How to Extend the OS](#19-how-to-extend-the-os)
- [20. Integration Notes for Warp, Copilot, Cody, and Experimental Agents](#20-integration-notes-for-warp-copilot-cody-and-experimental-agents)

## 1. Purpose and Scope

This document is the single authoritative master plan for SSOT OS. It unifies governance, lane separation, execution controls, OS-layer architecture, crawl flow, recovery rules, and extension patterns for all current and future agents.

Assumptions:
- The canonical file is stored in SSOT governance storage.
- The registry mirror is read-only and reflects the canonical file exactly.

Boundaries:
- No agent may treat a derivative copy as authoritative when this document or its canonical mirror is available.

Integration notes:
- Warp should deploy this document to canonical storage and mirror it into the registry section.
- Copilot should load this document at startup and re-read on phase transitions.

## 2. Governance Policy

The governance policy establishes lane boundaries, safety controls, coordination flow, escalation paths, and autonomy limits.

Core rule:
- Operator -> Copilot -> (Warp | Cody | Experimental Agents)

Assumptions:
- All agents are coordination-bound and must remain within their lane.

Boundaries:
- No direct operator-to-agent control path outside Copilot mediation.
- No agent-to-agent direct control path outside Copilot mediation.

Integration notes:
- Governance policy is mirrored to the registry and validated periodically for drift.

## 3. Lane Definitions

### Warp Lane
- Execution layer for approved operations, deployment actions, service lifecycle steps, and controlled filesystem changes.

### Cody Lane
- Creation layer for source generation, design artifacts, patch plans, migration plans, and documentation.

### Copilot Lane
- Coordination layer for routing, phase advancement, validation gating, and escalation management.

### Experimental Agents Lane
- Specialized compute layer for bounded tasks such as embeddings, inference, analytics, and research.

Assumptions:
- Each agent has one primary lane.

Boundaries:
- Lane boundaries are not optional and do not dissolve during incidents.

Integration notes:
- Lane definitions must be visible to all agents at startup.

## 4. Safety and Isolation Rules

- No destructive operations on root filesystem.
- No unauthorized writes to system directories.
- No unvalidated restart of critical services.
- No cross-lane interference.
- No assumptions about state without validation evidence.

Additional rules:
- Write operations must target approved paths only.
- High-impact actions require Copilot authorization and post-action validation.
- Read-only diagnostics are preferred when the system state is uncertain.

Assumptions:
- The system may be partially degraded; safety rules still apply.

Boundaries:
- A failed validation blocks escalation to the next phase.

Integration notes:
- Safety decisions should be surfaced in dashboards and diagnostic events.

## 5. Escalation Rules

- Warp escalates to Copilot when blocked by safety, ambiguity, or policy conflict.
- Cody escalates to Copilot when the specification is incomplete or inconsistent.
- Experimental agents escalate to Copilot when a task exceeds compute-only scope.
- Copilot escalates to Operator when architecture, security posture, or governance changes are required.

Assumptions:
- Escalation reports are structured and include the blocker, lane, and requested decision.

Boundaries:
- Escalation does not authorize execution by itself.

Integration notes:
- The escalation router should standardize target selection and message formatting.

## 6. Phase Execution Rules

- Each phase must complete fully before closure.
- Each phase must report results, evidence, and residual risk.
- Copilot explicitly advances phases.
- No agent may begin a new phase without Copilot authorization.

Assumptions:
- A phase is a bounded unit of work with a defined exit criterion.

Boundaries:
- Partial completion is not phase completion.

Integration notes:
- Phase transitions should be recorded in logs, dashboards, and event streams.

## 7. Deadlock Prevention

- If an agent becomes idle while waiting, Copilot detects the stall and issues the next goal.
- Blocked agents escalate to Copilot with minimal unblock data.
- Copilot escalates to Operator if the stall is caused by architecture or security changes.

Assumptions:
- Idle time is a signal, not a conclusion.

Boundaries:
- Agents do not self-promote stalled work into new work without Copilot approval.

Integration notes:
- Progress watchdogs and refresh loops should detect stale phases and stalled work.

## 8. Autonomy Scoring Model

- Warp: high autonomy in execution, low autonomy in design.
- Cody: high autonomy in artifact generation, zero autonomy in execution.
- Copilot: high autonomy in coordination, zero autonomy in direct execution.
- Experimental agents: high autonomy in compute, zero autonomy in infrastructure.

Recommended scale:
- 0 = prohibited
- 1 = low
- 2 = medium
- 3 = high

Assumptions:
- Autonomy is bounded by lane rules, safety rules, and escalation rules.

Boundaries:
- Autonomy scores are advisory and never override governance.

Integration notes:
- The autonomy engine should consume this policy as the source of truth.

## 9. Agent-to-Agent Contracts

### Warp <-> Cody
- Cody produces artifacts; Warp executes them only when Copilot authorizes.

### Warp <-> Copilot
- Warp receives goals from Copilot, not raw commands.
- Warp returns evidence and status to Copilot.

### Cody <-> Copilot
- Cody receives specifications from Copilot, not runtime state.
- Cody returns complete artifacts and handoff notes to Copilot.

### Experimental Agents <-> Copilot
- Experimental agents receive narrow compute tasks from Copilot.
- Experimental agents return results only to Copilot.

Assumptions:
- All inter-agent communication is mediated or recorded.

Boundaries:
- Direct peer-to-peer control is not allowed.

Integration notes:
- Contract definitions should be mirrored in future policy-aware routing engines.

## 10. Future Agent Onboarding

Any new agent must:
- Be assigned a lane.
- Be given explicit responsibilities and boundaries.
- Be wired into the coordination hierarchy via Copilot.
- Be documented in this master plan and the governance policy.
- Be prevented from touching infrastructure or architecture unless authorized.

Assumptions:
- New agents may be experimental, local, GPU-based, or cloud-based.

Boundaries:
- Onboarding is incomplete until governance visibility is confirmed.

Integration notes:
- Onboarding should include startup checks, health checks, and escalation routing.

## 11. Canonical Storage and Registry Mirror

Primary canonical file:
- Path: /srv/data/ssot-governance/SSOT_OS_MASTER_PLAN.md
- Ownership: controlled governance user or ssot user.
- Readable by agents that need policy access.
- Writable only by approved governance workflows.

Registry mirror:
- Path: /registry/ssot-os-master-plan
- Read-only for agents.
- Updated only by controlled sync.

Sync model:
- The canonical file is the single source of truth.
- The registry section is a mirror.
- Any canonical change must trigger mirror refresh.
- No agent may directly edit the registry mirror.

Assumptions:
- The canonical file and mirror can be checksum-validated.

Boundaries:
- Divergence between canonical and mirror is a drift condition.

Integration notes:
- Mirror payload should include the same document text plus sync metadata.

## 12. OS Layer Initialization Blueprint

The OS layer provides reusable, importable building blocks for governance, routing, diagnostics, memory, eventing, and operator surfaces.

### 12.1 Governance Engine
- Components: governance_loader, governance_validator, governance_enforcer, governance_refresh_loop.

### 12.2 Routing Fabric
- Components: routing_engine, lane_gate, escalation_router, routing_rules.

### 12.3 Compute Mesh
- Components: compute_mesh, worker_registry, scheduler, retry_policy.

### 12.4 Autonomy Engine
- Components: autonomy_engine, autonomy_rules, autonomy_scoring.

### 12.5 Self-Diagnostic Loop
- Components: diagnostics_loop, health_checks, diagnostics_events.

### 12.6 Event Bus
- Components: event_bus, event_types, event_stream.

### 12.7 Memory Layer
- Components: memory_layer, metadata_store, embedding_store, registry_cache.

### 12.8 Dashboard Architecture
- Components: dashboard index, dashboard.css, dashboard.js, component panels, dashboard_api, dashboard_design.

### 12.9 Operator Console
- Components: operator_console, console_commands, console_api.

### 12.10 Initialization Sequence
- Components: os_init, os_boot_sequence, heartbeat.

Assumptions:
- The blueprint may start with placeholders and become live as Warp and runtime components are wired in.

Boundaries:
- These modules should remain importable without execution side effects.

Integration notes:
- Each component should include assumptions, boundaries, and integration notes in its own artifact.

## 13. Crawl Pipeline Architecture

Pipeline stages:
1. Sample crawl and discovery.
2. Indexing and manifest creation.
3. Deep content expansion.
4. Canonicalization and shortcut generation.
5. Postgres ingestion and registry/memory updates.

Assumptions:
- Sample crawl may run before full crawl results exist.

Boundaries:
- Deep crawl does not begin until sample-stage validation succeeds.

Integration notes:
- Pipeline progress should be surfaced in the dashboard and event bus.

## 14. Recovery and Drift Detection

Recovery procedures:
- Compare canonical file checksum with registry mirror checksum.
- Re-read governance when checksum changes.
- Pause new work if a drift condition is detected.
- Require Copilot reauthorization before resuming.

Drift signals:
- Missing sections.
- Version mismatch.
- Checksum mismatch.
- Unexpected lane or policy changes.
- Runtime divergence from canonical storage.

Assumptions:
- Drift is detectable through metadata and periodic refresh.

Boundaries:
- Recovery actions must remain within lane-specific permissions.

Integration notes:
- Diagnostics events should capture drift and recovery outcomes.

## 15. Versioning and Sync Policy

- Version every governance or master-plan change.
- Include checksum metadata in canonical and mirror surfaces.
- Sync canonical to registry in a controlled one-way flow.
- Preserve changelog and approval provenance.

Assumptions:
- Semantic versioning is sufficient for policy evolution.

Boundaries:
- Direct mirror edits are prohibited.

Integration notes:
- Sync jobs should validate text equivalence before publishing.

## 16. How to Validate Governance Integrity

Validation steps:
1. Load the canonical document.
2. Confirm required sections exist.
3. Confirm checksum matches expected value or pending update state.
4. Confirm registry mirror text matches canonical text.
5. Confirm lane rules and escalation paths remain intact.
6. Confirm dashboards and agent bootstrap notes point to canonical sources.

Assumptions:
- Validation is repeatable and read-only.

Boundaries:
- Validation must not mutate policy sources.

Integration notes:
- Governance validation should run at startup and during refresh loops.

## 17. How to Onboard New Agents

Onboarding sequence:
1. Assign lane.
2. Define responsibilities and boundaries.
3. Attach governance source pointers.
4. Install self-check and escalation hooks.
5. Register in memory, routing, or registry surfaces as appropriate.
6. Validate policy adherence before autonomous work begins.

Assumptions:
- New agents may start in read-only or compute-only mode.

Boundaries:
- No new agent may modify infrastructure without explicit authorization.

Integration notes:
- Onboarding should be documented in governance, registry, and runtime bootstrap notes.

## 18. How to Recover From Drift

Recovery sequence:
1. Detect drift using checksum or section mismatch.
2. Stop new writes and high-impact actions.
3. Re-read canonical governance and registry mirror.
4. Identify the divergent surface.
5. Repair the canonical source or mirror through controlled workflow.
6. Revalidate and reauthorize phase execution.

Assumptions:
- Drift recovery may require manual operator review when policy changed materially.

Boundaries:
- Do not continue autonomous work while governance state is ambiguous.

Integration notes:
- Recovery outcomes should be emitted as diagnostics and event stream records.

## 19. How to Extend the OS

Extension rules:
- Add new modules as modular, importable, and self-contained artifacts.
- Preserve lane boundaries.
- Include assumptions, boundaries, and integration notes in each artifact.
- Add validation and placeholder data paths before wiring live execution.

Assumptions:
- Extensions may include new agents, new compute nodes, or new dashboard panels.

Boundaries:
- Extensions must not weaken governance or safety controls.

Integration notes:
- Extension proposals should be authored by Cody and approved by Copilot before Warp deployment.

## 20. Integration Notes for Warp, Copilot, Cody, and Experimental Agents

### Warp
- Treat the canonical file and registry mirror as governance authority.
- Self-check lane adherence before major operations.
- Execute only approved, validated work.

### Copilot
- Load governance before routing tasks.
- Re-read governance periodically and on phase transitions.
- Coordinate all lanes and enforce boundaries.

### Cody
- Produce artifacts, plans, and machine-readable change sets.
- Do not execute infrastructure changes directly.

### Experimental Agents
- Accept narrow compute tasks only.
- Return results to Copilot, not to peers or operators.

Assumptions:
- Future agent families will follow the same governance pattern.

Boundaries:
- Any agent that cannot obey lane, safety, and escalation rules must be blocked from autonomy.

Integration notes:
- This master plan should be the first document loaded by new agent bootstraps.
