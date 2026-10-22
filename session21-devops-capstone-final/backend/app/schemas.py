"""Request and response shapes.

Separate from the ORM models on purpose: the API contract should not change
just because a column was added.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import Category, Priority, Status


class IssueUpdateCreate(BaseModel):
    note: str = Field(min_length=1, max_length=2000)
    author: str = Field(default="staff", max_length=100)


class IssueUpdateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    issue_id: int
    note: str
    author: str
    created_at: datetime


class IssueCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(default="", max_length=5000)
    building: str = Field(min_length=1, max_length=100)
    room: str = Field(default="", max_length=50)
    category: Category = Category.OTHER
    priority: Priority = Priority.MEDIUM
    reported_by: str = Field(default="anonymous", max_length=100)
    # Required, and validated as a real address by EmailStr rather than a
    # hand-rolled regex.
    reporter_email: EmailStr


class IssuePatch(BaseModel):
    """Every field optional - PUT here means "change what I sent"."""

    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    building: str | None = Field(default=None, min_length=1, max_length=100)
    room: str | None = Field(default=None, max_length=50)
    category: Category | None = None
    priority: Priority | None = None
    status: Status | None = None
    assigned_to: str | None = Field(default=None, max_length=100)


class IssueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    building: str
    room: str
    category: Category
    priority: Priority
    status: Status
    reported_by: str
    reporter_email: str
    assigned_to: str | None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None


class IssueDetail(IssueOut):
    updates: list[IssueUpdateOut] = []


class Stats(BaseModel):
    total: int
    open: int
    in_progress: int
    resolved: int
    urgent_open: int
    by_building: dict[str, int]
    by_category: dict[str, int]
    # None until at least one issue has been resolved.
    avg_resolution_hours: float | None
