"""Seed top 100 board games into the global catalog (idempotent)."""

from app.services.seed import seed_top100_board_games


def main() -> None:
    """Upsert top 100 board games by normalized_name."""
    inserted, total = seed_top100_board_games()
    print(f"Top100 seed completed. Inserted: {inserted}, attempted: {total}")


if __name__ == "__main__":
    main()
