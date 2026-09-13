# Docker setup and running commands

[Project home](../README.md) · [Learning path](LEARNING_PATH.md) · [Server deployment](DEPLOYMENT.md)

Run commands from the repository root (the folder containing `docker-compose.yml`). The shortcuts below work on macOS/Linux or WSL. Open Docker Desktop first.

## 1. Check prerequisites

```bash
docker --version
docker compose version
docker info
make --version
```

Use Docker Compose 2.24.4 or later, including support for `!reset` in the balancing override. `docker info` must connect to a running engine. Install Python 3.12+ and uv for host development; if this checkout already has `.venv/bin/uv`, the Makefile uses it automatically. Otherwise install uv from its [official instructions](https://docs.astral.sh/uv/getting-started/installation/).

## 2. First run — recommended

```bash
make setup
make config
make up
make seed
make demo
```

| Command | What it does |
|---|---|
| `make setup` | Installs locked dependencies, creates missing `.env` and RSA signing keys. Existing configuration and keys are preserved. |
| `make config` | Validates both the base and complete lab Compose configurations without printing environment values. |
| `make up` | Builds images and starts PostgreSQL, Redis, migrations, API and reservation worker. Waits up to 120 seconds for startup/readiness after the build. |
| `make seed` | Runs the local seed inside the running API container. Creates missing role accounts, sample products and a buyer address. |
| `make demo` | Calls the running API from inside its container; creates a buyer order and simulates payment. Requires an empty demo buyer cart. |

The Makefile supplies your local user/group IDs so containers can read the private key without making it world-readable. Run `make up WAIT_TIMEOUT=240` if startup needs a longer wait.

Open [Swagger](http://localhost:8000/docs). Login with a [demo role account](../README.md), copy its access token, and click **Authorize**. For example: `buyer@example.com` / `Buyer-Demo-2026!`.

```bash
curl --fail http://localhost:8000/api/v1/health
curl --fail http://localhost:8000/api/v1/ready
make ps
```

Expected: `app`, `db`, and `redis` are healthy; `reservations` is running; `migrate` is exited with code 0. Migration is a one-time job, so its successful exit is normal. Compose waits for healthy dependencies and completed migrations before starting the API. See [Docker startup ordering](https://docs.docker.com/compose/how-tos/startup-order/).

## Equivalent commands without Make

If uv is only inside `.venv`, activate it first with `source .venv/bin/activate`.

```bash
uv sync --frozen
uv run python scripts/dev_setup.py
export LOCAL_UID=$(id -u)
export LOCAL_GID=$(id -g)
docker compose config --quiet
docker compose up --build --wait --wait-timeout 120
docker compose exec app python scripts/seed.py
docker compose exec app python scripts/demo_journey.py --base-url http://127.0.0.1:8000
```

Repeat the two `export` commands in each new terminal when using raw Compose commands. Make handles them for every invocation. `--wait` runs containers in the background and waits for their running/healthy state; it does not prove Kafka delivery or a complete business flow is healthy. See [Compose up](https://docs.docker.com/reference/cli/docker/compose/up/).

### Alternative: Docker only, without installing host Python or uv

The image contains Python and all runtime dependencies. Use it to generate the local files in the mounted workspace:

```bash
export LOCAL_UID=$(id -u)
export LOCAL_GID=$(id -g)
docker build -t marketplace-local .
docker run --rm \
  --user "$LOCAL_UID:$LOCAL_GID" \
  --volume "$PWD:/workspace" \
  --workdir /workspace \
  marketplace-local python scripts/dev_setup.py
docker compose up --build --wait --wait-timeout 120
docker compose exec app python scripts/seed.py
```

This bind mount lets `dev_setup.py` write `.env` and `keys/` into your checkout. You still need host development dependencies for the full test/lint workflow; the runtime image deliberately excludes them.

## 3. Daily commands

```bash
make help                  # List shortcuts
make up                    # Start again, or rebuild after source/dependency changes
make ps                    # Include the completed migration job in the status display
make logs                  # Follow API/migration/reservation logs; Ctrl+C stops log viewing
make shell                 # Open an API-container shell; type exit to leave it
make migrate               # Apply migrations using the running image
make seed                  # Safe to rerun; does not reset existing passwords or stock
make down                  # Remove all project containers/networks; preserve named data volumes
```

Source is copied into the image; Docker is not configured for live Python reload. After editing Python or migrations, run `make up` to rebuild the core stack. If using all labs, use `make all` to rebuild/recreate all their processes together.

```bash
# Restart the existing API process without changing its configuration/image:
docker compose restart app
# Inspect migrations and database connectivity:
docker compose logs --tail 100 migrate
docker compose exec app alembic current
docker compose exec db psql -U marketplace -d marketplace
# Check Redis:
docker compose exec redis redis-cli ping
```

After changing `.env`, use `make up` (or the corresponding lab target) to recreate affected containers. A plain restart does **not** apply changed environment variables. See [Compose restart](https://docs.docker.com/reference/cli/docker/compose/restart/).

`make down` preserves PostgreSQL/Kafka named volumes and stops optional lab containers too. No automatic data-reset command is provided. `docker compose down --volumes` deletes stored database data and should only be used deliberately on disposable data.

## 4. Kafka events

```bash
make events
docker compose --profile events logs --follow --tail 100 kafka outbox
# In another terminal, inspect published events:
docker compose --profile events exec kafka /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka:9092 --topic marketplace.events --from-beginning
```

Run `make demo` to generate events. Without Kafka, committed events remain in PostgreSQL; the outbox worker publishes them when Kafka starts. The broker advertises `kafka:9092` on Docker's internal network and has no host port mapping. Run consumers inside Docker as shown; `localhost:9092` on your computer will not reach this broker. [Outbox and delivery explanation](EVENTS.md).

## 5. Monitoring and tracing

```bash
make observe
```

| URL | Purpose |
|---|---|
| [localhost:8000/metrics](http://localhost:8000/metrics) | Raw API metrics |
| [localhost:9090](http://localhost:9090) | Prometheus UI; inspect targets and query metrics |
| [localhost:16686](http://localhost:16686) | Jaeger trace UI |

Prometheus scrapes `app:8000/metrics`. Keep `METRICS_ENABLED=true` and `METRICS_PATH=/metrics` unless you also change its scrape configuration. The included scrape file targets only `app`, not both balancing replicas.

Starting Jaeger alone does not enable traces: trace export is disabled in `APP_ENV=local` and `test`. To explore traces, change `.env` to `APP_ENV=dev`, then run `make observe` again and make API requests. Compose routes exports to `http://jaeger:4317`; a custom container-reachable collector can be set with `DOCKER_OTLP_ENDPOINT`. Your host Python process still reads `OTLP_ENDPOINT` from `.env`.

The local payment and email-token endpoints, and demo seeding, require `APP_ENV=local`. Use `dev` for tracing exploration and switch back to `local` with `make up` for the complete simulated buyer journey. Do not expect `make demo` to simulate payment in `dev`.

## 6. Two API instances behind Nginx

```bash
make balance
curl --fail http://localhost:8080/api/v1/ready
# Use the environment created by make setup to run a buyer journey through Nginx:
.venv/bin/python scripts/demo_journey.py --base-url http://localhost:8080
```

[Swagger through Nginx](http://localhost:8080/docs) routes to `app` and `app2`. Both use the same PostgreSQL, Redis and keys. The direct API remains at port 8000. Use `make balance` instead of `--scale app=2`, since `app` publishes a fixed host port. The override removes the second API's host port to avoid a collision.

```bash
# Start everything: two APIs, Nginx, Kafka/outbox, Prometheus and Jaeger.
make all
# Stop every lab and the core stack, keeping named data volumes.
make down
```

## 7. Port conflicts and troubleshooting

To persist alternate ports, add/change these entries in `.env`:

```dotenv
APP_PORT=8001
POSTGRES_PORT=5433
REDIS_PORT=6380
PROXY_PORT=8081
```

Then run the relevant start target and visit `http://localhost:8001/docs` or `http://localhost:8081/docs`. Internal ports remain 8000, 5432, 6379 and 8080, so container connection URLs do not change. If running Python on the host instead, update its `DATABASE_URL`/`REDIS_URL` for the changed host ports. The Makefile's `make demo` runs inside the container and continues to use port 8000.

| Symptom | Check / action |
|---|---|
| Cannot connect to Docker daemon | Start Docker Desktop and rerun `docker info`. |
| `uv: command not found` | Use `make setup`, which detects `.venv/bin/uv`, or install uv if neither location has it. |
| Missing `.env` or signing keys | Run `make setup` or the Docker-only setup above. |
| Permission denied reading private key | Use Make, or export `LOCAL_UID`/`LOCAL_GID` from your current user before raw Compose commands. |
| API startup timed out | Run `make ps` and inspect `docker compose logs --tail 100 migrate app db redis`. Fix the reported dependency/configuration error before retrying. |
| `migrate` exited 0 | Expected: its schema update finished successfully. |
| Port already allocated | Change the host port as above; do not change internal service ports. |
| Jaeger UI is empty | Enable trace export with `APP_ENV=dev` and recreate the API; see the tracing section. |
| HTTP 400 Invalid host header | Add the hostname/IP you actually use to `ALLOWED_HOSTS`, then recreate the API. |
| HTTP 429 on authentication | Wait a minute; the local Redis auth limit is shared by callers from the same address. |
| Changes do not appear | Run `make up`/`make all`; source is copied into images and a restart does not rebuild them. |
| Cannot call API from a physical phone | Default ports bind to loopback only. Follow [React Native network setup](REACT_NATIVE.md). |

A Compose **service** is a named component such as `app`; an **image** packages code/dependencies; a **container** is an instance of that image; a **volume** keeps data outside container lifetimes; a **profile** enables optional services. More terms are in the [glossary](GLOSSARY.md).
