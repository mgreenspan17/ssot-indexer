# SSOT Registry MCP Server

**Version:** 1.0.0  
**Author:** Oz + Manni  
**Date:** 2026-06-05  
**Session:** random-session-uuid

Persistent MCP-backed SSOT Registry service running on **srv1** (192.168.1.50 / t320 / Dell T320).

## Purpose

Provides a single source of truth for:
- Agent behavior contracts
- Identity graph (server aliases, roles, services)
- Personal preferences for AI interaction
- Deployment state and operational notes

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    MCP Clients (AIs)                     │
│  Warp  │  Claude  │  Copilot  │  Cody  │  Local LLMs    │
└────┬────────┬────────┬────────┬────────┬────────────────┘
     │        │        │        │        │
     └────────┴────────┴────────┴────────┘
                          │
                    MCP Protocol
                          │
┌─────────────────────────────────────────────────────────┐
│              SSOT Registry MCP Server                    │
│  (Python mcp package, systemd service)                   │
│  Runs on: srv1 (192.168.1.50)                            │
│  Path: /opt/ssot-registry/server.py                      │
└─────────────────────────────────────────────────────────┘
                          │
                    Reads from:
┌─────────────────────────────────────────────────────────┐
│           /opt/ssot-registry/registry/                   │
│  └── ssot-registry.json (canonical versioned data)       │
└─────────────────────────────────────────────────────────┘
```

## Available Resources

| Resource URI | Description |
|---|---|
| `ssot://registry/ssot` | Complete registry (all sections) |
| `ssot://behavior/contract` | Agent behavior contract rules |
| `ssot://identity/graph` | Server identity mappings and roles |
| `ssot://preferences/mannie` | Personal AI interaction preferences |
| `ssot://deployment/state` | Deployment status and notes |

## Available Tools

| Tool Name | Description |
|---|---|
| `query_registry(section)` | Query a specific registry section |
| `list_registry_sections()` | List all available sections |
| `resolve_identity(alias)` | Resolve alias to canonical server entity |

## Installation

### On srv1 (192.168.1.50)

```bash
# From your desktop, run:
bash mcp-registry/deploy/deploy-to-srv1.sh

# Or manually on srv1:
sudo mkdir -p /opt/ssot-registry/registry
sudo cp server.py /opt/ssot-registry/
sudo cp registry/ssot-registry.json /opt/ssot-registry/registry/
sudo cp deploy/ssot-registry.service /etc/systemd/system/

cd /opt/ssot-registry
python3 -m venv venv
./venv/bin/pip install mcp

sudo systemctl daemon-reload
sudo systemctl enable ssot-registry
sudo systemctl start ssot-registry
```

### Verify Installation

```bash
systemctl status ssot-registry.service
journalctl -u ssot-registry.service -f
```

## Usage by AI Agents

### MCP Configuration

Add this to your AI assistant's MCP server configuration:

```json
{
  "mcpServers": {
    "ssot-registry": {
      "command": "/opt/ssot-registry/venv/bin/python3",
      "args": ["/opt/ssot-registry/server.py"],
      "env": {
        "REGISTRY_DIR": "/opt/ssot-registry/registry"
      }
    }
  }
}
```

### Example Queries

Once connected, AIs can:
1. Read `ssot://registry/ssot` to get the full registry
2. Call `query_registry("behavior")` to get behavior rules
3. Call `resolve_identity("t320")` to find server details
4. Read `ssot://deployment/state` to check deployment status

## Updating the Registry

To update registry data:

```bash
# 1. Edit the JSON file
nano /opt/ssot-registry/registry/ssot-registry.json

# 2. Restart service to pick up changes
sudo systemctl restart ssot-registry

# 3. Verify
journalctl -u ssot-registry -n 20
```

## Logs

```bash
# View recent logs
journalctl -u ssot-registry.service --no-pager -n 50

# Follow logs in real-time
journalctl -u ssot-registry.service -f
```

## Registry Schema

The registry uses a versioned JSON schema:

```json
{
  "$schema_version": "1.0.0",
  "registry_id": "ssot-registry-001",
  "last_updated": "ISO-8601-timestamp",
  "agent_behavior_contract": { ... },
  "identity_graph": { ... },
  "preferences_mannie": { ... },
  "deployment_state": { ... }
}
```

Each section includes metadata when queried, with timestamps and source information.

## Security

- Runs as root with systemd security hardening
- NoNewPrivileges=true
- ProtectSystem=strict (read-only except registry dir)
- ProtectHome=true
- ReadWritePaths limited to registry directory

## Maintenance

### Backup Registry

```bash
cp /opt/ssot-registry/registry/ssot-registry.json \
   /opt/ssot-registry/registry/ssot-registry.json.bak.$(date +%Y%m%d)
```

### Update Service

```bash
# Pull latest code
cd /opt/ssot-registry
git pull  # if using git

# Restart
sudo systemctl restart ssot-registry

# Verify
systemctl status ssot-registry
```

---

**Changelog:**
- 1.0.0 (2026-06-05): Initial release with behavior contract, identity graph, preferences, and deployment state sections.
