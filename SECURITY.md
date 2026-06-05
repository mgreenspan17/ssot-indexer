# Security Policy

## Threat Model

See [threat-model.md](security/threat-model.md) for the system summary.

## Hardening Recommendations

- Run the scanner and orchestrator with a dedicated service account.
- Store `DATABASE_URL`, `GITHUB_TOKEN`, SSH keys, and rclone credentials in a secret manager.
- Prefer read-only SSH and rclone credentials for discovery workflows.
- Restrict systemd units to the deployment directory and the canonical store root.
- Enable symlink creation only where it is required.
- Keep `chmod 600` on private keys and `.env` files.
- Use separate Postgres roles for migrations, ingestion, and read-only health checks.
- Rotate release tokens regularly and prefer GitHub Actions `GITHUB_TOKEN` over long-lived PATs.

## Scanning and Dependencies

- Dependency scanning is handled by `.github/workflows/dependency-scan.yml`.
- Secrets scanning is handled by `.github/workflows/secrets-scan.yml`.
