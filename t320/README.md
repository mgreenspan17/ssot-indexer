# T320 Integration

The scripts in this directory are designed to be idempotent and conservative.

- `install.sh`: deploys the repository to `/opt/ssot-indexer`, creates a venv, installs dependencies, and registers systemd units.
- `update.sh`: synchronizes the repo into the deployment root and restarts services.
- `rollback.sh`: restores from a backup directory and restarts services.
- `health.sh`: runs the local health checks for the major subsystems.
