"""
SSOT MCP Registry Server
Session: random-session-uuid | Author: Oz + Manni | Date: 2026-06-05
Version: 1.0.0

MCP server exposing the Personal Intelligence Layer OS SSOT Registry.
Endpoints:
  - /behavior/contract
  - /identity/graph
  - /registry/ssot
  - /preferences/mannie
  - /deployment/state

Designed for discovery by all AIs (Warp, Cody, Copilot, Claude, local LLMs, server agents).
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

# --- Configuration ---
REGISTRY_DIR = Path(__file__).parent / "registry"
REGISTRY_FILE = REGISTRY_DIR / "ssot-registry.json"
SERVER_NAME = "ssot-registry-mcp"
SERVER_VERSION = "1.0.0"
SERVER_AUTHOR = "Oz + Manni"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger(SERVER_NAME)


# --- Registry Loader ---
def _load_registry() -> dict[str, Any]:
    """Load and return the canonical SSOT registry JSON."""
    if not REGISTRY_FILE.exists():
        logger.error(f"Registry file not found: {REGISTRY_FILE}")
        raise FileNotFoundError(f"Registry file not found: {REGISTRY_FILE}")

    with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# --- MCP Server ---
mcp = FastMCP(
    name=SERVER_NAME,
    version=SERVER_VERSION,
    instructions=(
        f"SSOT Registry MCP Server ({SERVER_VERSION}) — "
        f"Author: {SERVER_AUTHOR} — {datetime.now(timezone.utc).isoformat()}\n"
        "Provides access to the Personal Intelligence Layer OS global registry.\n"
        "Available resources: /behavior/contract, /identity/graph, /registry/ssot, "
        "/preferences/mannie, /deployment/state"
    ),
)


@mcp.resource("ssot://registry/ssot")
def get_full_registry() -> str:
    """Return the complete SSOT registry as JSON."""
    registry = _load_registry()
    registry["_metadata"] = {
        "server": SERVER_NAME,
        "version": SERVER_VERSION,
        "author": SERVER_AUTHOR,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_file": str(REGISTRY_FILE),
    }
    return json.dumps(registry, indent=2, ensure_ascii=False)


@mcp.resource("ssot://behavior/contract")
def get_behavior_contract() -> str:
    """Return the agent behavior contract rules."""
    registry = _load_registry()
    contract = registry.get("agent_behavior_contract", {})
    contract["_metadata"] = {
        "source": "ssot://behavior/contract",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return json.dumps(contract, indent=2, ensure_ascii=False)


@mcp.resource("ssot://identity/graph")
def get_identity_graph() -> str:
    """Return the identity graph mapping servers, aliases, and roles."""
    registry = _load_registry()
    graph = registry.get("identity_graph", {})
    graph["_metadata"] = {
        "source": "ssot://identity/graph",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return json.dumps(graph, indent=2, ensure_ascii=False)


@mcp.resource("ssot://preferences/mannie")
def get_preferences() -> str:
    """Return Mannie's personal preferences for AI interaction."""
    registry = _load_registry()
    prefs = registry.get("preferences_mannie", {})
    prefs["_metadata"] = {
        "source": "ssot://preferences/mannie",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return json.dumps(prefs, indent=2, ensure_ascii=False)


@mcp.resource("ssot://deployment/state")
def get_deployment_state() -> str:
    """Return the current deployment state and notes."""
    registry = _load_registry()
    state = registry.get("deployment_state", {})
    state["_metadata"] = {
        "source": "ssot://deployment/state",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return json.dumps(state, indent=2, ensure_ascii=False)


# --- Tools for AI agents to query registry ---
@mcp.tool()
def query_registry(section: str = "all") -> str:
    """Query a specific section of the SSOT registry.

    Args:
        section: One of 'behavior', 'identity', 'preferences', 'deployment', 'all'.

    Returns:
        JSON string of the requested registry section.
    """
    registry = _load_registry()
    section_map = {
        "all": registry,
        "behavior": registry.get("agent_behavior_contract", {}),
        "identity": registry.get("identity_graph", {}),
        "preferences": registry.get("preferences_mannie", {}),
        "deployment": registry.get("deployment_state", {}),
    }

    if section not in section_map:
        return json.dumps(
            {"error": f"Unknown section: {section}. Valid: {list(section_map.keys())}"},
            indent=2,
        )

    data = section_map[section]
    data["_query_metadata"] = {
        "section": section,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "server": SERVER_NAME,
    }
    return json.dumps(data, indent=2, ensure_ascii=False)


@mcp.tool()
def list_registry_sections() -> str:
    """List all available registry sections and their descriptions."""
    sections = {
        "behavior/contract": "Agent behavior contract rules and deployment context",
        "identity/graph": "Server identity mappings, aliases, roles, and service edges",
        "preferences/mannie": "Personal AI interaction preferences and safety constraints",
        "deployment/state": "Current deployment status, repo, and operational notes",
        "registry/ssot": "Complete registry (all sections combined)",
    }
    return json.dumps(sections, indent=2, ensure_ascii=False)


@mcp.tool()
def resolve_identity(alias: str) -> str:
    """Resolve an alias or identifier to its canonical server entity.

    Args:
        alias: Any known identifier (e.g., 't320', 'srv1', '192.168.1.50').

    Returns:
        JSON with the resolved entity information or an error if not found.
    """
    registry = _load_registry()
    graph = registry.get("identity_graph", {})
    entities = graph.get("entities", {})

    for entity_name, entity_data in entities.items():
        aliases = entity_data.get("aliases", [])
        if alias.lower() in [a.lower() for a in aliases] or alias.lower() == entity_name.lower():
            return json.dumps(
                {
                    "canonical_name": entity_name,
                    "aliases": aliases,
                    "roles": entity_data.get("roles", []),
                    "edges": entity_data.get("edges", []),
                    "_metadata": {
                        "query": f"resolve_identity({alias})",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                },
                indent=2,
            )

    return json.dumps(
        {"error": f"No entity found for alias: {alias}", "available_entities": list(entities.keys())},
        indent=2,
    )


def main():
    """Entry point for the MCP server."""
    logger.info(f"Starting {SERVER_NAME} v{SERVER_VERSION} by {SERVER_AUTHOR}")
    logger.info(f"Registry file: {REGISTRY_FILE}")

    if not REGISTRY_FILE.exists():
        logger.warning(
            f"Registry file not found at {REGISTRY_FILE}. "
            "Run the deployment script to populate initial data."
        )

    mcp.run()


if __name__ == "__main__":
    main()
