# Migration Policy

- Migrations must be sequential and additive.
- Each migration must be safe to re-run where practical.
- Schema changes must preserve existing file, version, hash, and location records.
- Migration execution must be validated in CI before release.
