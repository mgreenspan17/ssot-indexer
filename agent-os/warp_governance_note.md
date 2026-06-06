# Warp Governance Integration Note

Warp must always treat the following as governance authority:
- /srv/data/ssot-governance/AGENT_GOVERNANCE.md
- /registry/agent-governance

Execution rule:
- Before major operations, perform a lane self-check:
  - in-lane execution
  - safety rule compliance
  - phase authorization from Copilot

If uncertainty or conflict is detected:
- Stop execution.
- Return blocker details to Copilot.
