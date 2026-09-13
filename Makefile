# Run from the repository root. See docs/DOCKER.md for the underlying commands.
UV ?= $(if $(wildcard .venv/bin/uv),.venv/bin/uv,uv)
export LOCAL_UID ?= $(shell id -u)
export LOCAL_GID ?= $(shell id -g)
COMPOSE = docker compose -f docker-compose.yml
BALANCED = $(COMPOSE) -f docker-compose.balance.yml
ALL = $(BALANCED) --profile events --profile observability
WAIT_TIMEOUT ?= 120

.PHONY: help setup config up seed demo logs ps shell migrate events observe balance all down test check

help:
	@printf '%s\n' \
	  'First run: make setup && make up && make seed' \
	  'make up       Build/start the core stack and wait for readiness' \
	  'make seed     Create missing demo accounts/products (local only)' \
	  'make demo     Create a demo order through the running API' \
	  'make ps       Show all services, including completed migrations' \
	  'make logs     Follow API, migration and reservation-worker logs' \
	  'make shell    Open a shell in the running API container' \
	  'make migrate  Apply migrations to the running database' \
	  'make events   Start the core stack plus Kafka/outbox' \
	  'make observe  Start the core stack plus Prometheus/Jaeger' \
	  'make balance  Start two API instances behind Nginx' \
	  'make all      Start every local lab service' \
	  'make down     Remove project containers/networks; keep database volumes' \
	  'make config   Validate all Compose configurations' \
	  'make check    Run lint, format, type and documentation checks' \
	  'make test     Run the full test suite (host development dependencies)'

setup:
	$(UV) sync --frozen
	$(UV) run python scripts/dev_setup.py

config:
	$(COMPOSE) config --quiet
	$(ALL) config --quiet

up:
	$(COMPOSE) up --build --wait --wait-timeout $(WAIT_TIMEOUT)

seed:
	$(COMPOSE) exec app python scripts/seed.py

demo:
	$(COMPOSE) exec app python scripts/demo_journey.py --base-url http://127.0.0.1:8000

ps:
	$(ALL) ps --all

logs:
	$(COMPOSE) logs --follow --tail 100 app migrate reservations

shell:
	$(COMPOSE) exec app sh

migrate:
	$(COMPOSE) exec app alembic upgrade head

events:
	$(COMPOSE) --profile events up --build --wait --wait-timeout $(WAIT_TIMEOUT)

observe:
	$(COMPOSE) --profile observability up --build --wait --wait-timeout $(WAIT_TIMEOUT)

balance:
	$(BALANCED) up --build --wait --wait-timeout $(WAIT_TIMEOUT)

all:
	$(ALL) up --build --wait --wait-timeout $(WAIT_TIMEOUT)

down:
	$(ALL) down

check:
	$(UV) run ruff check src tests scripts alembic
	$(UV) run ruff format --check src tests scripts alembic
	$(UV) run mypy src
	$(UV) run python scripts/check_docs.py

test:
	$(UV) run pytest
