# SSOT Indexer Deployment Report

**Date**: 2026-06-05T20:42:00Z
**Server**: srv1 / t320 (192.168.1.50)
**Deployed Commit**: `dccdc98` - chore: remove tmp deploy artifacts
**GitHub Repo**: https://github.com/mgreenspan17/ssot-indexer

---

## Issues Found & Fixed

### 1. SSH Connectivity
- **Broken**: WSL couldn't resolve hostname `t320`, wrong username (`mannie` vs `mannieg`)
- **Fixed**: Updated `~/.ssh/config` with correct aliases (srv1, t320, 192.168.1.50), user `mannieg`, key `id_ed25519`

### 2. Duplicate Script Blocks
- **Broken**: All `t320/*.sh` scripts had duplicated content blocks from Cody generation
- **Fixed**: Rewrote `install.sh`, `update.sh`, `health.sh`, `rollback.sh` cleanly
- **Commit**: `7a44412` - fix: clean up all t320 scripts

### 3. Systemd Service File Duplication
- **Broken**: `ssot-indexer.service` and `ssot-api.service` had two `[Unit]` blocks each
- **Fixed**: Removed duplicate sections, kept single valid unit definitions
- **Commit**: `d8e754d` - fix: remove duplicate [Unit] blocks in systemd service files

### 4. Systemd Restart Loop
- **Broken**: `update.sh` called `systemctl restart ssot-indexer.service` from within the ssot-indexer service itself, causing a systemd job loop
- **Fixed**: Changed `update.sh` to only restart `ssot-api.service`
- **Commit**: `675378c` - fix: prevent systemd restart loop in update.sh

### 5. Logging Path Permission Error
- **Broken**: `observability/logging.py` tried to create `logs/` relative to `/opt/ssot-indexer` which failed with `PermissionError: [Errno 13]`
- **Fixed**: Changed default log directory from `logs` to `/var/log/ssot-indexer`
- **Commit**: `d267d4f` - fix: use /var/log/ssot-indexer for logging instead of relative logs dir

### 6. PostgreSQL Not Installed
- **Broken**: PostgreSQL service not found on server
- **Fixed**: Installed `postgresql` and `postgresql-contrib` packages, created `ssot` user and database

### 7. Script Permissions
- **Broken**: `update.sh` not executable after rsync
- **Fixed**: Set `chmod +x` on all t320 scripts

---

## Deployment Steps Completed

| Step | Status |
|------|--------|
| Git fetch/reset to origin/main | ✅ |
| rsync to /opt/ssot-indexer | ✅ |
| systemd daemon-reload | ✅ |
| ssot-api.service enabled & running | ✅ |
| ssot-indexer.service (oneshot) completed successfully | ✅ |
| Health endpoint `/health` returning `{"status":"ok"}` | ✅ |
| API docs available at `/docs` | ✅ |
| Listening on 0.0.0.0:8000 | ✅ |

---

## Service Status

- **ssot-api.service**: ✅ active (running)
- **ssot-indexer.service**: ✅ inactive (dead) - expected for oneshot orchestrator
- **postgresql**: ✅ active

## API Endpoints

- Health: `http://127.0.0.1:8000/health` → `{"status":"ok"}`
- Docs: `http://127.0.0.1:8000/docs` → Swagger UI available
