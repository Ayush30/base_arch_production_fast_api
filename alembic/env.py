from __future__ import annotations

import asyncio
from logging.config import fileConfig
from typing import TYPE_CHECKING

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy.schema import CreateSchema

import app.db.models  # noqa: F401
from app.core.config import settings
from app.db.base import Base

if TYPE_CHECKING:
    from sqlalchemy.engine import Connection

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url.replace("%", "%%"))
if config.config_file_name:
    fileConfig(config.config_file_name)
target_metadata = Base.metadata


def configure(connection: Connection | None = None) -> None:
    context.configure(
        connection=connection,
        url=settings.database_url if connection is None else None,
        target_metadata=target_metadata,
        version_table_schema=settings.shared_schema,
        include_schemas=True,
        include_name=lambda name, type_, parent_names: (
            type_ != "schema" or name in {None, settings.shared_schema}
        ),
        literal_binds=connection is None,
        compare_type=True,
        include_object=lambda obj, name, type_, reflected, compare_to: name != "alembic_version",
    )
    with context.begin_transaction():
        if connection is None:
            from sqlalchemy.dialects import postgresql

            quoted = postgresql.dialect().identifier_preparer.quote_schema(settings.shared_schema)
            context.execute(CreateSchema(settings.shared_schema, if_not_exists=True))
            context.execute(f"SET search_path TO {quoted}")
        context.run_migrations()


def run_migrations(connection: Connection) -> None:
    connection.execute(CreateSchema(settings.shared_schema, if_not_exists=True))
    quoted = connection.dialect.identifier_preparer.quote_schema(settings.shared_schema)
    connection.exec_driver_sql(f"SET search_path TO {quoted}")
    connection.commit()
    connection.dialect.default_schema_name = settings.shared_schema
    configure(connection)


async def online() -> None:
    engine = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with engine.connect() as connection:
        await connection.run_sync(run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    configure()
else:
    asyncio.run(online())
