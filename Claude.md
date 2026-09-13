# CLAUDE.md

## Database Session Pattern

The service uses two SQLAlchemy async engines from `src/app/db/session.py`:

- `engine` is the primary/write engine. It always uses `DATABASE_URL`.
- `read_engine` uses `DATABASE_READ_REPLICA_URL` when that value is set.
- When `DATABASE_READ_REPLICA_URL` is empty, `read_engine` is the same object as `engine`, so read sessions fall back to the primary with no behavior change.

Use the FastAPI dependency aliases from `src/app/api/deps.py`:

- `DbSession` for commands, mutations, transactions, or reads that must observe recent writes.
- `ReadDbSession` for read-only routes that can be served from a replica.

Both session types apply `schema_translate_map` for the current tenant schema and map `"shared"` to `SHARED_SCHEMA`.

Use `shared_session()` only for code that does not have tenant context, such as service startup, seed data, tenant provisioning, and background jobs that operate on shared tables. It always uses the primary/write engine.

Application shutdown must call `dispose_engines()` instead of disposing `engine` directly. This closes the primary pool and the replica pool when a separate read replica is configured.

Pool settings are managed with:

- `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_TIMEOUT`, `DB_POOL_RECYCLE`
- `DB_READ_POOL_SIZE`, `DB_READ_MAX_OVERFLOW`, `DB_READ_POOL_TIMEOUT`, `DB_READ_POOL_RECYCLE`

Keep write and read pool sizes independent. Read replicas often need different limits than the primary because traffic shape and database capacity differ.
