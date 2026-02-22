"""add username and played_at safety

Revision ID: 9b1f6a2c1d10
Revises: 0048342f4e95
Create Date: 2026-02-18 12:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9b1f6a2c1d10"
down_revision = "0048342f4e95"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    user_columns = {col["name"] for col in inspector.get_columns("users")}
    user_indexes = {idx["name"] for idx in inspector.get_indexes("users")}
    user_unique_constraints = inspector.get_unique_constraints("users")
    unique_names = {uc["name"] for uc in user_unique_constraints if uc.get("name")}
    has_unique_email = any(uc.get("column_names") == ["email"] for uc in user_unique_constraints)
    has_unique_username = any(
        uc.get("column_names") == ["username"] for uc in user_unique_constraints
    )

    if "username" not in user_columns:
        op.add_column("users", sa.Column("username", sa.String(length=20), nullable=True))

    op.execute(
        """
        UPDATE users
        SET username = 'user' || id
        WHERE username IS NULL OR username = ''
        """
    )

    op.alter_column("users", "username", existing_type=sa.String(length=20), nullable=False)

    if not has_unique_username and "uq_users_username" not in unique_names:
        op.create_unique_constraint("uq_users_username", "users", ["username"])
    if "ix_users_username" not in user_indexes:
        op.create_index("ix_users_username", "users", ["username"], unique=False)

    if not has_unique_email and "uq_users_email" not in unique_names:
        op.create_unique_constraint("uq_users_email", "users", ["email"])
    if "ix_users_email" not in user_indexes:
        op.create_index("ix_users_email", "users", ["email"], unique=False)

    session_columns = {col["name"] for col in inspector.get_columns("sessions")}
    if "played_at" not in session_columns:
        op.add_column(
            "sessions",
            sa.Column(
                "played_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    user_columns = {col["name"] for col in inspector.get_columns("users")}
    user_indexes = {idx["name"] for idx in inspector.get_indexes("users")}
    user_unique_constraints = {
        uc["name"] for uc in inspector.get_unique_constraints("users") if uc.get("name")
    }

    if "ix_users_email" in user_indexes:
        op.drop_index("ix_users_email", table_name="users")
    if "uq_users_email" in user_unique_constraints:
        op.drop_constraint("uq_users_email", "users", type_="unique")
    if "ix_users_username" in user_indexes:
        op.drop_index("ix_users_username", table_name="users")
    if "uq_users_username" in user_unique_constraints:
        op.drop_constraint("uq_users_username", "users", type_="unique")
    if "username" in user_columns:
        op.drop_column("users", "username")
