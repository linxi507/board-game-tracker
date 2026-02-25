"""user favorites custom games and sessions ref

Revision ID: e3f7c1b72a90
Revises: c2a4d8f1e3b7
Create Date: 2026-02-26 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e3f7c1b72a90"
down_revision = "c2a4d8f1e3b7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_favorite_games",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("board_game_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["board_game_id"], ["board_games.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "board_game_id",
            name="uq_user_favorite_games_user_board_game",
        ),
    )
    op.create_index("ix_user_favorite_games_user_id", "user_favorite_games", ["user_id"])
    op.create_index(
        "ix_user_favorite_games_board_game_id",
        "user_favorite_games",
        ["board_game_id"],
    )

    op.create_table(
        "user_custom_games",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("normalized_name", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "normalized_name",
            name="uq_user_custom_games_user_normalized_name",
        ),
    )
    op.create_index("ix_user_custom_games_user_id", "user_custom_games", ["user_id"])

    op.add_column("sessions", sa.Column("user_custom_game_id", sa.Integer(), nullable=True))
    op.create_index("ix_sessions_user_custom_game_id", "sessions", ["user_custom_game_id"])
    op.create_foreign_key(
        "fk_sessions_user_custom_game_id",
        "sessions",
        "user_custom_games",
        ["user_custom_game_id"],
        ["id"],
    )

    op.alter_column("sessions", "board_game_id", existing_type=sa.Integer(), nullable=True)
    op.create_check_constraint(
        "ck_sessions_exactly_one_game_reference",
        "sessions",
        "(board_game_id IS NOT NULL AND user_custom_game_id IS NULL) OR "
        "(board_game_id IS NULL AND user_custom_game_id IS NOT NULL)",
    )


def downgrade() -> None:
    op.drop_constraint("ck_sessions_exactly_one_game_reference", "sessions", type_="check")
    op.alter_column("sessions", "board_game_id", existing_type=sa.Integer(), nullable=False)
    op.drop_constraint("fk_sessions_user_custom_game_id", "sessions", type_="foreignkey")
    op.drop_index("ix_sessions_user_custom_game_id", table_name="sessions")
    op.drop_column("sessions", "user_custom_game_id")

    op.drop_index("ix_user_custom_games_user_id", table_name="user_custom_games")
    op.drop_table("user_custom_games")

    op.drop_index("ix_user_favorite_games_board_game_id", table_name="user_favorite_games")
    op.drop_index("ix_user_favorite_games_user_id", table_name="user_favorite_games")
    op.drop_table("user_favorite_games")
