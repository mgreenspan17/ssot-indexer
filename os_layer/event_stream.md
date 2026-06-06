# Event Stream

Assumptions:
- Agents publish events into a common stream for coordination and auditing.

Boundaries:
- The event stream is descriptive; durable transport is an implementation detail.

Integration notes:
- event_bus.py defines the in-memory interface.

Suggested stream topics:
- governance.refresh
- agent.health
- crawl.progress
- file.discovery
- registry.sync
- mesh.job
- escalation.request
