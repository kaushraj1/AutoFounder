"""Run model — one founder idea's end-to-end execution record."""

import uuid
from typing import Any

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Run(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A pillar execution run (see CLAUDE.md §19.3)."""

    __tablename__ = "runs"

    workspace_id: Mapped[uuid.UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    organization_id: Mapped[uuid.UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    pillar: Mapped[str | None] = mapped_column("current_pillar", String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    plan: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    idea_text: Mapped[str] = mapped_column(nullable=False)
    idea_meta: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
