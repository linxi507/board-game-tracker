"""add google auth fields

Revision ID: f1c2d3e4b5a6
Revises: e3f7c1b72a90
Create Date: 2026-03-09 10:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f1c2d3e4b5a6"
down_revision = "e3f7c1b72a90"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    user_columns = {col["name"] for col in inspector.get_columns("users")}
    user_indexes = {idx["name"] for idx in inspector.get_indexes("users")}
    if "auth_provider" not in user_columns:
        op.add_column(
            "users",
            sa.Column(
                "auth_provider",
                sa.String(length=20),
                nullable=False,
                server_default="local",
            ),
        )

    if "google_sub" not in user_columns:
        op.add_column("users", sa.Column("google_sub", sa.String(length=255), nullable=True))

    op.execute("UPDATE users SET auth_provider = 'local' WHERE auth_provider IS NULL")
    op.alter_column(
        "users",
        "password_hash",
        existing_type=sa.String(length=255),
        nullable=True,
    )

    if "ix_users_google_sub" not in user_indexes:
        op.create_index(
            "ix_users_google_sub",
            "users",
            ["google_sub"],
            unique=True,
            postgresql_where=sa.text("google_sub IS NOT NULL"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    user_columns = {col["name"] for col in inspector.get_columns("users")}
    user_indexes = {idx["name"] for idx in inspector.get_indexes("users")}
    if "ix_users_google_sub" in user_indexes:
        op.drop_index("ix_users_google_sub", table_name="users")

    if "auth_provider" in user_columns:
        op.drop_column("users", "auth_provider")
    if "google_sub" in user_columns:
        op.drop_column("users", "google_sub")

    op.alter_column(
        "users",
        "password_hash",
        existing_type=sa.String(length=255),
        nullable=False,
    )
