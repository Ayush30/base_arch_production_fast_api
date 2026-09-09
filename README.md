# SGI Aviation — Backend Service Template

Base template for SGI Aviation backend microservices. Every service (Identity, Fleet & Asset, Valuation Engine, Reporting, Risk, etc.) is cloned from this template.

---

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) — dependency management
- Docker & Docker Compose
- PostgreSQL 16
- Redis 7

---

## Quick Start

### 1. Install dependencies

```bash
uv sync
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and set DATABASE_URL and any other required values
```

### Environment variables

The service reads configuration from `.env` via `app.core.config.Settings`.

| Variable | Example | Description | Usage |
|---|---|---|---|
| `APP_ENV` | `local` | Runtime environment name. | Enables Uvicorn reload when running `python -m app.main`. Non-local environments enable OTLP tracing export. |
| `APP_NAME` | `sgi-backend` | Service display name. | Used as the FastAPI title and startup log service name. |
| `APP_VERSION` | `0.1.0` | Service version. | Used as the FastAPI application version. |
| `APP_HOST` | `0.0.0.0` | Host/interface for the local Python entrypoint. | Used by `uv run python -m app.main` to bind Uvicorn. Use `127.0.0.1` for local-only access or `0.0.0.0` for container/network access. |
| `APP_PORT` | `8000` | HTTP port for the service. | Used by `uv run python -m app.main`, Docker, and Docker Compose port publishing. |
| `APP_DOCS_ENABLED` | `true` | Enables FastAPI API docs. | When enabled, Swagger is available at `/docs` and ReDoc at `/redoc`, regardless of `APP_ENV`. Disable in deployed environments if docs should not be public. |
| `APP_DEBUG` | `true` | Enables debug-level behavior. | Controls SQLAlchemy engine echo and logging level. |
| `SECRET_KEY` | `change-me-in-production` | Reserved application secret placeholder. | Present in `.env.example`, but not currently read by `Settings`. Add a setting before relying on it in code. |
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/sgi_backend` | Async PostgreSQL DSN. | Used by SQLAlchemy, Alembic migrations, tenant migration scripts, and tenant provisioning scripts. |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL for app-level cache/state. | Available in settings for Redis-backed service features. |
| `JWT_ALGORITHM` | `RS256` | JWT signing/verification algorithm. | Used when decoding JWTs in auth dependencies and tenant middleware. |
| `JWT_PUBLIC_KEY_PATH` | `keys/public.pem` | Path to the RSA public key. | Used to verify incoming JWTs. |
| `JWT_PRIVATE_KEY_PATH` | `keys/private.pem` | Path to the RSA private key. | Available for token signing flows in services that issue JWTs. Keep private keys out of source control. |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Access token lifetime in minutes. | Available for services that issue access tokens. |
| `OTLP_ENDPOINT` | `http://localhost:4317` | OpenTelemetry collector endpoint. | Used by tracing when `APP_ENV` is not `local`. For local Jaeger use `http://localhost:4317`; from Docker use the collector service name or `host.docker.internal`. |
| `OTEL_SERVICE_NAME` | `sgi-backend` | OpenTelemetry service name. | Added to trace and metric resource attributes. |
| `METRICS_ENABLED` | `true` | Enables Prometheus metrics exposure. | When enabled, the app mounts `METRICS_PATH` and exports process, Python runtime, and OpenTelemetry metric instruments for Prometheus scraping. |
| `METRICS_PATH` | `/metrics` | HTTP path for Prometheus scraping. | Prometheus should scrape this path on the service host and port. |
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Kafka broker address(es). | Used by `app/kafka/producer.py` to publish audit events (and any topics this service adds after cloning). This value is for running the app directly on the host; docker-compose.yml hardcodes `kafka:9092` for the containerized run. The broker itself is owned by `auth-service`'s docker-compose — see its README. |
| `KAFKA_CLIENT_ID` | `sgi-backend` | Kafka producer client id. | Identifies this service's connections in Kafka broker logs/metrics. Set to the cloned service's own name. |
| `TENANT_SCHEMA_PREFIX` | `tenant_` | Prefix for tenant PostgreSQL schemas. | Used to build tenant schema names, for example `tenant_acme`. |
| `SHARED_SCHEMA` | `shared` | PostgreSQL schema for platform-wide tables. | Used by Alembic, shared DB sessions, and schema translation for non-tenant data. |

### 3. Generate JWT keys (local dev only)

```bash
mkdir keys
openssl genrsa -out keys/private.pem 2048
openssl rsa -in keys/private.pem -pubout -out keys/public.pem
```

### 4. Run with Docker (recommended)

Once cloned into a real service, this template publishes audit events to a shared
Kafka broker owned by `auth-service`'s `docker-compose.yml`, connected over an
external Docker network that isn't created by any compose file. Create it once per
machine (safe to re-run):

```bash
docker network create sgi-network
```

Start `auth-service` first (it owns the broker container), then this service:

```bash
docker compose up --build
```

### 5. Run locally

```bash
uv run python -m app.main
```

The host and port are read from `.env`:

```env
APP_HOST=0.0.0.0
APP_PORT=8000
```

API available at `http://localhost:${APP_PORT}`
Swagger docs available at `http://localhost:${APP_PORT}/docs` when `APP_DOCS_ENABLED=true`

---

## Development Commands

### Lint, format, and type-check

```bash
uv run ruff check src tests
uv run ruff format src tests
uv run mypy src
```

### Run tests

```bash
uv run pytest                        # all tests
uv run pytest tests/unit -q          # unit tests only (fast, no DB)
uv run pytest tests/integration      # integration tests (spins Postgres testcontainer)
uv run pytest -k golden              # golden-master tests
```

### Coverage report

```bash
uv run pytest --cov=app --cov-report=html
open htmlcov/index.html
```

---

## Database & Migrations

This service supports schema-based multi-tenancy:

- `SHARED_SCHEMA` stores platform-wide tables shared across tenants.
- Tenant schemas use `TENANT_SCHEMA_PREFIX`, for example `tenant_acme`.
- Alembic receives the target schema through `-x schema=<schema_name>`.

### Apply migrations to the shared schema

Use this for local setup and platform-wide tables. When `-x schema=...` is omitted,
Alembic defaults to `SHARED_SCHEMA`.

```bash
uv run alembic upgrade head
```

Equivalent explicit command:

```bash
uv run alembic upgrade head -x schema=shared
```

### Generate a new migration

Creates a new Alembic revision from model changes. Review the generated file before
running it, especially when adding tenant-scoped tables.

```bash
uv run alembic revision --autogenerate -m "describe your change"
```

### Roll back the shared schema by one migration

Use this only when you need to undo the most recent migration in `SHARED_SCHEMA`.

```bash
uv run alembic downgrade -1
```

Equivalent explicit command:

```bash
uv run alembic downgrade -1 -x schema=shared
```

### Provision a new tenant schema

Creates a schema named from `TENANT_SCHEMA_PREFIX` plus the tenant slug, then runs
all migrations for that tenant.

```bash
uv run python scripts/provision_tenant.py <tenant-slug>
```

Example:

```bash
uv run python scripts/provision_tenant.py acme
```

With `TENANT_SCHEMA_PREFIX=tenant_`, this creates and migrates `tenant_acme`.

### Apply migrations to one tenant schema

Use this when only one tenant needs to be moved to a revision. Pass the real
PostgreSQL schema name, not just the tenant slug.

```bash
uv run alembic upgrade head -x schema=tenant_acme
```

Run one specific revision for one tenant:

```bash
uv run alembic upgrade a1b2c3d4e5f6 -x schema=tenant_acme
```

Roll back one migration for one tenant:

```bash
uv run alembic downgrade -1 -x schema=tenant_acme
```

### Migrate all tenant schemas + shared

Runs the same Alembic command for `SHARED_SCHEMA` and every existing tenant schema
whose name starts with `TENANT_SCHEMA_PREFIX`. Use this after a migration should
be applied across the whole deployment.

```bash
uv run python scripts/migrate_tenants.py upgrade
uv run python scripts/migrate_tenants.py downgrade -1
```

Upgrade all schemas to a specific revision:

```bash
uv run python scripts/migrate_tenants.py upgrade a1b2c3d4e5f6
```

---

## Messages and Translations

API message keys are managed centrally in [src/app/core/messages.py](src/app/core/messages.py),
and English message text lives in [src/app/i18n/locales/en.json](src/app/i18n/locales/en.json).
English (`en`) is the primary and only locale included right now.

Use constants from `core/messages.py` instead of hard-coded user-facing strings:

```python
from app.core.exceptions import NotFoundError
from app.core.messages import ExampleMsg

raise NotFoundError(ExampleMsg.NOT_FOUND, item_id=item_id)
```

The exception handler treats the exception message as a translation key. It
translates the key using the request language, interpolates keyword arguments,
and returns the translated text:

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "ExampleItem 123 not found",
    "details": []
  }
}
```

For normal API responses, call `t()` when constructing the response:

```python
from app.core.messages import HealthMsg
from app.i18n import t

return {"status": t(HealthMsg.OK)}
```

Clients can request a language with `Accept-Language`:

```http
Accept-Language: en-US
```

`LanguageMiddleware` stores the active request language in a context variable so
service-layer code can call `t()` without receiving the request object. Missing
locale files or missing keys fall back to English, then to the key itself.

To add a new message:

1. Add a namespaced constant to [src/app/core/messages.py](src/app/core/messages.py), for example `example.created`.
2. Add the English text to [src/app/i18n/locales/en.json](src/app/i18n/locales/en.json).
3. Use the constant in exceptions or response builders.

---

## Project Structure

```
src/app/
├── main.py                   # App factory: middleware, routers, lifespan
├── core/                     # Config, logging, telemetry, security, tenancy, middleware, exceptions
├── i18n/                     # Locale catalogs and translation helpers
├── db/                       # DeclarativeBase, mixins, async session factory
├── api/
│   ├── deps.py               # Shared FastAPI dependencies (get_db, get_current_user)
│   └── v1/
│       ├── router.py         # Includes all domain routers
│       └── routes/health.py  # /health and /ready endpoints
├── domains/                  # One folder per bounded context
│   └── example/              # Reference domain: models, schemas, repository, service, router
└── kafka/                    # Kafka producer + topic constants (app/core/audit_client.py publishes audit events here)

tests/
├── conftest.py               # Fixtures: testcontainer DB, async client, fake user
├── unit/                     # Pure logic tests, no DB
├── integration/              # Real Postgres via testcontainers
└── golden/                   # Fixed-input / fixed-output tests for calculations
```

---

## Adding a New Domain

1. Create `src/app/domains/<name>/` with five files: `models.py`, `schemas.py`, `repository.py`, `service.py`, `router.py`
2. Wire the router into [src/app/api/v1/router.py](src/app/api/v1/router.py)
3. Register models in [alembic/env.py](alembic/env.py)
4. Generate and apply a migration
5. Add unit tests (service) and integration tests (router)

---

## Health Endpoints

| Endpoint  | Auth | Purpose                        |
|-----------|------|--------------------------------|
| `GET /api/v1/health` | None | Liveness — process is up |
| `GET /api/v1/ready`  | None | Readiness — DB connection ok |
| `GET /metrics` | None | Prometheus scrape endpoint for process/runtime and OpenTelemetry metrics |

### Prometheus scrape config

For a locally running service on `APP_PORT=8000`, add a scrape job like this to
your Prometheus config:

```yaml
scrape_configs:
  - job_name: "sgi-base-service"
    metrics_path: "/metrics"
    static_configs:
      - targets: ["localhost:8000"]
```

The service records HTTP request count and duration as OpenTelemetry metric
instruments, which are exported in Prometheus format at `/metrics`.

### Jaeger tracing

Prometheus shows metrics only. To see traces, run a collector/backend such as
Jaeger and set a non-local environment:

```env
APP_ENV=dev
OTLP_ENDPOINT=http://localhost:4317
OTEL_SERVICE_NAME=sgi-backend
```

Then start Jaeger locally:

```bash
docker run --rm \
  --name jaeger \
  -p 16686:16686 \
  -p 4317:4317 \
  -p 4318:4318 \
  jaegertracing/all-in-one:latest
```

Open `http://localhost:16686`, select `sgi-backend`, and click **Find Traces**.

---

## Tech Stack

| Concern | Choice |
|---|---|
| Language | Python 3.12+ |
| Framework | FastAPI |
| ORM | SQLAlchemy 2.0 async |
| Migrations | Alembic |
| Validation | Pydantic v2 |
| Database | PostgreSQL 16 |
| Cache | Redis |
| Event streaming | Kafka (aiokafka) |
| Auth | JWT RS256 |
| Logging | structlog |
| Tracing | OpenTelemetry → OTLP |
| Dep management | uv |
| Lint / format | ruff |
| Type checking | mypy --strict |
| Tests | pytest + testcontainers |
#   b a s e _ a r c h _ p r o d u c t i o n _ f a s t _ a p i  
 