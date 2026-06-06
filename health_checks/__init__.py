"""Health check package for OS layer diagnostics.

Assumptions:
- Each check returns a small structured payload with a healthy flag.

Boundaries:
- These checks are diagnostic only and must not mutate state.

Integration notes:
- Use with diagnostics_loop to assemble a single health report.
"""
