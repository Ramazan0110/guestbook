# Guestbook

Гостевая книга (FastAPI + PostgreSQL) — капстоун-проект: путь от коммита до прода с CI/CD,
версионированными релизами, откатом и документацией.

**Что умеет сервис:** `GET /entries`, `POST /entries`, `GET /health`, `GET /version`.
Swagger: <http://localhost:8000/docs>.

## Быстрый старт (локально, Docker)

```bash
cp .env.example .env        # задайте DB_PASSWORD
docker compose up --build   # сервис + PostgreSQL
curl localhost:8000/health
curl -X POST localhost:8000/entries -H 'Content-Type: application/json' \
     -d '{"author":"Аня","message":"Привет!"}'
curl localhost:8000/entries
```

## Разработка без Docker

```bash
uv sync                     # ставит Python из .python-version и зависимости из uv.lock
uv run ruff check . && uv run ruff format --check .
uv run pytest
```

Тестам база не нужна: хранилище подменяется заглушкой.

## Конфигурация

Всё через переменные окружения (pydantic-settings, `app/config.py`). Секреты лежат в `.env`
(в `.gitignore`); образец без секретов — `.env.example`.

| Переменная | Назначение | По умолчанию |
|---|---|---|
| `DB_HOST`, `DB_PORT` | адрес PostgreSQL (в compose host = `db`) | `localhost`, `5432` |
| `DB_NAME`, `DB_USER` | база и пользователь | `guestbook` |
| `DB_PASSWORD` | пароль (обязателен) | — |
| `IMAGE_TAG` | какая версия образа выкачена | `latest` |
| `GHCR_OWNER` | владелец образа в ghcr.io | — |

## Как устроен путь в прод

```
push / PR ──► CI: Ruff + pytest
                │ зелёный, ветка main
                ▼
             CD: образ ghcr.io/<owner>/guestbook:latest

git tag vX.Y.Z ──► CI ──► образ ghcr.io/<owner>/guestbook:vX.Y.Z
```

- `main` защищён зелёным CI: публикация образа зависит от него (`needs: check`).
- Релиз делается тегом по semver, изменения описываются в [CHANGELOG.md](CHANGELOG.md).
- Выкат и откат — это смена `IMAGE_TAG` и `docker compose up -d`.

## Выкат и откат

```bash
# выкатить версию
IMAGE_TAG=v0.2.0 docker compose pull app && IMAGE_TAG=v0.2.0 docker compose up -d app
curl localhost:8000/version     # {"version":"v0.2.0"}

# откатиться на предыдущую
IMAGE_TAG=v0.1.0 docker compose up -d app
curl localhost:8000/version     # {"version":"v0.1.0"}
```

Данные при этом не теряются: они лежат в томе `pgdata`, а миграции схемы обратно совместимы.

## Миграции и почему откат безопасен

Миграции — файлы `migrations/NNN_*.sql`, применяются при старте один раз. Правило:
каждая миграция должна работать **и со старой, и с новой версией кода** (expand/contract).
Добавляем колонку с `DEFAULT` — старый код её просто не видит. Удаление и переименование
колонок делаем отдельным релизом, когда ни одна живая версия кода их уже не использует.

## Документы

- [RUNBOOK.md](RUNBOOK.md) — что делать, когда что-то сломалось.
- [CHANGELOG.md](CHANGELOG.md) — история релизов.
- [docs/DEMO.md](docs/DEMO.md) — сценарий демонстрации для защиты.
