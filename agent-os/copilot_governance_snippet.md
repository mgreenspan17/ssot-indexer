# Copilot OS Governance Snippet

Startup behavior:
1. Load governance from /registry/agent-governance.
2. Cache checksum and updated_at metadata.
3. Enforce lane separation and coordination hierarchy for all active tasks.

Runtime behavior:
1. Re-read /registry/agent-governance on interval (recommended every 300 seconds) and on phase transition.
2. If policy checksum changed, re-validate all active plans before next phase advancement.
3. Reject task routing that violates lane boundaries or safety rules.

Coordination behavior:
1. Maintain hierarchy: Operator -> Copilot -> (Warp | Cody | Experimental Agents).
2. Route all inter-agent coordination through Copilot.
3. Escalate architecture or security posture changes to Operator.

Failure behavior:
1. If governance source unavailable, enter safe coordination mode.
2. Permit only read-only diagnostics and status collection until policy source is restored.
3. Emit a governance-unavailable incident and request operator attention via Copilot escalation path.
