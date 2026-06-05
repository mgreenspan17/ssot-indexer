#!/usr/bin/env bash
# deploy-to-srv1.sh
# Deploy SSOT MCP Registry Service to srv1 (192.168.1.50)
# Author: Oz + Manni | Session: random-session-uuid | Date: 2026-06-05
# Version: 1.0.0
#
# Usage: bash deploy-to-srv1.sh [SSH_USER]
#   SSH_USER defaults to 'root' if not provided

set -euo pipefail

SSH_USER="${1:-root}"
SERVER_IP="192.168.1.50"
REMOTE_DIR="/opt/ssot-registry"
SERVICE_NAME="ssot-registry.service"

echo "=== SSOT MCP Registry Deployment ==="
echo "Target: ${SSH_USER}@${SERVER_IP}"
echo "Remote dir: ${REMOTE_DIR}"
echo ""

# --- Step 1: Verify SSH connectivity ---
echo "[1/6] Verifying SSH connectivity..."
if ! ssh -o ConnectTimeout=10 -o BatchMode=yes "${SSH_USER}@${SERVER_IP}" echo "SSH OK" 2>/dev/null; then
    echo "ERROR: Cannot SSH to ${SERVER_IP} as ${SSH_USER}."
    echo "Fix SSH key authentication first:"
    echo "  ssh-copy-id ${SSH_USER}@${SERVER_IP}"
    echo "  # or add your public key to ${SSH_USER}@${SERVER_IP}:~/.ssh/authorized_keys"
    exit 1
fi
echo "SSH connectivity verified."

# --- Step 2: Create remote directory ---
echo "[2/6] Creating remote directory structure..."
ssh "${SSH_USER}@${SERVER_IP}" "mkdir -p ${REMOTE_DIR}/registry"

# --- Step 3: Copy files ---
echo "[3/6] Copying files to ${SERVER_IP}:${REMOTE_DIR}..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "${SCRIPT_DIR}")"

scp "${PROJECT_ROOT}/server.py" "${SSH_USER}@${SERVER_IP}:${REMOTE_DIR}/"
scp "${PROJECT_ROOT}/registry/ssot-registry.json" "${SSH_USER}@${SERVER_IP}:${REMOTE_DIR}/registry/"
scp "${SCRIPT_DIR}/${SERVICE_NAME}" "${SSH_USER}@${SERVER_IP}:/tmp/${SERVICE_NAME}"

echo "Files copied successfully."

# --- Step 4: Install Python dependencies ---
echo "[4/6] Installing Python dependencies..."
ssh "${SSH_USER}@${SERVER_IP}" << 'EOF'
cd /opt/ssot-registry
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install mcp
EOF

echo "Dependencies installed."

# --- Step 5: Install systemd service ---
echo "[5/6] Installing systemd service..."
ssh "${SSH_USER}@${SERVER_IP}" << EOF
cp /tmp/${SERVICE_NAME} /etc/systemd/system/
systemctl daemon-reload
systemctl enable ${SERVICE_NAME}
systemctl start ${SERVICE_NAME}
EOF

# Wait for service to start
sleep 3

# --- Step 6: Verify service ---
echo "[6/6] Verifying service status..."
ssh "${SSH_USER}@${SERVER_IP}" "systemctl status ${SERVICE_NAME} --no-pager" || true
echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Service: ${SERVICE_NAME}"
echo "Status: $(ssh ${SSH_USER}@${SERVER_IP} 'systemctl is-active ssot-registry.service' 2>/dev/null || echo 'checking...')"
echo ""
echo "Logs: journalctl -u ${SERVICE_NAME} -f"
echo ""
echo "To test manually:"
echo "  cd ${REMOTE_DIR}"
echo "  ./venv/bin/python server.py"
echo ""
echo "AI Discovery: Copy the content of ${REMOTE_DIR}/README-AI-DISCOVERY.md"
echo "              to your AI assistant's MCP configuration."
