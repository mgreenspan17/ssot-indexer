# Upgrade Path

1. Update `VERSION` using `scripts/bump_version.py`.
2. Validate migrations with `scripts/validate_sql.py`.
3. Run CI and nightly workflows.
4. Apply database migrations in order.
5. Deploy to T320 using the idempotent scripts.
