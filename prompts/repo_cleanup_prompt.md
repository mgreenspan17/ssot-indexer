# Repo Cleanup Wave Prompt

Version: v1.0
Timestamp: 2026-06-06T14:47:27Z
Purpose: Standardized safe cleanup workflow for SSOT repository maintenance without impacting pipeline runtime or data directories.

Full Prompt:

You are running the SSOT Repo Cleanup Wave.

Goal:
Safely clean the /opt/ssot-indexer repository without touching the running pipeline process or any data directories. Your job is to analyze the current Git workspace, categorize all changes, and produce a safe cleanup plan.

Rules:
- DO NOT modify or delete anything inside:
  /srv/data/
  /tmp/
  venv/
  .index/
  .index_db/
  .index_human/
  ingestion output directories
  pipeline runtime directories

- DO NOT touch the running pipeline process (PID 774410 or any active pipeline_phase3.py).

Steps:

1. Run a full diff analysis:
   - Identify modified files
   - Identify untracked files
   - Identify ignored files
   - Identify accidental edits
   - Identify debug artifacts
   - Identify stale worktrees

2. Categorize each file into:
   - core source code (pipeline_api, scripts, services)
   - tests
   - configs
   - docs
   - accidental edits
   - debug artifacts
   - stray files
   - build artifacts
   - cache junk

3. Produce a cleanup plan:
   - files to KEEP
   - files to DELETE (only safe junk)
   - files to REVERT (accidental edits)
   - files to STAGE (intentional changes)
   - files to IGNORE (venv, data dirs, runtime dirs)

4. Execute cleanup actions:
   - prune stale worktrees
   - remove safe untracked junk
   - revert accidental edits
   - leave intentional edits untouched

5. Produce a final report:
   - summary of deleted junk
   - summary of reverted files
   - summary of staged files
   - confirmation that the repo is clean
   - confirmation that no pipeline-related directories were touched
   - confirmation that the pipeline process was not affected

PRESERVATION REQUIREMENTS (IMPORTANT):
After generating the cleanup plan and performing the cleanup, you MUST save this cleanup prompt for future generations of agents.

Save it in two locations:
1. In the repository:
   /opt/ssot-indexer/prompts/repo_cleanup_prompt.md

2. In the SSOT Prompt Library (Notion):
   SSOT → Prompts → Repo Cleanup Wave

The saved file must contain:
- The full text of this prompt
- A timestamp
- A short description of its purpose
- Version number (start at v1.0)

This ensures all future agents (Warp, Orchestrator, Cody, and successors) can reuse this cleanup wave without needing it rewritten.
