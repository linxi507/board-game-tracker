"""Tests for favorites/custom games and custom session logging."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _create_global_game(client: TestClient, headers: dict[str, str], name: str = "Catan") -> int:
    response = client.post(
        "/board-games",
        headers=headers,
        json={"name": name, "source": "seed"},
    )
    if response.status_code == 201:
        return response.json()["id"]
    assert response.status_code == 400
    listing = client.get(f"/board-games?query={name}", headers=headers)
    assert listing.status_code == 200
    item = next((row for row in listing.json() if row["name"] == name), None)
    assert item is not None
    return item["id"]


def test_favorite_toggle_and_list(client: TestClient, auth_headers: dict[str, str]) -> None:
    board_game_id = _create_global_game(client, auth_headers, "Terraforming Mars")

    toggle_on = client.post(f"/me/favorites/{board_game_id}", headers=auth_headers)
    assert toggle_on.status_code == 200
    assert toggle_on.json()["is_favorite"] is True

    favorites = client.get("/me/favorites", headers=auth_headers)
    assert favorites.status_code == 200
    assert any(item["board_game"]["id"] == board_game_id for item in favorites.json())

    toggle_off = client.post(f"/me/favorites/{board_game_id}", headers=auth_headers)
    assert toggle_off.status_code == 200
    assert toggle_off.json()["is_favorite"] is False


def test_favorite_add_and_remove_endpoints(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    board_game_id = _create_global_game(client, auth_headers, "Azul")

    add_response = client.post(
        "/me/favorites",
        headers=auth_headers,
        json={"board_game_id": board_game_id},
    )
    assert add_response.status_code == 200
    assert add_response.json()["is_favorite"] is True

    remove_response = client.delete(f"/me/favorites/{board_game_id}", headers=auth_headers)
    assert remove_response.status_code == 200
    assert remove_response.json()["is_favorite"] is False


def test_create_custom_game_and_session(client: TestClient, auth_headers: dict[str, str]) -> None:
    custom = client.post("/me/custom-games", headers=auth_headers, json={"name": "My Homebrew"})
    assert custom.status_code == 201
    custom_id = custom.json()["id"]

    created_session = client.post(
        "/sessions",
        headers=auth_headers,
        json={
            "user_custom_game_id": custom_id,
            "played_date": "02/21/2026",
            "player_count": 2,
        },
    )
    assert created_session.status_code == 201
    assert created_session.json()["user_custom_game"]["id"] == custom_id
    assert created_session.json()["board_game"] is None


def test_delete_custom_game_succeeds_when_not_used(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    custom = client.post("/me/custom-games", headers=auth_headers, json={"name": "Delete Me"})
    assert custom.status_code == 201
    custom_id = custom.json()["id"]

    deleted = client.delete(f"/me/custom-games/{custom_id}", headers=auth_headers)
    assert deleted.status_code == 204

    listing = client.get("/me/custom-games", headers=auth_headers)
    assert listing.status_code == 200
    assert all(item["id"] != custom_id for item in listing.json())


def test_delete_custom_game_conflict_when_used_by_session(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    custom = client.post("/me/custom-games", headers=auth_headers, json={"name": "Used Custom"})
    assert custom.status_code == 201
    custom_id = custom.json()["id"]

    created_session = client.post(
        "/sessions",
        headers=auth_headers,
        json={
            "user_custom_game_id": custom_id,
            "played_date": "02/24/2026",
            "player_count": 3,
        },
    )
    assert created_session.status_code == 201

    deleted = client.delete(f"/me/custom-games/{custom_id}", headers=auth_headers)
    assert deleted.status_code == 409
    assert deleted.json()["detail"] == "Cannot delete: custom game is used by sessions"
