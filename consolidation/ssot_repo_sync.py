from __future__ import annotations

from dataclasses import dataclass

from consolidation.ssot_repo_map import default_repo_map
from consolidation.ssot_repo_rules import default_repo_rules


@dataclass(frozen=True)
class RepoSyncResult:
    repositories: list[dict[str, str]]
    rules: list[dict[str, str]]


def sync_repositories() -> RepoSyncResult:
    return RepoSyncResult(
        repositories=[mapping.__dict__ for mapping in default_repo_map()],
        rules=[rule.__dict__ for rule in default_repo_rules()],
    )
