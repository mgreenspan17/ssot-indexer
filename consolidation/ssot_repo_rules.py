from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RepoRule:
    rule_name: str
    description: str


def default_repo_rules() -> list[RepoRule]:
    return [
        RepoRule(rule_name="unify_references", description="Normalize references across repositories"),
        RepoRule(rule_name="unify_ingestion", description="Use a single ingest contract"),
        RepoRule(rule_name="unify_metadata", description="Keep metadata shapes consistent"),
        RepoRule(rule_name="unify_classification", description="Use one classification policy"),
    ]
