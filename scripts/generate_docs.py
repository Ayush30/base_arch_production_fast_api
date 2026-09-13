"""Regenerate navigational docs from real paths/AST/OpenAPI. Handwritten guides stay intact."""

from __future__ import annotations

import ast
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {
    ".git",
    ".venv",
    "venv",
    "keys",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "htmlcov",
    ".uv",
    "dist",
    "build",
}
PURPOSES = {
    "src": "Installable Python source tree. The app package is the server; it does not contain a mobile UI.",
    "src/app": "Application composition: main.py builds FastAPI, registers middleware and routers, and manages startup/shutdown.",
    "src/app/api": "Shared HTTP dependencies. deps.py opens a database session, verifies access tokens and current sessions, and enforces roles.",
    "src/app/api/v1": "Version-one API assembly. router.py attaches each domain beneath /api/v1, providing a stable client-facing prefix.",
    "src/app/api/v1/routes": "Infrastructure HTTP probes. health.py separates process liveness from PostgreSQL readiness.",
    "src/app/core": "Cross-cutting infrastructure: environment settings, cryptography, money rules, rate limits, errors, structured logs, translations and telemetry. tenancy.py and audit_client.py are retained template references, not active marketplace isolation/audit paths.",
    "src/app/db": "Database infrastructure: ORM base, reusable record identity/timestamps, explicit model registry, pooled async sessions. The marketplace uses one shared schema. Legacy tenant session helpers are reference-only.",
    "src/app/domains": "Business modules of the modular monolith. Start with identity or catalog, then follow shopping → orders → finance. Events persist alongside mutations; analytics reads aggregates.",
    "src/app/domains/identity": "Account registration, password login, session rotation/revocation, local email verification and password reset. Public registration allows only buyer/seller. api/deps.py checks current permissions on protected requests.",
    "src/app/domains/catalog": "Seller-owned physical products, stock and public browsing/reviews. Catalog reads require active approved sellers and unblocked products. Updates use row locking plus client version checks. Verified-purchase reviews depend on delivered orders.",
    "src/app/domains/shopping": "Buyer-owned shipping addresses and cart lines. Cart mutation locks the buyer record, the same lock used by checkout. Cart contents do not reserve inventory; checkout does.",
    "src/app/domains/orders": "Atomic checkout, price/address snapshots, inventory reservation, cancellation, seller fulfillment, and full-order return requests. Depends on identity, catalog, shopping and events. Payment/refund state changes live in finance.",
    "src/app/domains/finance": "Local simulated captures/refunds, capture/refund transaction journal, commission snapshots and manually recorded seller settlements. No live payment calls or bank transfers occur. Every mutation locks its order to coordinate with cancellation/expiry.",
    "src/app/domains/analytics": "Read-only paid-sales aggregates by currency, product and seller. No buyer emails or shipping addresses are exposed. Seller-scoped reports reuse the aggregate query with an ownership filter. There is no service wrapper because these queries contain no mutation workflow.",
    "src/app/domains/administration": "Administrator-only seller approval, account disablement, product moderation and audit inspection. Services use the same identity/catalog records and write durable audit events. Staff provisioning is a CLI in scripts/create_staff.py.",
    "src/app/domains/events": "Database-backed audit records and outbox events. record_event adds both to the caller's business transaction. The outbox worker publishes after commit; audit records remain queryable through administration.",
    "src/app/domains/example": "Unmounted reference from the original template. Shows the smallest five-file domain and generic mixins; active marketplace routes are wired in api/v1/router.py. Do not copy its generic version example for concurrency-critical stock operations.",
    "src/app/i18n": "Translation helpers and per-request language context. Missing translations fall back to English, then the original key/message. Original template messages use translation keys; new marketplace messages currently use English fallback text.",
    "src/app/i18n/locales": "JSON language catalogs. en.json contains original template translations. Extend core/messages.py and locale catalogs when localizing marketplace messages.",
    "src/app/kafka": "Low-level Kafka producer and original audit topic constants. Active marketplace events use the transactional outbox worker. The producer is idempotent within Kafka; consumers still must deduplicate application event IDs.",
    "src/app/workers": "Independent long-running processes: reservations cancels expired unpaid orders; outbox publishes durable events to Kafka. Start these separately from API replicas. Their batch functions are integration tested.",
    "tests": "Pytest suite. conftest.py creates isolated PostgreSQL schemas, temporary RSA keys, real role accounts and one session per HTTP request. TEST_DATABASE_URL optionally replaces Testcontainers.",
    "tests/unit": "Fast isolated checks for security, money, settings, translations, metrics and retained template services. Provider/Redis calls are mocked when testing deterministic decisions.",
    "tests/integration": "Real PostgreSQL and HTTP scenarios, including multi-seller checkout, ownership, revocation, refunds, settlement holds, concurrent inventory races, expiry and outbox retry state.",
    "tests/golden": "Reserved original-template location for fixed-input financial output fixtures. No standalone golden test cases yet; commission rounding is verified in unit/test_marketplace_security.py.",
    "alembic": "Database migration runner. env.py selects the configured marketplace schema and registers current models; versions contains frozen migration history. Runtime application startup does not call create_all.",
    "alembic/versions": "Versioned, reviewable database DDL. Upgrade creates tables/constraints/indexes; downgrade reverses them and can destroy data. Never rewrite a revision after deploying it.",
    "scripts": "Operational and teaching commands: local keys/configuration, idempotent demo seed, prompted staff provisioning, API demo journey, and documentation maintenance. Legacy tenant scripts are disabled to prevent confusing schema-per-tenant provisioning with sellers.",
    "docs": "Learning curriculum, request traces, generated API/code/configuration indexes, backend glossary and deployment/integration boundaries. Start at LEARNING_PATH.md.",
    "deploy": "Local infrastructure teaching configurations. Nginx demonstrates two API replicas; Prometheus scrapes application metrics. These files need environment-specific security and availability work for production.",
    "deploy/nginx": "Reverse proxy and least-connections balancing lab. nginx.conf forwards to app/app2, limits authentication traffic and blocks public /metrics. Production requires HTTPS and a deliberate trusted-proxy policy.",
    "deploy/prometheus": "Prometheus scrape configuration. Targets app:8000/metrics on the internal Compose network. Use service discovery when replicas are dynamic.",
    ".github": "Repository automation configuration; workflows run checks on pushes and pull requests.",
    ".github/workflows": "CI pipeline: frozen dependency installation, lint, formatting, strict source typing, docs checks, real PostgreSQL tests and migration round-trip verification.",
}
FILE_HELP = {
    "models.py": "Database table definitions, foreign keys, indexes and constraints.",
    "schemas.py": "Pydantic request/response contracts and input validation.",
    "repository.py": "Reusable SQLAlchemy queries and data retrieval.",
    "service.py": "Business rules and transaction orchestration; follow the named functions below.",
    "router.py": "HTTP endpoints and role dependencies; calls services/queries and shapes responses.",
    "__init__.py": "Python package marker (some packages also expose helper functions).",
    "README.md": "This folder's purpose, file map and cross-references.",
}


FILE_HELP.update(
    {
        "main.py": "FastAPI application factory, middleware/router registration and process lifecycle.",
        "deps.py": "Inject database/current user; enforce current session, role and seller approval.",
        "config.py": "Environment settings, typed defaults and production safety validation.",
        "security.py": "Argon2 password hashing, RSA access tokens, opaque token generation and hashing.",
        "money.py": "Supported currency exponents, enabled-currency validation and integer commission rounding.",
        "rate_limit.py": "Atomic Redis Lua counter for shared authentication throttling.",
        "middleware.py": "Request language, correlation IDs, bounded-route metrics and logging; legacy tenant reference.",
        "exceptions.py": "Business error types and translated JSON error handler.",
        "messages.py": "Original template translation-key constants.",
        "logging.py": "Configure structured JSON/console logs and logging levels.",
        "metrics.py": "OpenTelemetry HTTP request counters and duration histograms.",
        "telemetry.py": "Tracing/metrics providers and Prometheus endpoint registration.",
        "tenancy.py": "Retained original schema-per-tenant context helpers; not used for seller isolation.",
        "audit_client.py": "Retained best-effort Kafka audit example; marketplace uses transactional events.",
        "base.py": "Shared SQLAlchemy declarative base collecting mapped table metadata.",
        "record.py": "UUID identity and timezone-aware creation timestamp for marketplace records.",
        "mixins.py": "Original template UUID/timestamp/audit/soft-delete/version mixins.",
        "session.py": "Pooled primary/optional replica engines and commit/rollback session boundaries.",
        "health.py": "Liveness and database readiness probes.",
        "producer.py": "Kafka producer lifecycle and acknowledged event sends.",
        "constants.py": "Original template audit topic names; marketplace topic is stored in outbox rows.",
        "outbox.py": "Retrying at-least-once publisher for committed database outbox rows.",
        "reservations.py": "Expire unpaid orders and release inventory under transaction locks.",
        "env.py": "Configure Alembic online/offline migration execution and schema filtering.",
        "conftest.py": "Isolated PostgreSQL schemas, real role credentials and HTTP test fixtures.",
        "dev_setup.py": "Create missing local .env and private/public RSA keys without overwriting them.",
        "seed.py": "Idempotent local-only role accounts, catalog and buyer address.",
        "create_staff.py": "Prompted operational staff provisioning with an audit event.",
        "demo_journey.py": "Real HTTP walkthrough creating a local buyer order and simulated payment.",
        "generate_docs.py": "Build folder READMEs, AST code map and OpenAPI/configuration references.",
        "check_docs.py": "Detect missing folder READMEs and broken local Markdown links.",
        "provision_tenant.py": "Disabled legacy command; points to marketplace seller registration.",
        "migrate_tenants.py": "Disabled legacy command; points to the shared Alembic migration chain.",
    }
)


def access_rule(path: str, method: str) -> str:
    if path.endswith(("/health", "/ready")):
        return "Public"
    if "/auth/" in path:
        return "Authenticated" if path.endswith(("/me", "/logout")) else "Public, rate limited"
    if "/admin/" in path:
        return "Admin"
    if "/finance/" in path:
        return "Finance or admin"
    if "/analytics/" in path:
        return "Analytics or admin"
    if "/seller/" in path:
        return "Approved seller, own records"
    if "/products" in path and method == "get":
        return "Public"
    if path.endswith("/checkout"):
        return "Buyer, verified email"
    return "Buyer, own records"


def maintained_files() -> list[Path]:
    result = []
    for directory, names, files in os.walk(ROOT):
        names[:] = sorted(n for n in names if n not in EXCLUDED)
        for name in sorted(files):
            path = Path(directory) / name
            if name.startswith(".env") and name != ".env.example":
                continue
            if name in {".coverage", ".DS_Store"} or name.endswith((".pyc", ".log")):
                continue
            result.append(path)
    return result


def symbols(path: Path) -> str:
    if path.suffix != ".py":
        return ""
    tree = ast.parse(path.read_text())
    names = [
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]
    return ", ".join(f"`{name}`" for name in names)


def relative(source: Path, target: Path) -> str:
    return os.path.relpath(target, source).replace(os.sep, "/")


def generate() -> None:
    for name, description in PURPOSES.items():
        folder = ROOT / name
        folder.mkdir(parents=True, exist_ok=True)
        entries = []
        for path in sorted(folder.iterdir()):
            if path.name in EXCLUDED or path.name == "README.md":
                continue
            if path.is_dir():
                entries.append(
                    f"| [{path.name}/]({path.name}/README.md) | Child module; follow its README. |"
                )
            else:
                detail = FILE_HELP.get(
                    path.name,
                    "Supporting implementation/configuration; see code index for symbols.",
                )
                listed = symbols(path)
                entries.append(f"| [{path.name}]({path.name}) | {detail} {listed} |")
        home = relative(folder, ROOT / "README.md")
        index = relative(folder, ROOT / "docs/CODE_INDEX.md")
        glossary = relative(folder, ROOT / "docs/GLOSSARY.md")
        parent = relative(folder, folder.parent / "README.md")
        text = (
            f"# {name}\n\n{description}\n\n[Project home]({home}) · [Code index]({index}) · [Parent folder]({parent}) · [Terminology]({glossary})\n\n## Files and child folders\n\n| Entry | Responsibility / symbols |\n|---|---|\n"
            + "\n".join(entries)
        )
        if name.startswith("src/app/domains/"):
            text += (
                "\n\n## Relationships\n\nHTTP requests enter through [the API router]("
                + relative(folder, ROOT / "src/app/api/v1/router.py")
                + "). Role/session checks come from [api/deps.py]("
                + relative(folder, ROOT / "src/app/api/deps.py")
                + "). Persistence uses [db/session.py]("
                + relative(folder, ROOT / "src/app/db/session.py")
                + "); business mutations record [events]("
                + relative(folder, ROOT / "src/app/domains/events/service.py")
                + "). Read the [request walkthrough]("
                + relative(folder, ROOT / "docs/REQUEST_WALKTHROUGH.md")
                + ") and [integration scenarios]("
                + relative(folder, ROOT / "tests/integration/README.md")
                + ") to see these connections in use.\n"
            )
        text += "\n\nThis navigational file is regenerated by `python scripts/generate_docs.py`; edit its purpose in that script. Handwritten learning guides live in docs/.\n"
        (folder / "README.md").write_text(text)
    from app.core.config import Settings
    from app.main import app

    schema = app.openapi()
    lines = [
        "# API reference",
        "",
        "All routes below are generated from the running FastAPI OpenAPI definition. Base URL: `/api/v1`. Interactive field-level schemas and examples are at `/docs`; machine-readable schema is at `/openapi.json`.",
        "",
        "Lists support bounded limit/offset where shown by Swagger. Authentication is a Bearer access token; role and ownership rules are documented by domain and enforced in dependencies/services. Local payment endpoints simulate money movement.",
        "",
        "| Method | Path | Access | Summary |",
        "|---|---|---|---|",
    ]
    for path, operations in schema["paths"].items():
        for method, operation in operations.items():
            if method in {"get", "post", "put", "patch", "delete"}:
                lines.append(
                    f"| {method.upper()} | `{path}` | {access_rule(path, method)} | {operation.get('summary', '')} |"
                )
    (ROOT / "docs/API_REFERENCE.md").write_text(
        "\n".join(lines)
        + "\n\nSee [role matrix and examples](../README.md), [mobile integration](REACT_NATIVE.md) and [request walkthrough](REQUEST_WALKTHROUGH.md).\n"
    )
    config = [
        "# Configuration reference",
        "",
        "Settings are read from environment variables and `.env` by [core/config.py](../src/app/core/config.py). Environment variables take precedence. Lists use JSON arrays. See [.env.example](../.env.example) for the recommended local configuration and [deployment](DEPLOYMENT.md) for production restrictions.",
        "",
        "The defaults below come from the model definition, not from your secret environment. DB URLs and key paths must be configured for the execution environment (host versus container).",
        "",
        "| Environment variable | Model default |",
        "|---|---|",
    ]
    for name, field in Settings.model_fields.items():
        alias = field.validation_alias if isinstance(field.validation_alias, str) else name.upper()
        config.append(f"| `{alias}` | `{field.default}` |")
    config.append(
        "\n`APP_PORT` controls host Python binding and Docker's published host port; the image listens on 8000. `LOCAL_UID`/`LOCAL_GID` are Compose-only local key-file permissions, not application settings. `POSTGRES_PORT`, `REDIS_PORT` and `PROXY_PORT` are Compose host port overrides. `DOCKER_OTLP_ENDPOINT` optionally overrides the container trace collector (default http://jaeger:4317); host Python still uses `OTLP_ENDPOINT`. See [Docker commands](DOCKER.md). Legacy TENANT_SCHEMA_PREFIX is not used to isolate sellers.\n"
    )
    (ROOT / "docs/CONFIGURATION.md").write_text("\n".join(config))
    files = maintained_files()
    index = [
        "# Complete project code index",
        "",
        "[Start learning](LEARNING_PATH.md) · [Request walkthrough](REQUEST_WALKTHROUGH.md) · [Glossary](GLOSSARY.md)",
        "",
        "This map lists maintained files and top-level Python classes/functions. Each folder README explains responsibilities and relationships. Runtime files, secrets, virtual environments and caches are excluded. Regenerate after structural changes with `uv run python scripts/generate_docs.py`.",
        "",
    ]
    for folder in sorted({p.parent for p in files}):
        name = relative(ROOT, folder)
        index.extend(
            [
                f"## {name}",
                "",
                PURPOSES.get(
                    name, "Project entry points, packaging, local orchestration and orientation."
                ),
                "",
                "| File | Symbols / purpose |",
                "|---|---|",
            ]
        )
        for path in (p for p in files if p.parent == folder):
            index.append(
                f"| [{path.name}]({relative(ROOT / 'docs', path)}) | {symbols(path) or FILE_HELP.get(path.name, 'Documentation, configuration or support file.')} |"
            )
        index.append("")
    (ROOT / "docs/CODE_INDEX.md").write_text("\n".join(index))


if __name__ == "__main__":
    generate()
