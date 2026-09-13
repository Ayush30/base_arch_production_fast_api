# Testing and interpreting the evidence

[Root](../README.md) · [Tests](../tests/README.md)

Unit tests verify isolated behavior such as token validation, password verification, commission rounding, production configuration guards, translations, rate-limit decisions and metrics. Integration tests use a real PostgreSQL database, actual HTTP requests through ASGI, real RSA tokens, and a separate database transaction per request. They do not replace authorization with an always-admin test user.

```bash
uv run pytest tests/unit -q
uv run pytest tests/integration -q
uv run pytest --cov=app --cov-report=html
```

The default coverage gate applies to the complete suite, so a narrow subset may report less than 85%. Use `--no-cov` for a focused debugging run, then run the full suite before considering the change verified. Coverage is configured for SQLAlchemy's greenlet-based async bridge; omitting that setting can under-report lines after database awaits. See [Coverage concurrency configuration](https://coverage.readthedocs.io/en/latest/config.html#run-concurrency).

Testcontainers uses PostgreSQL 16 unless `TEST_DATABASE_URL` is provided. Each test creates a unique schema and deletes it afterward. A dedicated database user needs schema create/drop permissions. Tests do not seed your development schema. RSA test keys are temporary and separate from local application keys.

The suite covers a two-seller lifecycle, ownership/role denial, privilege escalation rejection, seller approval, user disablement, refresh rotation, logout/reset revocation, optimistic product versions, catalog moderation, idempotent checkout/payment/refund, transaction rollback on price mismatch, competing buyers for the last unit, simultaneous duplicate checkout, stock expiry, settlement holds and outbox retries.

The broker publish call is mocked in outbox integration tests to deterministically force failure. Those tests validate durable PostgreSQL state and retry behavior, not a real broker deployment. Load balancing, carrier delivery, email delivery and real card payments require separate infrastructure/provider tests. The local payment endpoint is a simulation.

CI runs lint, formatting, strict source type checking, documentation checks, PostgreSQL integration tests, and migration upgrade/check/downgrade/upgrade in a disposable database. Pin and periodically update dependencies through the lockfile; review changes and rerun checks. Do not lower the coverage threshold to make failures disappear.
