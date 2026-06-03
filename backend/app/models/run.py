"""Run model — one founder idea's end-to-end execution record."""

from typing import Any

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Run(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A pillar execution run (see CLAUDE.md §19.3)."""

    __tablename__ = "runs"

    pillar: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    plan: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
