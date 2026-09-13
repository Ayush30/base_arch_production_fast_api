from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Integer, func, text
from sqlalchemy.orm import Mapped, mapped_column


class UUIDPKMixin:
    """UUID v7 primary key — app-side generated for index locality."""

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        server_default=text("gen_random_uuid()"),  # fallback; prefer app-side uuid7
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class AuditMixin:
    """Tracks which user created/last-updated a record."""

    created_by: Mapped[UUID] = mapped_column(nullable=False)
    updated_by: Mapped[UUID] = mapped_column(nullable=False)


class SoftDeleteMixin:
    """Logical delete — hard deletes of tenant data are forbidden."""

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


class VersionMixin:
    """Optimistic concurrency version counter."""

    version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default=text("1")
    )
