"""Board game catalog tests."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_board_games_unique_by_normalized_name(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    base_name = "Unique Test Game"
    first = client.post(
        "/board-games",
        headers=auth_headers,
        json={"name": base_name, "source": "seed"},
    )
    assert first.status_code == 201

    second = client.post(
        "/board-games",
        headers=auth_headers,
        json={"name": "  unique   test   game ", "source": "seed"},
    )
    assert second.status_code == 400


def test_get_board_games_search_query_works(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    search = client.get("/board-games/search?query=Root", headers=auth_headers)
    assert search.status_code == 200
    rows = search.json()
    assert isinstance(rows, list)
    assert any(item["name"] == "Root" for item in rows)
    first = rows[0]
    assert "key" in first
    assert "source" in first
    assert "is_favorite" in first


def test_get_board_game_by_id(client: TestClient, auth_headers: dict[str, str]) -> None:
    name = "Unique Lookup Game"
    created = client.post(
        "/board-games",
        headers=auth_headers,
        json={"name": name, "source": "seed"},
    )
    assert created.status_code == 201
    board_game_id = created.json()["id"]

    response = client.get(f"/board-games/{board_game_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["name"] == name
