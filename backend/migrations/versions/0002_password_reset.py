"""Add password_reset_tokens table and updated_at on users.

Revision ID: 0002_password_reset
Revises: 0001_initial
Create Date: 2025-01-20
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_password_reset"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── password_reset_tokens ──────────────────────────────────────────
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_reset_tokens_user_id", "password_reset_tokens", ["user_id"])
    op.create_index("ix_reset_tokens_token_hash", "password_reset_tokens", ["token_hash"])

    # ── updated_at column on users ─────────────────────────────────────
    op.add_column(
        "users",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("users", "updated_at")
    op.drop_index("ix_reset_tokens_token_hash", table_name="password_reset_tokens")
    op.drop_index("ix_reset_tokens_user_id", table_name="password_reset_tokens")
    op.drop_table("password_reset_tokens")
