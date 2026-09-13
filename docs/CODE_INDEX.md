# Complete project code index

[Start learning](LEARNING_PATH.md) · [Request walkthrough](REQUEST_WALKTHROUGH.md) · [Glossary](GLOSSARY.md)

This map lists maintained files and top-level Python classes/functions. Each folder README explains responsibilities and relationships. Runtime files, secrets, virtual environments and caches are excluded. Regenerate after structural changes with `uv run python scripts/generate_docs.py`.

## .

Project entry points, packaging, local orchestration and orientation.

| File | Symbols / purpose |
|---|---|
| [.dockerignore](../.dockerignore) | Documentation, configuration or support file. |
| [.env.example](../.env.example) | Documentation, configuration or support file. |
| [.gitignore](../.gitignore) | Documentation, configuration or support file. |
| [Claude.md](../Claude.md) | Documentation, configuration or support file. |
| [Dockerfile](../Dockerfile) | Documentation, configuration or support file. |
| [Makefile](../Makefile) | Documentation, configuration or support file. |
| [README.md](../README.md) | This folder's purpose, file map and cross-references. |
| [alembic.ini](../alembic.ini) | Documentation, configuration or support file. |
| [docker-compose.balance.yml](../docker-compose.balance.yml) | Documentation, configuration or support file. |
| [docker-compose.yml](../docker-compose.yml) | Documentation, configuration or support file. |
| [pyproject.toml](../pyproject.toml) | Documentation, configuration or support file. |
| [uv.lock](../uv.lock) | Documentation, configuration or support file. |

## .github

Repository automation configuration; workflows run checks on pushes and pull requests.

| File | Symbols / purpose |
|---|---|
| [README.md](../.github/README.md) | This folder's purpose, file map and cross-references. |

## .github/workflows

CI pipeline: frozen dependency installation, lint, formatting, strict source typing, docs checks, real PostgreSQL tests and migration round-trip verification.

| File | Symbols / purpose |
|---|---|
| [README.md](../.github/workflows/README.md) | This folder's purpose, file map and cross-references. |
| [ci.yml](../.github/workflows/ci.yml) | Documentation, configuration or support file. |

## alembic

Database migration runner. env.py selects the configured marketplace schema and registers current models; versions contains frozen migration history. Runtime application startup does not call create_all.

| File | Symbols / purpose |
|---|---|
| [README.md](../alembic/README.md) | This folder's purpose, file map and cross-references. |
| [env.py](../alembic/env.py) | `configure`, `run_migrations`, `online` |
| [script.py.mako](../alembic/script.py.mako) | Documentation, configuration or support file. |

## alembic/versions

Versioned, reviewable database DDL. Upgrade creates tables/constraints/indexes; downgrade reverses them and can destroy data. Never rewrite a revision after deploying it.

| File | Symbols / purpose |
|---|---|
| [35db5a494cde_initial_marketplace_schema.py](../alembic/versions/35db5a494cde_initial_marketplace_schema.py) | `upgrade`, `downgrade` |
| [README.md](../alembic/versions/README.md) | This folder's purpose, file map and cross-references. |

## deploy

Local infrastructure teaching configurations. Nginx demonstrates two API replicas; Prometheus scrapes application metrics. These files need environment-specific security and availability work for production.

| File | Symbols / purpose |
|---|---|
| [README.md](../deploy/README.md) | This folder's purpose, file map and cross-references. |

## deploy/nginx

Reverse proxy and least-connections balancing lab. nginx.conf forwards to app/app2, limits authentication traffic and blocks public /metrics. Production requires HTTPS and a deliberate trusted-proxy policy.

| File | Symbols / purpose |
|---|---|
| [README.md](../deploy/nginx/README.md) | This folder's purpose, file map and cross-references. |
| [nginx.conf](../deploy/nginx/nginx.conf) | Documentation, configuration or support file. |

## deploy/prometheus

Prometheus scrape configuration. Targets app:8000/metrics on the internal Compose network. Use service discovery when replicas are dynamic.

| File | Symbols / purpose |
|---|---|
| [README.md](../deploy/prometheus/README.md) | This folder's purpose, file map and cross-references. |
| [prometheus.yml](../deploy/prometheus/prometheus.yml) | Documentation, configuration or support file. |

## docs

Learning curriculum, request traces, generated API/code/configuration indexes, backend glossary and deployment/integration boundaries. Start at LEARNING_PATH.md.

| File | Symbols / purpose |
|---|---|
| [API_REFERENCE.md](API_REFERENCE.md) | Documentation, configuration or support file. |
| [CODE_INDEX.md](CODE_INDEX.md) | Documentation, configuration or support file. |
| [CONFIGURATION.md](CONFIGURATION.md) | Documentation, configuration or support file. |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Documentation, configuration or support file. |
| [DOCKER.md](DOCKER.md) | Documentation, configuration or support file. |
| [EVENTS.md](EVENTS.md) | Documentation, configuration or support file. |
| [GLOSSARY.md](GLOSSARY.md) | Documentation, configuration or support file. |
| [LEARNING_PATH.md](LEARNING_PATH.md) | Documentation, configuration or support file. |
| [MONEY_AND_PAYMENTS.md](MONEY_AND_PAYMENTS.md) | Documentation, configuration or support file. |
| [REACT_NATIVE.md](REACT_NATIVE.md) | Documentation, configuration or support file. |
| [README.md](README.md) | This folder's purpose, file map and cross-references. |
| [REQUEST_WALKTHROUGH.md](REQUEST_WALKTHROUGH.md) | Documentation, configuration or support file. |
| [TESTING.md](TESTING.md) | Documentation, configuration or support file. |
| [VERIFICATION.md](VERIFICATION.md) | Documentation, configuration or support file. |

## scripts

Operational and teaching commands: local keys/configuration, idempotent demo seed, prompted staff provisioning, API demo journey, and documentation maintenance. Legacy tenant scripts are disabled to prevent confusing schema-per-tenant provisioning with sellers.

| File | Symbols / purpose |
|---|---|
| [README.md](../scripts/README.md) | This folder's purpose, file map and cross-references. |
| [check_docs.py](../scripts/check_docs.py) | `main` |
| [create_staff.py](../scripts/create_staff.py) | `create` |
| [demo_journey.py](../scripts/demo_journey.py) | `main` |
| [dev_setup.py](../scripts/dev_setup.py) | `main` |
| [generate_docs.py](../scripts/generate_docs.py) | `access_rule`, `maintained_files`, `symbols`, `relative`, `generate` |
| [migrate_tenants.py](../scripts/migrate_tenants.py) | Disabled legacy command; points to the shared Alembic migration chain. |
| [provision_tenant.py](../scripts/provision_tenant.py) | Disabled legacy command; points to marketplace seller registration. |
| [seed.py](../scripts/seed.py) | `seed` |

## src

Installable Python source tree. The app package is the server; it does not contain a mobile UI.

| File | Symbols / purpose |
|---|---|
| [README.md](../src/README.md) | This folder's purpose, file map and cross-references. |

## src/app

Application composition: main.py builds FastAPI, registers middleware and routers, and manages startup/shutdown.

| File | Symbols / purpose |
|---|---|
| [README.md](../src/app/README.md) | This folder's purpose, file map and cross-references. |
| [__init__.py](../src/app/__init__.py) | Python package marker (some packages also expose helper functions). |
| [main.py](../src/app/main.py) | `lifespan`, `create_app`, `run` |

## src/app/api

Shared HTTP dependencies. deps.py opens a database session, verifies access tokens and current sessions, and enforces roles.

| File | Symbols / purpose |
|---|---|
| [README.md](../src/app/api/README.md) | This folder's purpose, file map and cross-references. |
| [__init__.py](../src/app/api/__init__.py) | Python package marker (some packages also expose helper functions). |
| [deps.py](../src/app/api/deps.py) | `get_db`, `CurrentUser`, `get_current_user`, `require_roles` |

## src/app/api/v1

Version-one API assembly. router.py attaches each domain beneath /api/v1, providing a stable client-facing prefix.

| File | Symbols / purpose |
|---|---|
| [README.md](../src/app/api/v1/README.md) | This folder's purpose, file map and cross-references. |
| [__init__.py](../src/app/api/v1/__init__.py) | Python package marker (some packages also expose helper functions). |
| [router.py](../src/app/api/v1/router.py) | HTTP endpoints and role dependencies; calls services/queries and shapes responses. |

## src/app/api/v1/routes

Infrastructure HTTP probes. health.py separates process liveness from PostgreSQL readiness.

| File | Symbols / purpose |
|---|---|
| [README.md](../src/app/api/v1/routes/README.md) | This folder's purpose, file map and cross-references. |
| [__init__.py](../src/app/api/v1/routes/__init__.py) | Python package marker (some packages also expose helper functions). |
| [health.py](../src/app/api/v1/routes/health.py) | `liveness`, `readiness` |

## src/app/core

Cross-cutting infrastructure: environment settings, cryptography, money rules, rate limits, errors, structured logs, translations and telemetry. tenancy.py and audit_client.py are retained template references, not active marketplace isolation/audit paths.

| File | Symbols / purpose |
|---|---|
| [README.md](../src/app/core/README.md) | This folder's purpose, file map and cross-references. |
| [__init__.py](../src/app/core/__init__.py) | Python package marker (some packages also expose helper functions). |
| [audit_client.py](../src/app/core/audit_client.py) | `emit_audit_event` |
| [config.py](../src/app/core/config.py) | `Settings` |
| [exceptions.py](../src/app/core/exceptions.py) | `AppError`, `NotFoundError`, `ValidationError`, `ConflictError`, `ForbiddenError`, `UnauthorizedError`, `RateLimitError`, `OptimisticLockError`, `_error_envelope`, `app_error_handler` |
| [logging.py](../src/app/core/logging.py) | `configure_logging` |
| [messages.py](../src/app/core/messages.py) | `HealthMsg`, `SecurityMsg`, `ExampleMsg` |
| [metrics.py](../src/app/core/metrics.py) | `_http_instruments`, `record_http_request` |
| [middleware.py](../src/app/core/middleware.py) | `LanguageMiddleware`, `CorrelationIdMiddleware`, `TenantMiddleware`, `RequestLoggingMiddleware` |
| [money.py](../src/app/core/money.py) | `validate_currency`, `commission` |
| [rate_limit.py](../src/app/core/rate_limit.py) | `limit_auth` |
| [security.py](../src/app/core/security.py) | `hash_password`, `verify_password`, `opaque_token`, `token_digest`, `access_token`, `decode_token` |
| [telemetry.py](../src/app/core/telemetry.py) | `configure_telemetry`, `mount_metrics`, `prometheus_metrics`, `get_tracer` |
| [tenancy.py](../src/app/core/tenancy.py) | `set_current_tenant`, `get_current_tenant_id`, `get_current_tenant_slug`, `get_tenant_schema`, `current_schema` |

## src/app/db

Database infrastructure: ORM base, reusable record identity/timestamps, explicit model registry, pooled async sessions. The marketplace uses one shared schema. Legacy tenant session helpers are reference-only.

| File | Symbols / purpose |
|---|---|
| [README.md](../src/app/db/README.md) | This folder's purpose, file map and cross-references. |
| [__init__.py](../src/app/db/__init__.py) | Python package marker (some packages also expose helper functions). |
| [base.py](../src/app/db/base.py) | `Base` |
| [mixins.py](../src/app/db/mixins.py) | `UUIDPKMixin`, `TimestampMixin`, `AuditMixin`, `SoftDeleteMixin`, `VersionMixin` |
| [models.py](../src/app/db/models.py) | Database table definitions, foreign keys, indexes and constraints. |
| [record.py](../src/app/db/record.py) | `Record` |
| [session.py](../src/app/db/session.py) | `_make_engine`, `dispose_engines`, `shared_session`, `_tenant_session`, `get_db_session`, `get_read_db_session`, `marketplace_session` |

## src/app/domains

Business modules of the modular monolith. Start with identity or catalog, then follow shopping → orders → finance. Events persist alongside mutations; analytics reads aggregates.

| File | Symbols / purpose |
|---|---|
| [README.md](../src/app/domains/README.md) | This folder's purpose, file map and cross-references. |
| [__init__.py](../src/app/domains/__init__.py) | Python package marker (some packages also expose helper functions). |

## src/app/domains/administration

Administrator-only seller approval, account disablement, product moderation and audit inspection. Services use the same identity/catalog records and write durable audit events. Staff provisioning is a CLI in scripts/create_staff.py.

| File | Symbols / purpose |
|---|---|
| [README.md](../src/app/domains/administration/README.md) | This folder's purpose, file map and cross-references. |
| [__init__.py](../src/app/domains/administration/__init__.py) | Python package marker (some packages also expose helper functions). |
| [router.py](../src/app/domains/administration/router.py) | `users`, `update_user`, `moderate`, `audit` |
| [schemas.py](../src/app/domains/administration/schemas.py) | `UserUpdate`, `StaffCreate`, `ModerateProduct`, `AuditOut` |
| [service.py](../src/app/domains/administration/service.py) | `update_user` |

## src/app/domains/analytics

Read-only paid-sales aggregates by currency, product and seller. No buyer emails or shipping addresses are exposed. Seller-scoped reports reuse the aggregate query with an ownership filter. There is no service wrapper because these queries contain no mutation workflow.

| File | Symbols / purpose |
|---|---|
| [README.md](../src/app/domains/analytics/README.md) | This folder's purpose, file map and cross-references. |
| [__init__.py](../src/app/domains/analytics/__init__.py) | Python package marker (some packages also expose helper functions). |
| [repository.py](../src/app/domains/analytics/repository.py) | `sales`, `product_sales`, `seller_sales` |
| [router.py](../src/app/domains/analytics/router.py) | `sales`, `products`, `sellers`, `seller_sales` |
| [schemas.py](../src/app/domains/analytics/schemas.py) | `CurrencySales`, `ProductSales`, `SellerSales` |

## src/app/domains/catalog

Seller-owned physical products, stock and public browsing/reviews. Catalog reads require active approved sellers and unblocked products. Updates use row locking plus client version checks. Verified-purchase reviews depend on delivered orders.

| File | Symbols / purpose |
|---|---|
| [README.md](../src/app/domains/catalog/README.md) | This folder's purpose, file map and cross-references. |
| [__init__.py](../src/app/domains/catalog/__init__.py) | Python package marker (some packages also expose helper functions). |
| [models.py](../src/app/domains/catalog/models.py) | `Product`, `Review` |
| [repository.py](../src/app/domains/catalog/repository.py) | `visible_products`, `get_product` |
| [router.py](../src/app/domains/catalog/router.py) | `products`, `product`, `seller_products`, `create`, `update`, `review`, `reviews` |
| [schemas.py](../src/app/domains/catalog/schemas.py) | `ProductCreate`, `ProductUpdate`, `ProductOut`, `ReviewCreate`, `ReviewOut` |
| [service.py](../src/app/domains/catalog/service.py) | `create`, `update`, `review` |

## src/app/domains/events

Database-backed audit records and outbox events. record_event adds both to the caller's business transaction. The outbox worker publishes after commit; audit records remain queryable through administration.

| File | Symbols / purpose |
|---|---|
| [README.md](../src/app/domains/events/README.md) | This folder's purpose, file map and cross-references. |
| [__init__.py](../src/app/domains/events/__init__.py) | Python package marker (some packages also expose helper functions). |
| [models.py](../src/app/domains/events/models.py) | `OutboxEvent`, `AuditLog` |
| [service.py](../src/app/domains/events/service.py) | `record_event` |

## src/app/domains/example

Unmounted reference from the original template. Shows the smallest five-file domain and generic mixins; active marketplace routes are wired in api/v1/router.py. Do not copy its generic version example for concurrency-critical stock operations.

| File | Symbols / purpose |
|---|---|
| [README.md](../src/app/domains/example/README.md) | This folder's purpose, file map and cross-references. |
| [__init__.py](../src/app/domains/example/__init__.py) | Python package marker (some packages also expose helper functions). |
| [models.py](../src/app/domains/example/models.py) | `ExampleItem` |
| [repository.py](../src/app/domains/example/repository.py) | `ExampleItemRepository` |
| [router.py](../src/app/domains/example/router.py) | `_service`, `list_items`, `create_item`, `get_item`, `update_item`, `delete_item` |
| [schemas.py](../src/app/domains/example/schemas.py) | `CamelModel`, `PaginationMeta`, `PagedResponse`, `ExampleItemCreate`, `ExampleItemUpdate`, `ExampleItemResponse` |
| [service.py](../src/app/domains/example/service.py) | `ExampleItemService` |

## src/app/domains/finance

Local simulated captures/refunds, capture/refund transaction journal, commission snapshots and manually recorded seller settlements. No live payment calls or bank transfers occur. Every mutation locks its order to coordinate with cancellation/expiry.

| File | Symbols / purpose |
|---|---|
| [README.md](../src/app/domains/finance/README.md) | This folder's purpose, file map and cross-references. |
| [__init__.py](../src/app/domains/finance/__init__.py) | Python package marker (some packages also expose helper functions). |
| [models.py](../src/app/domains/finance/models.py) | `Payment`, `LedgerEntry`, `Settlement` |
| [repository.py](../src/app/domains/finance/repository.py) | `payment_for_order` |
| [router.py](../src/app/domains/finance/router.py) | `pay_local`, `payments`, `returns`, `refund`, `settle`, `ledger`, `settlements`, `seller_settlements` |
| [schemas.py](../src/app/domains/finance/schemas.py) | `PaymentOut`, `RefundInput`, `SettlementInput`, `SettlementOut`, `LedgerOut` |
| [service.py](../src/app/domains/finance/service.py) | `require_local_payments`, `pay_local`, `refund_local`, `settle` |

## src/app/domains/identity

Account registration, password login, session rotation/revocation, local email verification and password reset. Public registration allows only buyer/seller. api/deps.py checks current permissions on protected requests.

| File | Symbols / purpose |
|---|---|
| [README.md](../src/app/domains/identity/README.md) | This folder's purpose, file map and cross-references. |
| [__init__.py](../src/app/domains/identity/__init__.py) | Python package marker (some packages also expose helper functions). |
| [models.py](../src/app/domains/identity/models.py) | `User`, `LoginSession`, `ActionToken` |
| [repository.py](../src/app/domains/identity/repository.py) | `by_email` |
| [router.py](../src/app/domains/identity/router.py) | `register`, `login`, `refresh`, `logout`, `me`, `request_verification`, `verify`, `request_reset`, `reset` |
| [schemas.py](../src/app/domains/identity/schemas.py) | `Register`, `Login`, `TokenInput`, `EmailInput`, `ResetPassword`, `UserOut`, `Tokens`, `ActionResponse` |
| [service.py](../src/app/domains/identity/service.py) | `register`, `issue_session`, `login`, `refresh_session`, `request_action`, `consume_action`, `logout` |

## src/app/domains/orders

Atomic checkout, price/address snapshots, inventory reservation, cancellation, seller fulfillment, and full-order return requests. Depends on identity, catalog, shopping and events. Payment/refund state changes live in finance.

| File | Symbols / purpose |
|---|---|
| [README.md](../src/app/domains/orders/README.md) | This folder's purpose, file map and cross-references. |
| [__init__.py](../src/app/domains/orders/__init__.py) | Python package marker (some packages also expose helper functions). |
| [models.py](../src/app/domains/orders/models.py) | `Order`, `OrderItem`, `ReturnRequest` |
| [repository.py](../src/app/domains/orders/repository.py) | `get_order`, `items`, `serialize` |
| [router.py](../src/app/domains/orders/router.py) | `checkout`, `orders`, `order`, `cancel`, `request_return`, `returns`, `fulfillments`, `fulfill` |
| [schemas.py](../src/app/domains/orders/schemas.py) | `Checkout`, `OrderItemOut`, `OrderOut`, `Fulfill`, `ReturnCreate`, `ReturnOut`, `SellerFulfillment` |
| [service.py](../src/app/domains/orders/service.py) | `checkout`, `restock`, `cancel`, `fulfill`, `request_return` |

## src/app/domains/shopping

Buyer-owned shipping addresses and cart lines. Cart mutation locks the buyer record, the same lock used by checkout. Cart contents do not reserve inventory; checkout does.

| File | Symbols / purpose |
|---|---|
| [README.md](../src/app/domains/shopping/README.md) | This folder's purpose, file map and cross-references. |
| [__init__.py](../src/app/domains/shopping/__init__.py) | Python package marker (some packages also expose helper functions). |
| [models.py](../src/app/domains/shopping/models.py) | `Address`, `CartItem` |
| [repository.py](../src/app/domains/shopping/repository.py) | `lock_buyer`, `owned_address` |
| [router.py](../src/app/domains/shopping/router.py) | `addresses`, `address`, `delete_address`, `cart`, `put`, `remove` |
| [schemas.py](../src/app/domains/shopping/schemas.py) | `AddressCreate`, `AddressOut`, `CartPut`, `CartOut` |
| [service.py](../src/app/domains/shopping/service.py) | `put_item` |

## src/app/i18n

Translation helpers and per-request language context. Missing translations fall back to English, then the original key/message. Original template messages use translation keys; new marketplace messages currently use English fallback text.

| File | Symbols / purpose |
|---|---|
| [README.md](../src/app/i18n/README.md) | This folder's purpose, file map and cross-references. |
| [__init__.py](../src/app/i18n/__init__.py) | `_load_locale`, `translate`, `t`, `get_request_language`, `set_language` |

## src/app/i18n/locales

JSON language catalogs. en.json contains original template translations. Extend core/messages.py and locale catalogs when localizing marketplace messages.

| File | Symbols / purpose |
|---|---|
| [README.md](../src/app/i18n/locales/README.md) | This folder's purpose, file map and cross-references. |
| [en.json](../src/app/i18n/locales/en.json) | Documentation, configuration or support file. |

## src/app/kafka

Low-level Kafka producer and original audit topic constants. Active marketplace events use the transactional outbox worker. The producer is idempotent within Kafka; consumers still must deduplicate application event IDs.

| File | Symbols / purpose |
|---|---|
| [README.md](../src/app/kafka/README.md) | This folder's purpose, file map and cross-references. |
| [__init__.py](../src/app/kafka/__init__.py) | Python package marker (some packages also expose helper functions). |
| [constants.py](../src/app/kafka/constants.py) | `KafkaTopics` |
| [producer.py](../src/app/kafka/producer.py) | `start_kafka_producer`, `stop_kafka_producer`, `publish` |

## src/app/workers

Independent long-running processes: reservations cancels expired unpaid orders; outbox publishes durable events to Kafka. Start these separately from API replicas. Their batch functions are integration tested.

| File | Symbols / purpose |
|---|---|
| [README.md](../src/app/workers/README.md) | This folder's purpose, file map and cross-references. |
| [__init__.py](../src/app/workers/__init__.py) | Python package marker (some packages also expose helper functions). |
| [outbox.py](../src/app/workers/outbox.py) | `publish_batch`, `main` |
| [reservations.py](../src/app/workers/reservations.py) | `expire_batch`, `main` |

## tests

Pytest suite. conftest.py creates isolated PostgreSQL schemas, temporary RSA keys, real role accounts and one session per HTTP request. TEST_DATABASE_URL optionally replaces Testcontainers.

| File | Symbols / purpose |
|---|---|
| [README.md](../tests/README.md) | This folder's purpose, file map and cross-references. |
| [__init__.py](../tests/__init__.py) | Python package marker (some packages also expose helper functions). |
| [conftest.py](../tests/conftest.py) | `test_settings`, `db_url`, `test_engine`, `db_session`, `client`, `accounts` |

## tests/golden

Reserved original-template location for fixed-input financial output fixtures. No standalone golden test cases yet; commission rounding is verified in unit/test_marketplace_security.py.

| File | Symbols / purpose |
|---|---|
| [README.md](../tests/golden/README.md) | This folder's purpose, file map and cross-references. |
| [__init__.py](../tests/golden/__init__.py) | Python package marker (some packages also expose helper functions). |

## tests/integration

Real PostgreSQL and HTTP scenarios, including multi-seller checkout, ownership, revocation, refunds, settlement holds, concurrent inventory races, expiry and outbox retry state.

| File | Symbols / purpose |
|---|---|
| [README.md](../tests/integration/README.md) | This folder's purpose, file map and cross-references. |
| [__init__.py](../tests/integration/__init__.py) | Python package marker (some packages also expose helper functions). |
| [test_health.py](../tests/integration/test_health.py) | `test_health_returns_ok` |
| [test_identity.py](../tests/integration/test_identity.py) | `test_registration_verification_and_password_reset`, `test_refresh_rotation_and_logout`, `test_admin_approval_and_immediate_revocation` |
| [test_marketplace.py](../tests/integration/test_marketplace.py) | `product`, `prepare`, `checkout`, `deliver`, `test_full_marketplace_lifecycle`, `test_checkout_race_never_oversells`, `test_simultaneous_duplicate_checkout`, `test_checkout_rollback_and_cancellation`, `test_ownership_and_role_boundaries`, `test_catalog_versions_moderation_and_validation`, `test_settlement_waits_for_return_window`, `test_currency_expansion_and_mixed_cart_rollback`, `test_cart_address_and_fulfillment_guards` |
| [test_workers.py](../tests/integration/test_workers.py) | `session_scope`, `test_expiry_restocks_once`, `test_outbox_failure_is_retryable` |

## tests/unit

Fast isolated checks for security, money, settings, translations, metrics and retained template services. Provider/Redis calls are mocked when testing deterministic decisions.

| File | Symbols / purpose |
|---|---|
| [README.md](../tests/unit/README.md) | This folder's purpose, file map and cross-references. |
| [__init__.py](../tests/unit/__init__.py) | Python package marker (some packages also expose helper functions). |
| [test_audit_client.py](../tests/unit/test_audit_client.py) | `TestEmitAuditEvent` |
| [test_example_service.py](../tests/unit/test_example_service.py) | `_make_item`, `repo`, `service`, `test_create_delegates_to_repo`, `test_update_version_mismatch_raises`, `test_delete_calls_soft_delete` |
| [test_i18n.py](../tests/unit/test_i18n.py) | `_public_constants`, `test_translate_uses_english_catalog_by_default`, `test_translate_interpolates_params`, `test_translate_falls_back_to_english_for_unknown_language`, `test_translate_returns_key_itself_if_not_found_in_any_locale`, `test_get_request_language_parses_en_us`, `test_get_request_language_empty_returns_en`, `test_set_language_context_manager_restores_previous`, `test_app_error_accepts_message_key`, `test_error_response_uses_translated_message`, `test_all_message_keys_present_in_en_json`, `test_all_en_json_values_are_non_empty_strings` |
| [test_marketplace_security.py](../tests/unit/test_marketplace_security.py) | `test_commission_rounds_minor_units`, `test_password_and_token_security`, `test_production_rejects_unsafe_config`, `test_simulation_unavailable_in_production`, `test_rate_limiter_and_fail_closed`, `test_missing_audience_rejected` |
| [test_metrics.py](../tests/unit/test_metrics.py) | `test_metrics_endpoint_exposes_prometheus_metrics` |
