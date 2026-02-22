"""global board games and user library and sessions

Revision ID: 0048342f4e95
Revises: 20260216_0001
Create Date: 2026-02-16 05:32:33.452878
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0048342f4e95'
down_revision = '20260216_0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("sessions")
    op.drop_table("games")

    op.create_table(
        "board_games",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=True),
        sa.Column("source_id", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "user_games",
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
            name="uq_user_games_user_board_game",
        ),
    )
    op.create_index("ix_user_games_user_id", "user_games", ["user_id"], unique=False)
    op.create_index(
        "ix_user_games_board_game_id",
        "user_games",
        ["board_game_id"],
        unique=False,
    )

    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("board_game_id", sa.Integer(), nullable=False),
        sa.Column(
            "played_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("player_count", sa.Integer(), nullable=False),
        sa.Column("placement", sa.Integer(), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "player_count >= 1",
            name="ck_sessions_player_count_ge_1",
        ),
        sa.CheckConstraint(
            "placement IS NULL OR (placement >= 1 AND placement <= player_count)",
            name="ck_sessions_placement_between_1_and_player_count",
        ),
        sa.CheckConstraint(
            "duration_minutes IS NULL OR duration_minutes >= 1",
            name="ck_sessions_duration_minutes_ge_1",
        ),
        sa.ForeignKeyConstraint(["board_game_id"], ["board_games.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"], unique=False)
    op.create_index(
        "ix_sessions_board_game_id",
        "sessions",
        ["board_game_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_sessions_board_game_id", table_name="sessions")
    op.drop_index("ix_sessions_user_id", table_name="sessions")
    op.drop_table("sessions")

    op.drop_index("ix_user_games_board_game_id", table_name="user_games")
    op.drop_index("ix_user_games_user_id", table_name="user_games")
    op.drop_table("user_games")

    op.drop_table("board_games")

    op.create_table(
        "games",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("game_id", sa.Integer(), nullable=False),
        sa.Column("played_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("players_count", sa.Integer(), nullable=False),
        sa.Column("my_rank", sa.Integer(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "players_count >= 1",
            name="ck_sessions_players_count_ge_1",
        ),
        sa.CheckConstraint(
            "duration_minutes > 0",
            name="ck_sessions_duration_minutes_gt_0",
        ),
        sa.CheckConstraint(
            "my_rank >= 1 AND my_rank <= players_count",
            name="ck_sessions_my_rank_between_1_and_players_count",
        ),
        sa.ForeignKeyConstraint(["game_id"], ["games.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
