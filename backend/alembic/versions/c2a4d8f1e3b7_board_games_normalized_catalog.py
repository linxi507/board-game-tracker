"""board games normalized catalog

Revision ID: c2a4d8f1e3b7
Revises: 9b1f6a2c1d10
Create Date: 2026-02-23 10:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c2a4d8f1e3b7"
down_revision = "9b1f6a2c1d10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    columns = {col["name"] for col in inspector.get_columns("board_games")}
    constraints = inspector.get_unique_constraints("board_games")
    indexes = inspector.get_indexes("board_games")

    if "normalized_name" not in columns:
        op.add_column(
            "board_games",
            sa.Column("normalized_name", sa.String(length=255), nullable=True),
        )

    op.execute(
        """
        UPDATE board_games
        SET normalized_name = lower(trim(regexp_replace(name, '\\s+', ' ', 'g')))
        WHERE normalized_name IS NULL OR normalized_name = ''
        """
    )

    op.alter_column(
        "board_games",
        "normalized_name",
        existing_type=sa.String(length=255),
        nullable=False,
    )
    op.alter_column(
        "board_games",
        "name",
        existing_type=sa.String(length=120),
        type_=sa.String(length=255),
        nullable=False,
    )

    has_normalized_unique = any(
        uc.get("column_names") == ["normalized_name"] for uc in constraints
    )
    if not has_normalized_unique:
        op.create_unique_constraint(
            "uq_board_games_normalized_name",
            "board_games",
            ["normalized_name"],
        )

    index_names = {idx["name"] for idx in indexes}
    if "ix_board_games_name" not in index_names:
        op.create_index("ix_board_games_name", "board_games", ["name"], unique=False)
    if "ix_board_games_normalized_name" not in index_names:
        op.create_index(
            "ix_board_games_normalized_name",
            "board_games",
            ["normalized_name"],
            unique=False,
        )
    if "ix_board_games_source" not in index_names:
        op.create_index("ix_board_games_source", "board_games", ["source"], unique=False)
    if "ix_board_games_source_id" not in index_names:
        op.create_index("ix_board_games_source_id", "board_games", ["source_id"], unique=False)
    if "uq_board_games_source_source_id_not_null" not in index_names:
        op.create_index(
            "uq_board_games_source_source_id_not_null",
            "board_games",
            ["source", "source_id"],
            unique=True,
            postgresql_where=sa.text("source_id IS NOT NULL"),
        )

    # Remove old strict unique(name) if present; normalized_name owns uniqueness now.
    for uc in constraints:
        if uc.get("column_names") == ["name"] and uc.get("name"):
            op.drop_constraint(uc["name"], "board_games", type_="unique")
            break


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    indexes = {idx["name"] for idx in inspector.get_indexes("board_games")}
    constraints = inspector.get_unique_constraints("board_games")

    if "uq_board_games_source_source_id_not_null" in indexes:
        op.drop_index("uq_board_games_source_source_id_not_null", table_name="board_games")
    if "ix_board_games_source_id" in indexes:
        op.drop_index("ix_board_games_source_id", table_name="board_games")
    if "ix_board_games_source" in indexes:
        op.drop_index("ix_board_games_source", table_name="board_games")
    if "ix_board_games_normalized_name" in indexes:
        op.drop_index("ix_board_games_normalized_name", table_name="board_games")
    if "ix_board_games_name" in indexes:
        op.drop_index("ix_board_games_name", table_name="board_games")

    for uc in constraints:
        if uc.get("column_names") == ["normalized_name"] and uc.get("name"):
            op.drop_constraint(uc["name"], "board_games", type_="unique")
            break

    op.create_unique_constraint("board_games_name_key", "board_games", ["name"])
    op.alter_column(
        "board_games",
        "name",
        existing_type=sa.String(length=255),
        type_=sa.String(length=120),
        nullable=False,
    )
    op.drop_column("board_games", "normalized_name")
