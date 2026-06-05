from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RepoMapping:
    name: str
    root_path: str
    pipeline: str


def default_repo_map() -> list[RepoMapping]:
    return [
        RepoMapping(name="ssot-indexer", root_path=".", pipeline="cli-to-postgres"),
    ]
