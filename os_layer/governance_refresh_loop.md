# Governance Refresh Loop

Assumptions:
- Governance can change independently of agent runtime state.

Boundaries:
- Refreshes are read-only and should not modify the source of truth.

Integration notes:
- Copilot should trigger a refresh on startup, on phase transitions, and after governance updates.
- Warp should re-check governance before major execution steps.

Suggested loop:
1. Load /srv/data/ssot-governance/AGENT_GOVERNANCE.md or /registry/agent-governance.
2. Validate lane and safety sections.
3. Cache checksum and updated_at.
4. Re-read on a fixed interval.
5. If checksum changes, halt new work and ask Copilot to reauthorize.
