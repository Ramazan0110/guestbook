from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app import main
from app.db import get_storage


class FakeStorage:
    """Хранилище в памяти: тестам не нужна настоящая база."""

    def __init__(self, alive: bool = True):
        self.alive = alive
        self.rows: list[dict] = []

    def ping(self) -> bool:
        return self.alive

    def list_entries(self, limit: int) -> list[dict]:
        return list(reversed(self.rows))[:limit]

    def add_entry(self, author: str, message: str) -> dict:
        row = {
            "id": len(self.rows) + 1,
            "author": author,
            "message": message,
            "created_at": datetime.now(UTC),
        }
        self.rows.append(row)
        return row


@pytest.fixture
def storage() -> FakeStorage:
    return FakeStorage()


@pytest.fixture
def client(storage, monkeypatch):
    # Миграции при старте требуют базу, в тестах их отключаем.
    monkeypatch.setattr(main, "apply_migrations", lambda: [])
    main.app.dependency_overrides[get_storage] = lambda: storage
    with TestClient(main.app) as c:
        yield c
    main.app.dependency_overrides.clear()


def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_health_db_down(client, storage):
    storage.alive = False
    assert client.get("/health").status_code == 503


def test_version_endpoint(client):
    r = client.get("/version")
    assert r.status_code == 200
    assert "version" in r.json()


def test_add_and_list_entries(client):
    r = client.post("/entries", json={"author": "  Аня ", "message": " Привет! "})
    assert r.status_code == 201
    assert r.json()["author"] == "Аня"
    assert r.json()["message"] == "Привет!"

    r = client.get("/entries")
    assert r.status_code == 200
    assert [e["message"] for e in r.json()] == ["Привет!"]


@pytest.mark.parametrize(
    "payload",
    [
        {"author": "", "message": "x"},
        {"author": "a", "message": ""},
        {"author": "a", "message": "x" * 501},
        {"message": "no author"},
    ],
)
def test_validation_errors(client, payload):
    assert client.post("/entries", json=payload).status_code == 422
