# Routing Rules

Assumptions:
- Task metadata contains a lane hint, kind, and authorization flag.

Boundaries:
- Routing suggests lanes; it does not execute tasks.

Integration notes:
- Use with routing_engine.py and lane_gate.py.

Rules:
- deploy/restart/validate/sync -> Warp
- design/patch/document/plan -> Cody
- route/coordinate/approve/triage -> Copilot
- embeddings/inference/analytics/research -> Experimental
