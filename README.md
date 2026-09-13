# Marketplace backend — learn by following a real request

A FastAPI backend for a physical-product marketplace, designed as a long-term reference for a React Native developer learning backend engineering. It uses the original template's router → service → repository pattern, async SQLAlchemy, PostgreSQL, Alembic, structured logging, and monitoring.

**Start reading:** [Learning path](docs/LEARNING_PATH.md) · [Complete code index](docs/CODE_INDEX.md) · [API reference](docs/API_REFERENCE.md) · [Backend glossary](docs/GLOSSARY.md) · [React Native integration](docs/REACT_NATIVE.md).

## What is implemented

| Role | Capabilities |
|---|---|
| Public | Browse/search/filter products and read reviews; register as buyer or seller |
| Buyer | Login, verify email, addresses, cart, checkout, pay locally, order history, cancel unpaid orders, request a full return, review delivered purchases |
| Seller | Approved sellers manage their own products and stock, fulfill their own order items, view their sales and settlements |
| Finance | Inspect payments, returns and ledger, simulate full refunds after goods receipt, record externally completed seller settlements |
| Analytics | Read aggregate sales/product/seller reports without buyer emails or addresses |
| Admin | Approve sellers, disable users, moderate products, inspect audit records |

Money uses integer minor units, with USD enabled by default. For example, `1999` means $19.99. Orders contain exactly one currency; reports never combine currencies. [Currency extension design](docs/MONEY_AND_PAYMENTS.md).

This is a runnable reference implementation with production-oriented controls, **not a finished live-commerce deployment**. Payments/refunds are simulated; email tokens are exposed only by the local development adapter. Shipping is manual tracking, returns are full-order only, and settlement records do not transfer funds. Tax calculation, shipping rates, live payment/email providers and production infrastructure must be integrated before real orders. Production configuration refuses unsafe local adapters. See [deployment and readiness](docs/DEPLOYMENT.md) for the concrete remaining work.

## Run locally with Docker

From the repository root, the shortest path on macOS/Linux is:

```bash
make setup
make up
make seed
make demo
```

`make setup` uses `.venv/bin/uv` when present, otherwise `uv` from your PATH. Docker Desktop must be running. `make up` waits for service readiness; an exited `migrate` container with code 0 is expected.

**Full command guide:** [Docker setup, daily commands, Kafka, monitoring and load balancing](docs/DOCKER.md). Run `make help` to list shortcuts.

Requirements: Python 3.12+, `uv`, and Docker Desktop with Compose v2. Install uv using its [official installation guide](https://docs.astral.sh/uv/getting-started/installation/).

```bash
uv sync --frozen
uv run python scripts/dev_setup.py
# macOS/Linux: allows the containers to read your private key with its 0600 permissions.
export LOCAL_UID=$(id -u)
export LOCAL_GID=$(id -g)
docker compose up --build --wait --wait-timeout 120
docker compose exec app python scripts/seed.py
```

`dev_setup.py` creates `.env` and RSA keys only if missing. Compose starts PostgreSQL, Redis, migrations, the API, and the reservation-expiry worker. It does not depend on another repository. On Windows Docker Desktop, use the default container UID if the bind-mounted key is readable; otherwise use WSL and the commands above.

Open [Swagger API explorer](http://localhost:8000/docs). Click an endpoint, select **Try it out**, and execute it. `POST /api/v1/auth/login` returns an access token; paste just that token into Swagger's **Authorize** dialog.

| Email | Local password | Role |
|---|---|---|
| buyer@example.com | Buyer-Demo-2026! | Buyer |
| seller@example.com | Seller-Demo-2026! | Approved seller |
| finance@example.com | Finance-Demo-2026! | Finance |
| analytics@example.com | Analytics-Demo-2026! | Analytics |
| admin@example.com | Admin-Demo-2026! | Administrator |

These demo accounts are already email verified. Seeding is idempotent: rerunning it does not reset passwords, existing inventory, or orders. The script refuses to run outside `APP_ENV=local`.

Check `docker compose logs app migrate reservations` if startup fails. Stop with `docker compose down`; the database volume persists. Removing volumes deletes stored data, so do that only for a disposable environment.

## Run Python on your host

```bash
docker compose up -d db redis
uv run alembic upgrade head
uv run python scripts/seed.py
uv run python -m app.main
# In another terminal:
uv run python -m app.workers.reservations
```

The host app reads `.env` and uses port 8000 by default. Docker always serves container port 8000 and maps your `APP_PORT` to it. Set `POSTGRES_PORT`/`REDIS_PORT` for port conflicts and update host URLs in `.env` accordingly.

## Try a full buyer journey

```bash
uv run python scripts/demo_journey.py
```

This logs into the seeded buyer account, adds one seeded product, creates an idempotent checkout, simulates payment, and prints the order ID. It creates a real local order and reduces local stock. For fulfillment, returns and staff operations, follow [the request walkthrough](docs/REQUEST_WALKTHROUGH.md).

## Checks

```bash
uv run ruff check src tests scripts alembic
uv run ruff format --check src tests scripts alembic
uv run mypy src
uv run python scripts/check_docs.py
uv run pytest
```

Integration tests start disposable PostgreSQL 16 through Testcontainers by default. Alternatively set `TEST_DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/test_database`. Each test creates and drops its own random schema; use a dedicated test database. Test requests use actual signed tokens and independent database transactions. See [testing](docs/TESTING.md) and the [verification record](docs/VERIFICATION.md).

## Learning infrastructure

```bash
# Durable events are already written to PostgreSQL; this starts Kafka and publishes them.
docker compose --profile events up -d
# Optional metrics and trace UI:
docker compose --profile observability up -d
# Two API instances behind Nginx at http://localhost:8080:
docker compose -f docker-compose.yml -f docker-compose.balance.yml up --build -d
```

The balancing lab requires Compose support for `!reset`. The direct API remains at port 8000. Nginx uses two explicitly named replicas for a reproducible local demonstration. Read [Kafka and background work](docs/EVENTS.md) and [deployment/load balancing](docs/DEPLOYMENT.md) before adapting these files to a server.

## Navigation

Every maintained folder has a `README.md` explaining its responsibility, files, dependencies, and relevant backend terms. Generated folders such as `.venv`, caches, `.git`, and secret keys are excluded. The [code index](docs/CODE_INDEX.md) links every maintained file and lists Python classes/functions. The [documentation generator](scripts/generate_docs.py) keeps these maps aligned with code.

## Development instructions

Read [Claude.md](Claude.md) before making changes. It documents the architecture, permissions, transaction rules, local workflow and required checks.

Every change must update the relevant READMEs and explain why it was made, including affected behavior and connections to other modules. This requirement keeps the project useful as a long-term learning reference and prevents setup instructions and code explanations from drifting away from the implementation. Final change summaries must identify the updated documentation and report what was actually verified.

For generated folder READMEs, edit the descriptions in [scripts/generate_docs.py](scripts/generate_docs.py) and regenerate them; edit this root README and handwritten guides directly. Run `.venv/bin/python scripts/check_docs.py` to check folder coverage and local links.
