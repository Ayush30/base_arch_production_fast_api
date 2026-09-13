# Learning path for a React Native developer

[Project home](../README.md) · [Code index](CODE_INDEX.md)

You already understand the consumer side: a screen sends JSON, receives JSON, shows loading/error states, and stores credentials. This project implements the server on the other side of that request.

## Start the project before reading the code

Open Docker Desktop, then run these commands in the repository root:

```bash
make setup   # Install dependencies; create missing local configuration and keys
make up      # Build/start PostgreSQL, Redis, migrations, API and reservation worker
make seed    # Create the separate demo accounts and products
make demo    # Run a buyer checkout and simulated payment
```

Open [Swagger](http://localhost:8000/docs), then use the [role credentials](../README.md). `make logs` shows what the server does; `make down` stops the project while preserving database volumes. Follow the [Docker command guide](DOCKER.md) for prerequisites, troubleshooting, Kafka, monitoring, and load balancing.

## Read in this order

1. **Run and explore:** follow the root README, log in with each demo account, and try `/auth/me`. Notice that a finance token cannot use seller APIs. Read [API reference](API_REFERENCE.md).
2. **Trace one request:** read [REQUEST_WALKTHROUGH.md](REQUEST_WALKTHROUGH.md). Start at `catalog/router.py`, then `service.py`, `repository.py`, and `models.py`. A router resembles a screen's event handler; a service resembles reusable application logic. The database persists data across process restarts.
3. **Understand data shapes:** compare `catalog/schemas.py` and `catalog/models.py`. A Pydantic schema describes an API input/output contract (similar to a TypeScript interface with runtime validation). A SQLAlchemy model describes a database table. They are deliberately separate: password hashes belong in storage but never in API responses.
4. **Understand authentication:** follow `identity/router.py` → `identity/service.py` → `core/security.py` and `api/deps.py`. A signed JWT proves who issued a token; database session checks decide whether it is still allowed. Read the glossary entries for authentication, authorization, RBAC and ownership.
5. **Understand transactions:** study checkout and its tests. First read `orders/service.py::checkout`, then the two concurrency tests in `test_marketplace.py`. A database transaction means the order, stock changes, cart clearing and outbox either all commit or all roll back.
6. **Understand state transitions:** a pending order can be paid or cancelled. A paid item's fulfillment moves from unfulfilled to shipped to delivered. A return/refund has additional rules; it is not an arbitrary status edit.
7. **Understand asynchronous work:** events are saved with orders; a worker publishes them later. Follow `events/service.py` and `workers/outbox.py`. Read [EVENTS.md](EVENTS.md).
8. **Understand operations:** run a migration, inspect logs/correlation IDs, run tests, and try the balancing lab. Read [DEPLOYMENT.md](DEPLOYMENT.md). An application being correct locally and an operated production service are separate achievements.

Suggested exercises: add a product brand field with a migration; add a category filter test; add EUR-priced products and prove a mixed-currency cart is rejected; add a per-item return design before changing refund code. Keep each exercise small, run checks, and trace how its data crosses layers.

When adding a feature, ask: Who is allowed? Which records do they own? What needs to commit together? Can the phone retry? What happens if two requests arrive simultaneously? What should be stored, logged, or excluded from responses?
