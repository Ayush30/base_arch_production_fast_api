# Configuration reference

Settings are read from environment variables and `.env` by [core/config.py](../src/app/core/config.py). Environment variables take precedence. Lists use JSON arrays. See [.env.example](../.env.example) for the recommended local configuration and [deployment](DEPLOYMENT.md) for production restrictions.

The defaults below come from the model definition, not from your secret environment. DB URLs and key paths must be configured for the execution environment (host versus container).

| Environment variable | Model default |
|---|---|
| `APP_ENV` | `local` |
| `APP_NAME` | `marketplace-backend` |
| `APP_VERSION` | `0.1.0` |
| `APP_HOST` | `0.0.0.0` |
| `APP_PORT` | `8000` |
| `APP_DOCS_ENABLED` | `True` |
| `APP_DEBUG` | `False` |
| `DATABASE_URL` | `postgresql+asyncpg://marketplace:marketplace@localhost:5432/marketplace` |
| `DB_POOL_SIZE` | `10` |
| `DB_MAX_OVERFLOW` | `20` |
| `DB_POOL_TIMEOUT` | `30` |
| `DB_POOL_RECYCLE` | `3600` |
| `DATABASE_READ_REPLICA_URL` | `` |
| `DB_READ_POOL_SIZE` | `10` |
| `DB_READ_MAX_OVERFLOW` | `20` |
| `DB_READ_POOL_TIMEOUT` | `30` |
| `DB_READ_POOL_RECYCLE` | `3600` |
| `REDIS_URL` | `redis://localhost:6379/0` |
| `JWT_ALGORITHM` | `RS256` |
| `JWT_PUBLIC_KEY_PATH` | `keys/public.pem` |
| `JWT_PRIVATE_KEY_PATH` | `keys/private.pem` |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `60` |
| `OTLP_ENDPOINT` | `http://localhost:4317` |
| `OTEL_SERVICE_NAME` | `marketplace-backend` |
| `METRICS_ENABLED` | `True` |
| `METRICS_PATH` | `/metrics` |
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` |
| `KAFKA_CLIENT_ID` | `marketplace-backend` |
| `JWT_ISSUER` | `marketplace` |
| `JWT_AUDIENCE` | `marketplace-mobile` |
| `REFRESH_TOKEN_DAYS` | `30` |
| `LOCAL_PAYMENTS_ENABLED` | `True` |
| `LOCAL_EMAIL_TOKENS_ENABLED` | `True` |
| `AUTH_RATE_LIMIT` | `20` |
| `RATE_LIMIT_ENABLED` | `True` |
| `KAFKA_ENABLED` | `False` |
| `CORS_ORIGINS` | `[]` |
| `ALLOWED_HOSTS` | `['localhost', '127.0.0.1', 'testserver', 'test']` |
| `SUPPORTED_CURRENCIES` | `['USD']` |
| `COMMISSION_BPS` | `1000` |
| `CHECKOUT_EXPIRY_MINUTES` | `30` |
| `TENANT_SCHEMA_PREFIX` | `tenant_` |
| `SHARED_SCHEMA` | `shared` |

`APP_PORT` controls host Python binding and Docker's published host port; the image listens on 8000. `LOCAL_UID`/`LOCAL_GID` are Compose-only local key-file permissions, not application settings. `POSTGRES_PORT`, `REDIS_PORT` and `PROXY_PORT` are Compose host port overrides. `DOCKER_OTLP_ENDPOINT` optionally overrides the container trace collector (default http://jaeger:4317); host Python still uses `OTLP_ENDPOINT`. See [Docker commands](DOCKER.md). Legacy TENANT_SCHEMA_PREFIX is not used to isolate sellers.
