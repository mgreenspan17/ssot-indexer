# AI Discovery Guide for SSOT MCP Registry

**DashboardID:** ssot-registry-001  
**Version:** 1.0.0  
**Author:** Oz + Manni  
**Session:** random-session-uuid  
**Last Updated:** 2026-06-05T20:34:39Z

---

## What This Is

This is the **Single Source of Truth (SSOT) Registry** for the Personal Intelligence Layer OS. It's a FastAPI-based HTTP service running on **srv1** that exposes registry data for all AI agents (Warp, Cody, Copilot, Claude, local LLMs, server agents).

## Where It Lives

- **Server:** srv1 (192.168.1.50 / t320 / Dell T320)
- **Path:** `/opt/mcp-registry/service/app.py`
- **Data:** `/opt/mcp-registry/registry/*.json`
- **Service:** `mcp-registry.service` (systemd)
- **Port:** 9000
- **User:** mannieg

## How to Query

### HTTP Endpoints

```bash
# From any machine on the network:
curl http://192.168.1.50:9000/behavior/contract
curl http://192.168.1.50:9000/identity/graph
curl http://192.168.1.50:9000/preferences/mannie
curl http://192.168.1.50:9000/deployment/state
curl http://192.168.1.50:9000/registry/ssot

# Health check:
curl http://192.168.1.50:9000/health

# List all sections:
curl http://192.168.1.50:9000/registry/sections

# Resolve identity alias:
curl http://192.168.1.50:9000/registry/resolve/t320
```

### For AI Agents

When an AI needs to query this registry, use these endpoints:
1. `GET /behavior/contract` - Agent behavior rules and deployment context
2. `GET /identity/graph` - Server identity mappings, aliases, roles
3. `GET /preferences/mannie` - Personal AI interaction preferences
4. `GET /deployment/state` - Deployment status and operational notes
5. `GET /registry/ssot` - Complete registry (all sections)

## Registry Schema

Each JSON file follows this schema:
```json
{
  "$schema_version": "1.0.0",
  "registry_id": "ssot-registry-001",
  "section": "<section_name>",
  "last_updated": "ISO-8601-timestamp",
  "author": "Oz + Manni",
  "<section_data>"
}
```

Responses include `_metadata` with query timestamp and server info.

## Version History

| Version | Date | Changes |
|---|---|---|
| 1.0.0 | 2026-06-05 | Initial release with behavior contract, identity graph, preferences, deployment state, and ssot root sections |

## Troubleshooting

### Service Status
```bash
ssh mannieg@srv1 "systemctl status mcp-registry"
```

### Service Logs
```bash
ssh mannieg@srv1 "journalctl -u mcp-registry --no-pager -n 50"
```

### Restart Service
```bash
ssh mannieg@srv1 "sudo systemctl restart mcp-registry"
```

### Test Endpoints
```bash
ssh mannieg@srv1 "curl http://127.0.0.1:9000/health"
```

---

**GitHub:** https://github.com/mgreenspan17/ssot-indexer
**Registry Path:** /opt/mcp-registry/registry/
