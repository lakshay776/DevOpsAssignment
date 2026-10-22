"""create issues and issue_updates

Revision ID: 0001
Revises:
Create Date: 2026-10-21
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

# The types are created once, explicitly, at the top of upgrade(). They are
# then referenced with create_type=False, because a plain sa.Enum column
# makes create_table emit its own CREATE TYPE, which fails with
# "type already exists" the moment it is also created up front.
STATUS = ("open", "in_progress", "resolved")
PRIORITY = ("low", "medium", "high", "urgent")
CATEGORY = ("electrical", "plumbing", "network", "furniture", "other")

status_enum = postgresql.ENUM(*STATUS, name="status", create_type=False)
priority_enum = postgresql.ENUM(*PRIORITY, name="priority", create_type=False)
category_enum = postgresql.ENUM(*CATEGORY, name="category", create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    # checkfirst so a re-run after a partial failure is not fatal.
    sa.Enum(*STATUS, name="status").create(bind, checkfirst=True)
    sa.Enum(*PRIORITY, name="priority").create(bind, checkfirst=True)
    sa.Enum(*CATEGORY, name="category").create(bind, checkfirst=True)

    op.create_table(
        "issues",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("building", sa.String(length=100), nullable=False),
        sa.Column("room", sa.String(length=50), nullable=False, server_default=""),
        sa.Column("category", category_enum, nullable=False, server_default="other"),
        sa.Column("priority", priority_enum, nullable=False, server_default="medium"),
        sa.Column("status", status_enum, nullable=False, server_default="open"),
        sa.Column("reported_by", sa.String(length=100), nullable=False, server_default="anonymous"),
        sa.Column("assigned_to", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    # The dashboard filters on these three, and the stats endpoint groups by
    # building, so they are worth indexing from the start.
    op.create_index("ix_issues_building", "issues", ["building"])
    op.create_index("ix_issues_category", "issues", ["category"])
    op.create_index("ix_issues_priority", "issues", ["priority"])
    op.create_index("ix_issues_status", "issues", ["status"])

    op.create_table(
        "issue_updates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "issue_id",
            sa.Integer(),
            sa.ForeignKey("issues.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("author", sa.String(length=100), nullable=False, server_default="staff"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_issue_updates_issue_id", "issue_updates", ["issue_id"])


def downgrade() -> None:
    op.drop_index("ix_issue_updates_issue_id", table_name="issue_updates")
    op.drop_table("issue_updates")
    for name in ("ix_issues_status", "ix_issues_priority", "ix_issues_category", "ix_issues_building"):
        op.drop_index(name, table_name="issues")
    op.drop_table("issues")

    bind = op.get_bind()
    sa.Enum(name="status").drop(bind, checkfirst=True)
    sa.Enum(name="priority").drop(bind, checkfirst=True)
    sa.Enum(name="category").drop(bind, checkfirst=True)
