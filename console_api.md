# Console API

Assumptions:
- API calls are read-mostly and coordination oriented.

Boundaries:
- No API method should mutate infrastructure without Copilot authorization.

Integration notes:
- Expose status, list, validate, and plan operations.

Suggested methods:
- GET /dashboard/status
- GET /dashboard/governance
- POST /console/command
- GET /console/commands
- POST /diagnostics/run
