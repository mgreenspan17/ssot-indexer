# AI Discovery Guide for SSOT MCP Registry

**DashboardID:** ssot-registry-001  
**Version:** 1.0.0  
**Author:** Oz + Manni  
**Session:** random-session-uuid  
**Last Updated:** 2026-06-05T20:09:00Z

---

## What This Is

This is the **Single Source of Truth (SSOT) Registry** for the Personal Intelligence Layer OS. It's an MCP (Model Context Protocol) server that provides standardized access to:

1. **Behavior Contracts** - Rules for how AI agents should interact
2. **Identity Graph** - Server mappings (srv1 = t320 = 192.168.1.50 = etc.)
3. **Preferences** - User preferences for AI interaction
4. **Deployment State** - Current system status and operational notes

## Where It Lives

- **Server:** srv1 (192.168.1.50 / t320 / Dell T320)
- **Path:** `/opt/ssot-registry/server.py`
- **Data:** `/opt/ssot-registry/registry/ssot-registry.json`
- **Service:** `ssot-registry.service` (systemd)
- **Logs:** `journalctl -u ssot-registry.service`

## How to Connect

### For MCP-Enabled AI Assistants

Add this configuration to your MCP server settings:

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

### For Direct HTTP Access

The server exposes resources at these URIs:
- `ssot://registry/ssot` - Complete registry
- `ssot://behavior/contract` - Behavior rules
- `ssot://identity/graph` - Server identity mappings
- `ssot://preferences/mannie` - User preferences
- `ssot://deployment/state` - Deployment status

### For SSH/Manual Access

```bash
ssh root@192.168.1.50
cat /opt/ssot-registry/registry/ssot-registry.json
```

## Available Tools

When connected via MCP, these tools are available:

1. **`query_registry(section)`** - Query specific registry sections
   - Valid sections: `all`, `behavior`, `identity`, `preferences`, `deployment`
   - Returns JSON data for the requested section

2. **`list_registry_sections()`** - List all available sections with descriptions
   - Returns a map of section paths to their descriptions

3. **`resolve_identity(alias)`** - Resolve any alias to canonical server entity
   - Example: `resolve_identity("t320")` returns srv1 entity details
   - Works with any known alias: srv1, t320, Dell T320, 192.168.1.50, main-server, ai-host

## Registry Schema

The registry follows a versioned JSON schema:

```json
{
  "$schema_version": "1.0.0",
  "registry_id": "ssot-registry-001",
  "last_updated": "2026-06-05T20:09:00Z",
  "agent_behavior_contract": {
    "interaction_loop_rule": "User pastes external agent reply → AI analyzes → AI produces one complete next prompt → AI waits.",
    "prompt_completeness_rule": "If the AI can anticipate future steps, include them now.",
    "no_partial_prompts": true,
    "warp_steering_style": "Use natural language steering, not raw commands, unless Warp chooses commands.",
    "deployment_context": "SSOT Indexer runs on srv1, not WSL."
  },
  "identity_graph": {
    "entities": {
      "srv1": {
        "aliases": ["t320", "Dell T320", "192.168.1.50", "main-server", "ai-host"],
        "roles": ["SSOT-Indexer-Host", "Database-Host", "AI-Node"],
        "edges": [
          {"relation": "runs_service", "target": "ssot-indexer"},
          {"relation": "runs_service", "target": "postgres"}
        ]
      }
    }
  },
  "preferences_mannie": {
    "requires_reply_analysis": true,
    "single_next_prompt": true,
    "no_partial_prompts": true
  },
  "deployment_state": {
    "repo": "github:mgreenspan17/ssot-indexer",
    "status": "in-progress",
    "notes": [
      "Code authored on desktop → pushed to GitHub.",
      "Warp deploys from WSL → srv1.",
      "SSH path must be fixed."
    ]
  }
}
```

## Version History

| Version | Date | Changes |
|---|---|---|
| 1.0.0 | 2026-06-05 | Initial release with behavior contract, identity graph, preferences, and deployment state sections |

## Troubleshooting

### Service Not Running
```bash
systemctl status ssot-registry.service
journalctl -u ssot-registry.service -n 50
```

### Restart Service
```bash
sudo systemctl restart ssot-registry.service
```

### Update Registry Data
1. Edit `/opt/ssot-registry/registry/ssot-registry.json`
2. Restart the service: `sudo systemctl restart ssot-registry.service`
3. The server reads the JSON file on each request, so changes take effect immediately after restart

### Check Logs
```bash
# Recent logs
journalctl -u ssot-registry.service --no-pager -n 100

# Follow logs in real-time
journalctl -u ssot-registry.service -f
```

## Security Notes

- The service runs with systemd security hardening enabled
- File system access is restricted to the registry directory only
- No new privileges are allowed for the service process
- Home directory protection is enabled
- All access is logged to journalctl

---

**For Questions:** Check `/opt/ssot-registry/README.md` or contact the system administrator.
**GitHub:** https://github.com/mgreenspan17/ssot-indexer/tree/main/mcp-registry
