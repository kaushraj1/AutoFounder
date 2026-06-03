"""Artifact model — a deliverable produced during a run (canvas, ERD, repo URL, ...)."""

import uuid
from typing import Any

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Artifact(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """An artifact attached to a run."""

    __tablename__ = "artifacts"

    run_id: Mapped[uuid.UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    uri: Mapped[str] = mapped_column(String(1024), nullable=False)
    # Mapped to column "metadata" (the attribute is `meta` because `metadata` is reserved).
    meta: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONB, nullable=True)
