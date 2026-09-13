# Verification record

Verified locally on 2026-09-13 with Python 3.12 and the checked-in dependency lockfile.

| Check | Result |
|---|---|
| Full test suite against Compose PostgreSQL 16 | 46 passed; 88.67% statement coverage (required: 85%) |
| Ruff lint | Passed for src, tests, scripts and alembic |
| Ruff formatting | Passed for 106 Python files |
| Strict mypy | Passed for 82 source files |
| Folder documentation and Markdown links | Passed |
| Initial migration upgrade → drift check → downgrade → upgrade | Passed against an isolated PostgreSQL 15 database |
| Migration SQL generation without a database | Passed |
| Container build using frozen dependencies | Passed |
| Base Compose startup | API, PostgreSQL and Redis healthy; reservation worker running |
| Documented seed and buyer journey | Passed against host API and Docker API; Docker used real Redis auth rate limiting |
| Base, events/observability and load-balancing Compose configuration parsing | Passed |
| Kafka 3.9.1 and outbox delivery | Passed; console consumer read a real event, and all 4 persisted events were marked published |
| Nginx two-replica lab | Both API instances healthy; documented buyer checkout/payment journey passed through the proxy |

The integration suite includes concurrent last-unit purchases and concurrent identical checkout retries. Each HTTP request receives its own PostgreSQL session. Kafka publishing failures are injected in worker tests; published-state rollback and retry are asserted against PostgreSQL.

Coverage includes the retained unmounted template modules; it is not a security certification or proof of production capacity. The test suite disables rate limiting for most API scenarios and separately tests Redis limit decisions and fail-closed behavior. The Docker smoke journey exercises the real Redis connection.

Real payment/email/carrier providers, cloud deployment, TLS termination, production backup restoration, load/stress behavior and live business operations have not been validated. See [deployment readiness](DEPLOYMENT.md) and [payment boundaries](MONEY_AND_PAYMENTS.md).
