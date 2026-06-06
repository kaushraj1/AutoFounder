"""Gate model — a human-in-the-loop approval checkpoint within a run."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Gate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """An approval gate (pending | approved | rejected)."""

    __tablename__ = "gates"

    run_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True),
        nullable=False,
    )
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    decided_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    timeout_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
