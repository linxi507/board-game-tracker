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


def test_board_games_limit_and_offset_are_respected(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    base = "Limit Offset Check"
    for index in range(25):
        response = client.post(
            "/board-games",
            headers=auth_headers,
            json={"name": f"{base} {index:02d}", "source": "seed"},
        )
        assert response.status_code in (201, 400)

    first_page = client.get(
        "/board-games?query=Limit%20Offset%20Check&limit=20&offset=0",
        headers=auth_headers,
    )
    assert first_page.status_code == 200
    first_items = first_page.json()
    assert len(first_items) == 20
    assert first_page.headers.get("X-Limit") == "20"
    assert first_page.headers.get("X-Offset") == "0"

    second_page = client.get(
        "/board-games?query=Limit%20Offset%20Check&limit=20&offset=20",
        headers=auth_headers,
    )
    assert second_page.status_code == 200
    second_items = second_page.json()
    assert len(second_items) >= 5
