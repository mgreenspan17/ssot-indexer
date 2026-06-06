# Autonomy Scoring

Assumptions:
- Autonomy is bounded by lane, safety, and Copilot authorization.

Boundaries:
- Scores are advisory and do not override governance.

Integration notes:
- Use autonomy_engine.py as the reference evaluator.

Baseline:
- Warp: execution 3, design 1
- Cody: artifact_generation 3, execution 0
- Copilot: coordination 3, direct_execution 0
- Experimental: compute 3, infrastructure 0
