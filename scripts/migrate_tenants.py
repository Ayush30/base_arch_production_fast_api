"""
migrate_tenants.py upgrade|downgrade [revision]

Iterates every tenant schema in the registry + the shared schema and applies
pending Alembic migrations.
"""
from __future__ import annotations

import asyncio
import subprocess
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

sys.path.insert(0, "src")
from app.core.config import settings  # noqa: E402


async def get_tenant_schemas(engine_url: str) -> list[str]:
    engine = create_async_engine(engine_url)
    async with engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT schema_name FROM information_schema.schemata "
                "WHERE schema_name LIKE :prefix"
            ),
            {"prefix": f"{settings.tenant_schema_prefix}%"},
        )
        schemas = [row[0] for row in result.fetchall()]
    await engine.dispose()
    return schemas


def alembic_run(schema: str, command: str, revision: str) -> int:
    result = subprocess.run(
        ["uv", "run", "alembic", command, revision, "-x", f"schema={schema}"],
        capture_output=False,
    )
    return result.returncode


async def main(command: str, revision: str) -> None:
    tenant_schemas = await get_tenant_schemas(settings.database_url)
    all_schemas = [settings.shared_schema] + tenant_schemas

    failures: list[str] = []
    for schema in all_schemas:
        print(f"  → {schema}")
        code = alembic_run(schema, command, revision)
        if code != 0:
            failures.append(schema)

    if failures:
        print(f"\nFailed schemas: {failures}", file=sys.stderr)
        sys.exit(1)
    print("\nAll schemas migrated successfully.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/migrate_tenants.py upgrade|downgrade [revision]")
        sys.exit(1)
    cmd = sys.argv[1]
    rev = sys.argv[2] if len(sys.argv) > 2 else "head"
    asyncio.run(main(cmd, rev))
