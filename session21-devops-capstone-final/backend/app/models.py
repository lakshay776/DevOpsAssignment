"""Database tables.

Two tables with a foreign key between them: an issue, and the worklog of
notes staff add while working on it.
"""

import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _values(enum_cls) -> list[str]:
    """Persist enum values rather than names, matching the migration."""
    return [member.value for member in enum_cls]


def _utcnow() -> datetime:
    """Timezone-aware UTC. `datetime.utcnow` is deprecated and returns a
    naive value, which compares badly against values read back from Postgres."""
    return datetime.now(timezone.utc)


class Status(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


class Priority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Category(str, enum.Enum):
    ELECTRICAL = "electrical"
    PLUMBING = "plumbing"
    NETWORK = "network"
    FURNITURE = "furniture"
    OTHER = "other"


class Issue(Base):
    __tablename__ = "issues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)

    building: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    room: Mapped[str] = mapped_column(String(50), default="", nullable=False)

    # values_callable matters: without it SQLAlchemy stores the enum *name*
    # ("RESOLVED"), while the migration created the Postgres type from the
    # *values* ("resolved"), and every write fails on the mismatch.
    category: Mapped[Category] = mapped_column(
        Enum(Category, name="category", values_callable=_values),
        default=Category.OTHER, nullable=False, index=True,
    )
    priority: Mapped[Priority] = mapped_column(
        Enum(Priority, name="priority", values_callable=_values),
        default=Priority.MEDIUM, nullable=False, index=True,
    )
    status: Mapped[Status] = mapped_column(
        Enum(Status, name="status", values_callable=_values),
        default=Status.OPEN, nullable=False, index=True,
    )

    reported_by: Mapped[str] = mapped_column(String(100), default="anonymous", nullable=False)
    # Required from the reporter so maintenance can follow up. Existing rows
    # predate the column, so the migration backfills them rather than failing
    # on a NOT NULL constraint.
    reporter_email: Mapped[str] = mapped_column(String(200), nullable=False)
    assigned_to: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )
    # Set the moment status becomes RESOLVED; this is what makes average
    # resolution time computable.
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    updates: Mapped[list["IssueUpdate"]] = relationship(
        back_populates="issue",
        # Deleting an issue must take its worklog with it, otherwise the FK
        # blocks the delete.
        cascade="all, delete-orphan",
        order_by="IssueUpdate.created_at",
    )


class IssueUpdate(Base):
    __tablename__ = "issue_updates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    issue_id: Mapped[int] = mapped_column(
        ForeignKey("issues.id", ondelete="CASCADE"), nullable=False, index=True
    )
    note: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(String(100), default="staff", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    issue: Mapped[Issue] = relationship(back_populates="updates")
