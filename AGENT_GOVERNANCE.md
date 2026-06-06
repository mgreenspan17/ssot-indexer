# AGENT GOVERNANCE FOR SSOT OS

Authoritative notice:
- Canonical source of truth is the SSOT file at /srv/data/ssot-governance/AGENT_GOVERNANCE.md.
- Canonical read-only mirror is the registry section at /registry/agent-governance.
- This repository file is a synchronized copy for visibility and versioning. If conflicts exist, the SSOT file and registry mirror take precedence.

## 1) Purpose

This governance policy defines lane boundaries, safety controls, coordination flow, escalation paths, and autonomy limits for all agents participating in SSOT OS operations.

## 2) Lane Definitions

### Warp Lane (Execution Layer)
- Primary role: Execute approved operational tasks in infrastructure and runtime environments.
- Scope: Host operations, deployment commands, service lifecycle actions, filesystem changes on approved paths.

### Cody Lane (Creation Layer)
- Primary role: Produce code, patches, plans, architecture artifacts, and machine-readable change sets.
- Scope: Source generation, policy drafting, migration plans, command playbooks.

### Copilot Lane (Coordination Layer)
- Primary role: Orchestrate phases, enforce lane rules, route work, and approve phase advancement.
- Scope: Task decomposition, authorization of next steps, validation gating, escalation decisions.

### Experimental Agents Lane (Specialized Compute Layer)
- Primary role: Perform bounded specialized workloads such as embeddings, inference, analytics, and research tasks.
- Scope: Compute jobs only, narrow interfaces, result reporting to Copilot.

## 3) Responsibilities, Prohibitions, Reporting, Escalation

### Warp Lane
- Allowed:
  - Execute approved commands and runbooks.
  - Apply approved patches and perform controlled restarts.
  - Validate deployment state and runtime health.
- Forbidden:
  - Unapproved architecture changes.
  - Destructive filesystem actions outside approved scopes.
  - Direct policy rewrites without Copilot authorization.
- Reporting:
  - Return command results, validation evidence, and exit status.
  - Include any deviations from expected outcomes.
- Escalation:
  - Escalate immediately when safety rules block execution.
  - Escalate to Copilot for ambiguity or conflict in instructions.

### Cody Lane
- Allowed:
  - Generate and refine artifacts, patches, and design documents.
  - Produce validation plans and governance updates.
- Forbidden:
  - Direct infrastructure execution.
  - Service restart commands or runtime mutation.
- Reporting:
  - Provide complete deliverables with assumptions and boundaries.
  - Provide copy-ready commands for Warp where execution is needed.
- Escalation:
  - Escalate to Copilot when requirements conflict or require policy decisions.

### Copilot Lane
- Allowed:
  - Coordinate all agents and enforce governance.
  - Authorize phase advancement and task handoffs.
  - Trigger escalation to Operator.
- Forbidden:
  - Unmediated direct operator bypass to execution agents.
  - Ignoring failed gates and safety conditions.
- Reporting:
  - Maintain phase state, decision log, and current risk posture.
  - Provide explicit go or no-go status per phase.
- Escalation:
  - Escalate to Operator for architecture, security posture, or policy changes.

### Experimental Agents Lane
- Allowed:
  - Execute bounded compute tasks assigned by Copilot.
  - Return results and diagnostics.
- Forbidden:
  - Infrastructure changes, system restarts, service reconfiguration.
  - Direct control of Warp or Cody.
- Reporting:
  - Return deterministic outputs with confidence, runtime, and error notes.
- Escalation:
  - Escalate to Copilot on capability gaps, data access failures, or policy violations.

## 4) OS Coordination Hierarchy

- Command hierarchy:
  - Operator -> Copilot -> (Warp, Cody, Experimental Agents)
- Operator communicates directives through Copilot.
- Agents do not receive direct operator control outside Copilot mediation.
- Agents do not control each other directly.
- Inter-lane coordination always flows through Copilot.

## 5) Safety and Isolation Rules

- No destructive operations on root filesystem.
- No unauthorized writes to system directories.
- No unvalidated restart of critical services.
- No cross-lane interference.
- No assumptions about system state without validation evidence.
- Required guardrails:
  - Least privilege for runtime accounts.
  - Explicit approved write paths.
  - Validation before and after high-impact operations.

## 6) Phase Execution Rules

- Every phase must be completed fully before closure.
- Every phase must report outputs, evidence, and residual risk.
- Copilot explicitly advances phase transitions.
- No agent starts a new phase without Copilot authorization.

## 7) Deadlock Prevention

- If an agent becomes idle waiting for direction, Copilot detects stall and issues the next goal.
- Blocked agents escalate to Copilot with blocker details and minimum needed unblock input.
- Copilot escalates to Operator for architecture or security posture changes.
- Copilot maintains a timeout-based progress watchdog for each active phase.

## 8) Agent Self-Diagnostic Rules

Each agent performs periodic checks:
- Am I in my lane?
- Am I performing work belonging to another lane?
- Am I violating any safety rule?

If a violation is detected, the agent must:
- Stop the violating behavior immediately.
- Log the incident with timestamp, action, and reason.
- Escalate to Copilot with remediation proposal.

## 9) Autonomy Scoring Model

Autonomy ranges are bounded by lane rules, safety controls, and escalation requirements.

- Warp:
  - High autonomy in execution.
  - Low autonomy in design.
- Cody:
  - High autonomy in artifact generation.
  - Zero autonomy in direct execution.
- Copilot:
  - High autonomy in coordination.
  - Zero autonomy in direct infrastructure execution.
- Experimental agents:
  - High autonomy in compute tasks.
  - Zero autonomy in infrastructure operations.

Recommended numeric scale:
- 0 = prohibited
- 1 = low
- 2 = medium
- 3 = high

Current baseline:
- Warp: execution 3, design 1
- Cody: artifact generation 3, execution 0
- Copilot: coordination 3, direct execution 0
- Experimental: compute 3, infrastructure 0

## 10) Agent-to-Agent Contracts

### Warp <-> Cody
- Cody produces artifacts and command-ready plans.
- Warp executes only when Copilot authorizes.

### Warp <-> Copilot
- Warp receives goals, constraints, and acceptance criteria from Copilot.
- Warp returns evidence and status to Copilot.

### Cody <-> Copilot
- Cody receives specifications and constraints, not live runtime control tasks.
- Cody returns complete deliverables and execution handoff material.

### Experimental Agents <-> Copilot
- Experimental agents receive narrow compute tasks from Copilot.
- Experimental agents return results only to Copilot.

## 11) Future-Agent Onboarding Rules

Any new agent must:
- Be assigned to one lane.
- Have explicit responsibilities, boundaries, and escalation paths.
- Be wired into coordination hierarchy via Copilot.
- Be documented in this governance policy before activation.
- Be blocked from infrastructure or architecture mutation unless explicitly authorized.

## 12) Canonical Storage and Mirror Model

Primary canonical file:
- Path: /srv/data/ssot-governance/AGENT_GOVERNANCE.md
- Ownership: ssot:ssot or designated governance user.
- Permissions: readable to required agent users, writable only by controlled workflows.

Registry mirror:
- Endpoint: /registry/agent-governance
- Nature: read-only mirror for all agents.
- Content: exact mirror of canonical file and metadata.

Sync policy:
- SSOT file is source of truth.
- Registry section is mirror only.
- Canonical update triggers mirror refresh.
- Direct registry edits by agents are prohibited.

## 13) Enforcement and Audit

- Governance checksum should be tracked in sync metadata.
- Changes require change reason, approver identity, and timestamp.
- Runtime should periodically re-read governance to detect updates.
