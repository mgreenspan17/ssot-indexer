# Threat Model Summary

- Confidentiality: protect source paths, file contents, Postgres credentials, and shortcut targets.
- Integrity: verify BLAKE3 digests before canonical storage, prevent silent shortcut replacement, and keep migration ordering deterministic.
- Availability: avoid destructive operations in scanners and deploy scripts; keep nightly jobs read-only unless explicitly ingesting into an isolated database.
- Attack surfaces: CLI arguments, manifest input, SSH/rclone remotes, GitHub Actions secrets, Postgres DSNs, and systemd service environments.
