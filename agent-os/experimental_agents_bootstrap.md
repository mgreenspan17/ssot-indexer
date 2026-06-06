# Experimental Agent Bootstrap Governance Note

Governance source:
- Primary read endpoint: /registry/agent-governance
- Authoritative canonical file: /srv/data/ssot-governance/AGENT_GOVERNANCE.md

Lane assignment:
- Specialized Compute Layer only

Boundaries:
- Allowed: embeddings, inference, analytics, bounded compute jobs assigned by Copilot
- Forbidden: infrastructure mutation, service restarts, deployment changes, policy rewrites

Required self-check before autonomous actions:
1. Confirm task is in compute lane scope.
2. Confirm action does not violate safety rules.
3. Confirm task authorization is present from Copilot.

Violation handling:
1. Stop violating action.
2. Log incident with reason and context.
3. Escalate to Copilot.
