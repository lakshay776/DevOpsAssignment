"""add reporter_email to issues

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-22
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Added nullable first, backfilled, then made NOT NULL. Adding a NOT NULL
    # column directly fails on any table that already has rows.
    op.add_column("issues", sa.Column("reporter_email", sa.String(length=200), nullable=True))
    op.execute("UPDATE issues SET reporter_email = 'unknown@campus.local' WHERE reporter_email IS NULL")
    op.alter_column("issues", "reporter_email", nullable=False)


def downgrade() -> None:
    op.drop_column("issues", "reporter_email")
