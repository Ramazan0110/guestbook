from collections.abc import Iterator
from pathlib import Path
from typing import Protocol

import psycopg
from psycopg.rows import dict_row

from app.config import get_settings

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


class Storage(Protocol):
    def list_entries(self, limit: int) -> list[dict]: ...
    def add_entry(self, author: str, message: str) -> dict: ...
    def ping(self) -> bool: ...


def connect() -> psycopg.Connection:
    return psycopg.connect(get_settings().dsn, row_factory=dict_row)


def apply_migrations() -> list[str]:
    """Применяет *.sql из migrations/ по порядку, один раз каждую.

    Применённые версии хранятся в таблице schema_migrations.
    """
    applied_now: list[str] = []
    with connect() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            "version text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())"
        )
        done = {r["version"] for r in conn.execute("SELECT version FROM schema_migrations")}
        for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
            if path.name in done:
                continue
            conn.execute(path.read_text(encoding="utf-8"))
            conn.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (path.name,))
            applied_now.append(path.name)
    return applied_now


class PostgresStorage:
    def list_entries(self, limit: int) -> list[dict]:
        with connect() as conn:
            return conn.execute(
                "SELECT id, author, message, created_at FROM entries ORDER BY id DESC LIMIT %s",
                (limit,),
            ).fetchall()

    def add_entry(self, author: str, message: str) -> dict:
        with connect() as conn:
            return conn.execute(
                "INSERT INTO entries (author, message) VALUES (%s, %s) "
                "RETURNING id, author, message, created_at",
                (author, message),
            ).fetchone()

    def ping(self) -> bool:
        try:
            with connect() as conn:
                conn.execute("SELECT 1")
            return True
        except psycopg.Error:
            return False


def get_storage() -> Iterator[Storage]:
    yield PostgresStorage()
