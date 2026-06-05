"""
SSOT MCP Registry Service (FastAPI)
Session: random-session-uuid | Author: Oz + Manni | Date: 2026-06-05
Version: 1.0.0

FastAPI-based MCP registry service exposing the Personal Intelligence Layer OS
global specifications, rules, identity mappings, preferences, and deployment state.

Designed for discovery by all AIs (Warp, Cody, Copilot, Claude, local LLMs, server agents).

Endpoints:
  GET /behavior/contract
  GET /identity/graph
  GET /preferences/mannie
  GET /deployment/state
  GET /registry/ssot
  GET /health
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# --- Configuration ---
REGISTRY_DIR = Path("/opt/mcp-registry/registry")
SERVER_NAME = "ssot-registry-mcp"
SERVER_VERSION = "1.0.0"
SERVER_AUTHOR = "Oz + Manni"
HOST = "0.0.0.0"
PORT = 9000

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(SERVER_NAME)

# --- FastAPI App ---
app = FastAPI(
    title=SERVER_NAME,
    version=SERVER_VERSION,
    description=(
        f"SSOT Registry MCP Server ({SERVER_VERSION}) — "
        f"Author: {SERVER_AUTHOR} — {datetime.now(timezone.utc).isoformat()}\n"
        "Provides access to the Personal Intelligence Layer OS global registry.\n"
        "Available endpoints: /behavior/contract, /identity/graph, /registry/ssot, "
        "/preferences/mannie, /deployment/state"
    ),
)


# --- Helpers ---
def _load_json(filename: str) -> dict:
    """Load and return a JSON file from the registry directory."""
    filepath = REGISTRY_DIR / filename
    if not filepath.exists():
        logger.error(f"Registry file not found: {filepath}")
        raise FileNotFoundError(f"Registry file not found: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def _add_metadata(data: dict, source: str) -> dict:
    """Add query metadata to the response."""
    data["_metadata"] = {
        "source": f"ssot://{source}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "server": SERVER_NAME,
        "version": SERVER_VERSION,
        "author": SERVER_AUTHOR,
    }
    return data


# --- Endpoints ---
@app.get("/health")
def health_check():
    """Health check endpoint for service monitoring."""
    return {
        "status": "healthy",
        "server": SERVER_NAME,
        "version": SERVER_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/behavior/contract")
def get_behavior_contract():
    """Return the agent behavior contract rules."""
    try:
        data = _load_json("behavior.json")
        return _add_metadata(data, "behavior/contract")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Behavior contract not found")


@app.get("/identity/graph")
def get_identity_graph():
    """Return the identity graph mapping servers, aliases, and roles."""
    try:
        data = _load_json("identity.json")
        return _add_metadata(data, "identity/graph")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Identity graph not found")


@app.get("/preferences/mannie")
def get_preferences():
    """Return Mannie's personal preferences for AI interaction."""
    try:
        data = _load_json("preferences.json")
        return _add_metadata(data, "preferences/mannie")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Preferences not found")


@app.get("/deployment/state")
def get_deployment_state():
    """Return the current deployment state and notes."""
    try:
        data = _load_json("deployment.json")
        return _add_metadata(data, "deployment/state")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Deployment state not found")


@app.get("/registry/ssot")
def get_full_registry():
    """Return the complete SSOT registry (all sections combined)."""
    try:
        registry = {
            "behavior": _load_json("behavior.json"),
            "identity": _load_json("identity.json"),
            "preferences": _load_json("preferences.json"),
            "deployment": _load_json("deployment.json"),
            "ssot_root": _load_json("ssot.json"),
        }
        return _add_metadata(registry, "registry/ssot")
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/registry/sections")
def list_registry_sections():
    """List all available registry sections and their descriptions."""
    sections = {
        "behavior/contract": "Agent behavior contract rules and deployment context",
        "identity/graph": "Server identity mappings, aliases, roles, and service edges",
        "preferences/mannie": "Personal AI interaction preferences and safety constraints",
        "deployment/state": "Current deployment status, repo, and operational notes",
        "registry/ssot": "Complete registry (all sections combined)",
    }
    return sections


@app.get("/registry/resolve/{alias}")
def resolve_identity(alias: str):
    """Resolve an alias or identifier to its canonical server entity.

    Args:
        alias: Any known identifier (e.g., 't320', 'srv1', '192.168.1.50').
    """
    try:
        data = _load_json("identity.json")
        entities = data.get("entities", {})

        for entity_name, entity_data in entities.items():
            aliases = entity_data.get("aliases", [])
            if alias.lower() in [a.lower() for a in aliases] or alias.lower() == entity_name.lower():
                return {
                    "canonical_name": entity_name,
                    "aliases": aliases,
                    "roles": entity_data.get("roles", []),
                    "edges": entity_data.get("edges", []),
                    "_metadata": {
                        "query": f"resolve_identity({alias})",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                }

        return JSONResponse(
            status_code=404,
            content={
                "error": f"No entity found for alias: {alias}",
                "available_entities": list(entities.keys()),
            },
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Identity graph not found")


# --- Startup/Shutdown ---
@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {SERVER_NAME} v{SERVER_VERSION} by {SERVER_AUTHOR}")
    logger.info(f"Registry directory: {REGISTRY_DIR}")
    logger.info(f"Service listening on {HOST}:{PORT}")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"Shutting down {SERVER_NAME}")


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting {SERVER_NAME} v{SERVER_VERSION} by {SERVER_AUTHOR}")
    logger.info(f"Registry directory: {REGISTRY_DIR}")

    uvicorn.run(
        "app:app",
        host=HOST,
        port=PORT,
        reload=False,
        log_level="info",
    )
