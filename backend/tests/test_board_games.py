"""Board game catalog tests."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_board_games_unique_by_normalized_name(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    first = client.post(
        "/board-games",
        headers=auth_headers,
        json={"name": "Catan", "source": "seed"},
    )
    assert first.status_code == 201

    second = client.post(
        "/board-games",
        headers=auth_headers,
        json={"name": "  catan  ", "source": "seed"},
    )
    assert second.status_code == 400


def test_get_board_games_search_query_works(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    for title in ["Catan", "Carcassonne", "Azul"]:
        response = client.post(
            "/board-games",
            headers=auth_headers,
            json={"name": title, "source": "seed"},
        )
        assert response.status_code == 201

    search = client.get("/board-games?query=ca", headers=auth_headers)
    assert search.status_code == 200
    names = [item["name"] for item in search.json()]
    assert "Catan" in names
    assert "Carcassonne" in names


def test_get_board_game_by_id(client: TestClient, auth_headers: dict[str, str]) -> None:
    created = client.post(
        "/board-games",
        headers=auth_headers,
        json={"name": "Wingspan", "source": "seed"},
    )
    assert created.status_code == 201
    board_game_id = created.json()["id"]

    response = client.get(f"/board-games/{board_game_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Wingspan"
