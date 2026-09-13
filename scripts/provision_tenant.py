"""
provision_tenant.py <slug>

Creates the tenant schema and runs all tenant migrations into it.
"""
from __future__ import annotations

import asyncio
import subprocess
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

sys.path.insert(0, "src")
from app.core.config import settings  # noqa: E402


async def provision(slug: str) -> None:
    schema = f"{settings.tenant_schema_prefix}{slug}"
    engine = create_async_engine(settings.database_url)

    async with engine.begin() as conn:
        await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
        print(f"Schema '{schema}' created.")

    await engine.dispose()

    # Run Alembic migrations targeting the new tenant schema
    result = subprocess.run(
        ["uv", "run", "alembic", "upgrade", "head", "-x", f"schema={schema}"],
        capture_output=False,
    )
    if result.returncode != 0:
        print(f"Migration failed for {schema}", file=sys.stderr)
        sys.exit(1)
    print(f"Tenant '{slug}' provisioned successfully.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/provision_tenant.py <slug>", file=sys.stderr)
        sys.exit(1)
    asyncio.run(provision(sys.argv[1]))
