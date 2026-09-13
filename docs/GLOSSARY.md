# Backend terminology, with code references

[Learning path](LEARNING_PATH.md) · [Code index](CODE_INDEX.md)

| Term | Meaning in this project | Where to look |
|---|---|---|
| API endpoint / route | HTTP method plus URL, such as POST /checkout | domains/*/router.py |
| REST | Resource-oriented HTTP conventions; this API also has action endpoints for state transitions | api/v1/router.py |
| Request/response schema | Runtime-validated JSON contract, similar to a TypeScript type plus validation | domains/*/schemas.py |
| Model / entity | Python class mapped to a persisted database table | domains/*/models.py |
| ORM | Object-relational mapper; SQLAlchemy turns Python queries into SQL | domains/*/repository.py |
| Repository | Focused database queries; complex aggregate SQL also lives here | catalog/repository.py |
| Service layer | Business rules, authorization context, transaction orchestration | orders/service.py |
| Dependency injection | Framework supplies dependencies such as DB session and current user | api/deps.py |
| Middleware | Code around requests/responses for logging, language and correlation IDs | core/middleware.py |
| Authentication | Establishing who the request represents | core/security.py, identity/service.py |
| Authorization | Deciding which actions and records that actor can access | api/deps.py, ownership checks |
| RBAC | Role-based access control: buyer, seller, finance, analytics, admin | api/deps.py |
| Ownership / object authorization | A seller role alone cannot edit another seller's product | catalog/service.py |
| JWT | Signed claims with expiry, issuer, audience and session ID; not encrypted | core/security.py |
| Access token | Short-lived bearer credential used on API calls | identity/schemas.py |
| Refresh token | High-entropy credential exchanged for a new session; stored hashed server-side | identity/service.py |
| Rotation / revocation | Replace a credential / invalidate an existing session | identity/service.py |
| Hashing / salt | One-way password verification with a per-hash random salt; Argon2 manages it | core/security.py |
| Primary key / UUID | Stable unique row identity | db/record.py |
| Foreign key | Database-enforced reference to another row | orders/models.py |
| Unique constraint | Database rule preventing duplicate identity, checkout keys or payments | models.py files |
| Index | Data structure speeding lookup, at a cost to writes/storage | models.py index=True |
| Migration / DDL | Versioned change to the database structure | alembic/versions/ |
| DML | Inserts, updates and deletes of data rather than schema | service/repository modules |
| Transaction / ACID | Changes commit together or roll back; database consistency and durability rules | db/session.py, orders/service.py |
| Commit / rollback | Persist transaction changes / discard uncommitted changes | service.py, db/session.py |
| Flush | Send pending ORM changes to DB without committing | identity/service.py |
| Isolation | What concurrent transactions can observe; PostgreSQL default is READ COMMITTED here | checkout tests |
| Row lock / pessimistic locking | Prevent conflicting updates while a transaction checks and changes a row | with_for_update() |
| Optimistic concurrency | Client supplies a version; stale edits are rejected | ProductUpdate, catalog/service.py |
| Deadlock | Transactions wait on each other's locks; consistent lock ordering reduces risk | orders/service.py |
| Idempotency | Repeating the same operation does not repeat its effect | checkout and payment services |
| Race condition | Outcome depends on interleaving concurrent operations | test_checkout_race_never_oversells |
| Reservation | Stock held temporarily for an unpaid order | workers/reservations.py |
| State machine | Allowed transitions instead of freely editable status strings | orders/service.py |
| Snapshot | Copy of data at purchase time so later product/address edits cannot rewrite history | Order / OrderItem |
| Minor unit / basis point | Currency's integer subdivision / one hundredth of one percent | core/money.py |
| Ledger / settlement | Money transaction journal / recording seller proceeds transferred elsewhere | finance/ |
| Modular monolith | One deployable application split into business modules | domains/ |
| Bounded context | Business area with its own concepts and rules, such as catalog or finance | domains/ |
| Multi-tenancy | Several customer organizations sharing infrastructure; not the same as seller ownership | core/tenancy.py (template reference) |
| Async / await | Lets the event loop serve other work while waiting for I/O | async service functions |
| Event loop | Scheduler for async tasks; CPU-heavy work can block it | identity hashing uses threadpool |
| Connection pool | Reusable DB connections, with bounded size | db/session.py |
| Read replica / replication lag | Copy for reads / delay before committed changes arrive | db/session.py |
| Outbox pattern | Save a business event in the same transaction as its data change | events/service.py |
| Producer / consumer / broker | Sends events / processes events / stores and transports events | kafka/, workers/outbox.py |
| Topic / partition / offset | Named stream / ordered subdivision / consumer position in it | docs/EVENTS.md |
| At-least-once delivery | Event is retried and can arrive multiple times | workers/outbox.py |
| Deduplication | Remember processed event IDs to avoid repeating side effects | docs/EVENTS.md |
| Backpressure / retry | Limit work under load / attempt transient failures again | pools, rate limits, workers |
| Dead-letter queue | Quarantine events needing intervention; extension, not implemented | docs/EVENTS.md |
| Webhook | Provider's server-to-server HTTP notification; live integration not implemented | docs/MONEY_AND_PAYMENTS.md |
| Reverse proxy / load balancer | Front server forwarding requests / distributing them across replicas | deploy/nginx/ |
| Horizontal scaling | Add application instances rather than making one instance larger | docker-compose.balance.yml |
| Stateless API | Replicas keep shared durable state outside their local process | PostgreSQL sessions, Redis limits |
| Liveness / readiness | Process responds / selected dependencies are reachable | api/v1/routes/health.py |
| Observability | Logs, metrics and traces explain system behavior | core/telemetry.py |
| Correlation ID / trace | Request identifier / linked spans describing work across services | middleware.py, telemetry.py |
| p95 / p99 latency | Time within which 95% / 99% of requests complete | docs/DEPLOYMENT.md |
| CI/CD | Automated verification / delivery pipeline | .github/workflows/ci.yml |
| Secret management | Store keys/passwords outside source and images | .env.example, scripts/dev_setup.py |
| CORS | Browser rules for cross-origin requests, not API authorization | main.py |
| RPO / RTO / PITR | Acceptable data-loss window / recovery time / point-in-time database recovery | docs/DEPLOYMENT.md |
