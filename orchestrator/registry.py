# MCP Registry Client

Provides integration between the SSOT Indexer and the MCP Registry service.
Handles loading and caching of registry sections at startup.

## Sections
- behavior: Contract definitions for agent behavior
- identity: Agent identity graph
- preferences: User preferences and configuration
- deployment: Current deployment state

"""Registry client for MCP integration."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import httpx
from pydantic import BaseModel

from observability.logging import get_logger

logger = get_logger(__name__)


class RegistryMetadata(BaseModel):
    """Metadata about the registry sync operation."""
    timestamp: str
    sync_status: str
    registry_url: str
    sections_loaded: list[str]
    sections_failed: list[str]
    error: str | None = None


class RegistrySection(BaseModel):
    """A section from the MCP Registry."""
    section: str
    last_updated: str
    registry: str
    data: dict[str, Any]


class RegistryCache:
    """In-memory cache for MCP Registry sections."""

    def __init__(self, registry_url: str = "http://127.0.0.1:9000"):
        self.registry_url = registry_url
        self._cache: dict[str, Any] = {}
        self._metadata: RegistryMetadata | None = None
        self._sections: list[str] = [
            "behavior",
            "identity",
            "preferences",
            "deployment",
        ]
        self._section_endpoints: dict[str, str] = {
            "behavior": "/behavior/contract",
            "identity": "/identity/graph",
            "preferences": "/preferences/mannie",
            "deployment": "/deployment/state",
        }

    async def load_all_sections(self) -> RegistryMetadata:
        """Load all registry sections from the MCP Registry service."""
        sections_loaded: list[str] = []
        sections_failed: list[str] = []
        sync_status = "success"
        error: str | None = None

        async with httpx.AsyncClient() as client:
            for section_name in self._sections:
                endpoint = self._section_endpoints[section_name]
                try:
                    response = await client.get(
                        f"{self.registry_url}{endpoint}",
                        timeout=10.0,
                    )
                    response.raise_for_status()
                    data = response.json()
                    self._cache[section_name] = data
                    sections_loaded.append(section_name)
                    logger.info(f"Loaded registry section: {section_name}")
                except Exception as exc:
                    sections_failed.append(section_name)
                    logger.warning(f"Failed to load section {section_name}: {exc}")
                    sync_status = "partial_failure" if sections_loaded else "failure"

        self._metadata = RegistryMetadata(
            timestamp=datetime.now(timezone.utc).isoformat(),
            sync_status=sync_status,
            registry_url=self.registry_url,
            sections_loaded=sections_loaded,
            sections_failed=sections_failed,
            error=error,
        )

        logger.info(
            f"Registry sync complete: {len(sections_loaded)} sections loaded, "
            f"{len(sections_failed)} sections failed"
        )
        return self._metadata

    def get_all(self) -> dict[str, Any]:
        """Return all cached registry sections."""
        return dict(self._cache)

    def get_section(self, name: str) -> Any:
        """Return a specific cached section."""
        return self._cache.get(name)

    def get_metadata(self) -> RegistryMetadata | None:
        """Return sync metadata."""
        return self._metadata

    def is_loaded(self) -> bool:
        """Check if any sections have been loaded."""
        return bool(self._cache)
