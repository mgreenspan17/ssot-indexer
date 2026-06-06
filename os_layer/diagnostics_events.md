# Diagnostics Events

Assumptions:
- Diagnostics events are structured, append-only records.

Boundaries:
- Diagnostics emit reports and escalation hints; they do not remediate.

Integration notes:
- Use diagnostics_loop.py to aggregate checks and emit health_failure events.

Event shapes:
- health_failure
- governance_mismatch
- agent_lane_violation
- registry_miss
- database_unreachable
- filesystem_guard_triggered
