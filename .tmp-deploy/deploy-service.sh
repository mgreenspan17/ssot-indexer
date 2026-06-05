#!/bin/bash
# deploy-service.sh
# Deploy and start MCP Registry Service on srv1
# Author: Oz + Manni | Session: random-session-uuid | Date: 2026-06-05
# Version: 1.0.0

set -euo pipefail

echo "=== Deploying MCP Registry Service on srv1 ==="

# Copy service file to systemd
sudo cp /opt/mcp-registry/service/mcp-registry.service /etc/systemd/system/mcp-registry.service

# Reload systemd
sudo systemctl daemon-reload

# Enable and start service
sudo systemctl enable mcp-registry
sudo systemctl restart mcp-registry

echo "=== Deployment Complete ==="

# Show status
systemctl status mcp-registry --no-pager || true
