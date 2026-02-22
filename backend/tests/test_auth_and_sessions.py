"""Integration tests for auth and session flows."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _first_board_game_id(client: TestClient, headers: dict[str, str]) -> int:
    response = client.get("/board-games", headers=headers)
    assert response.status_code == 200
    games = response.json()
    assert isinstance(games, list)
    assert len(games) > 0
    return games[0]["id"]


def test_register_succeeds_and_returns_expected_fields(client: TestClient) -> None:
    payload = {
        "username": "register01",
        "email": "register01@example.com",
        "password": "Password11",
    }
    response = client.post("/auth/register", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["username"] == payload["username"]
    assert body["email"] == payload["email"]
    assert "created_at" in body


def test_login_succeeds_after_register_and_returns_access_token(client: TestClient) -> None:
    register_payload = {
        "username": "login01",
        "email": "login01@example.com",
        "password": "Password11",
    }
    register_response = client.post("/auth/register", json=register_payload)
    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={"identifier": register_payload["username"], "password": register_payload["password"]},
    )
    assert login_response.status_code == 200
    body = login_response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str)
    assert len(body["access_token"]) > 10


def test_auth_me_returns_200_with_token_and_401_without_token(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    with_token = client.get("/auth/me", headers=auth_headers)
    assert with_token.status_code == 200
    assert "email" in with_token.json()
    assert "username" in with_token.json()

    without_token = client.get("/auth/me")
    assert without_token.status_code == 401


def test_create_session_requires_auth(client: TestClient) -> None:
    response = client.post(
        "/sessions",
        json={
            "board_game_id": 1,
            "played_date": "02/17/2026",
            "player_count": 4,
        },
    )
    assert response.status_code == 401


def test_create_session_succeeds_with_auth(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    board_game_id = _first_board_game_id(client, auth_headers)
    payload = {
        "board_game_id": board_game_id,
        "played_date": "02/17/2026",
        "player_count": 4,
        "placement": 1,
        "duration_minutes": 60,
        "notes": "test session",
    }
    response = client.post("/sessions", headers=auth_headers, json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["board_game"]["id"] == board_game_id
    assert body["player_count"] == 4
    assert body["played_at"].startswith("2026-02-17")


def test_list_sessions_returns_array_and_includes_created_session(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    board_game_id = _first_board_game_id(client, auth_headers)
    create_response = client.post(
        "/sessions",
        headers=auth_headers,
        json={
            "board_game_id": board_game_id,
            "played_date": "02/18/2026",
            "player_count": 3,
        },
    )
    assert create_response.status_code == 201
    created_id = create_response.json()["id"]

    list_response = client.get("/sessions", headers=auth_headers)
    assert list_response.status_code == 200
    body = list_response.json()
    assert isinstance(body, list)
    assert any(item["id"] == created_id for item in body)
