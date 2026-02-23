"""Seed global board game catalog with a default starter set."""

from app.services.seed import seed_board_games_if_empty


def main() -> None:
    """Run board game seed process."""
    seed_board_games_if_empty()
    print("Board game seed completed.")


if __name__ == "__main__":
    main()
