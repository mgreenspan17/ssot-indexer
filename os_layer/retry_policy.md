# Retry Policy

Assumptions:
- Jobs may fail due to transient service or network errors.

Boundaries:
- Retry policy applies to bounded, idempotent work only.

Integration notes:
- Use with scheduler.py and compute_mesh.py.

Policy:
- retryable: true for transient compute or IO failures
- max_attempts: 3 by default
- backoff: 1s, 2s, 4s
- jitter: enabled
- terminal failures must escalate to Copilot
