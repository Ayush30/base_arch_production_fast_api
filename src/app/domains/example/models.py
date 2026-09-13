from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import AuditMixin, SoftDeleteMixin, TimestampMixin, UUIDPKMixin, VersionMixin


class ExampleItem(UUIDPKMixin, TimestampMixin, AuditMixin, SoftDeleteMixin, VersionMixin, Base):
    """Tenant-scoped example record.  No __table_args__ schema → resolves per-request."""

    __tablename__ = "example_items"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
