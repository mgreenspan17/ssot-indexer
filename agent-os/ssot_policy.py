from __future__ import annotations

from dataclasses import dataclass


READ_ONLY_ROLES = {"scan", "resolve", "inspect", "sync"}
WRITE_ROLES = {"ingest", "canonicalize", "shortcuts"}


@dataclass(frozen=True)
class AgentPermission:
    role: str
    may_read: bool
    may_write: bool
    may_touch_canonical_store: bool


def policy_for(role: str) -> AgentPermission:
    if role in READ_ONLY_ROLES:
        return AgentPermission(role=role, may_read=True, may_write=False, may_touch_canonical_store=False)
    if role in WRITE_ROLES:
        return AgentPermission(role=role, may_read=True, may_write=True, may_touch_canonical_store=role == "canonicalize")
    return AgentPermission(role=role, may_read=False, may_write=False, may_touch_canonical_store=False)


def may_read(role: str) -> bool:
    return policy_for(role).may_read


def may_write(role: str) -> bool:
    return policy_for(role).may_write


def may_touch_canonical_store(role: str) -> bool:
    return policy_for(role).may_touch_canonical_store
