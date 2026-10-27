# RUNBOOK — аварийная инструкция

Читайте сверху вниз: сначала быстрая диагностика, потом по симптому. Команды выполняются
в каталоге с `compose.yaml` и `.env`.

## 0. Быстрая диагностика (30 секунд)

```bash
docker compose ps                      # app и db в состоянии running / healthy?
curl -s localhost:8000/health          # {"status":"ok"} — всё хорошо
curl -s localhost:8000/version         # какая версия сейчас выкачена
docker compose logs --tail=50 app      # последние строки лога приложения
```

## 1. Сервис отвечает 5xx или не стартует после выката

Это самый частый случай: **сначала откатываемся, разбираемся потом.**

1. Узнать предыдущую рабочую версию: `git tag --sort=-v:refname | head` или вкладка Packages.
2. Откатить:
   ```bash
   IMAGE_TAG=<предыдущий_тег> docker compose pull app
   IMAGE_TAG=<предыдущий_тег> docker compose up -d app
   ```
3. Проверить: `curl -s localhost:8000/version` и `curl -s localhost:8000/health`.
4. Записать, что откатили и почему (в issue или в CHANGELOG, раздел Unreleased).

Откат кода безопасен, пока миграции обратно совместимы: данные и схема остаются как есть.

## 2. `/health` возвращает 503 (database unavailable)

```bash
docker compose ps db                   # должен быть healthy
docker compose logs --tail=50 db
```

- `db` не запущена: `docker compose up -d db`, затем подождать healthcheck.
- `db` запущена, но приложение не подключается: проверьте, что `DB_PASSWORD` в `.env` тот же,
  с которым создавался том. Пароль задаётся только при **первой** инициализации тома;
  смена `.env` потом не меняет пароль в уже созданной базе.
- Перезапустить приложение: `docker compose restart app`.

## 3. Приложение падает при старте: ошибка миграции

```bash
docker compose logs app | grep -i -B2 -A8 migrat
docker compose exec db psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT * FROM schema_migrations;"
```

1. Откатите версию кода (раздел 1).
2. Миграции выполняются в транзакции: упавшая миграция не записывается в `schema_migrations`
   и не оставляет половинчатых изменений.
3. Исправьте SQL новым релизом (патч-версия), не правьте уже применённый файл миграции.

## 4. Не собирается или не публикуется образ

- Вкладка **Actions** → упавший шаг. Красный `check` — линтер или тесты: `uv run ruff check .`,
  `uv run pytest` локально.
- Ошибка push в ghcr.io: у workflow есть `permissions: packages: write`; в настройках репозитория
  Actions должны быть разрешены.
- Образ есть, но `pull` не работает: пакет приватный. Войдите:
  `echo $GHCR_TOKEN | docker login ghcr.io -u <логин> --password-stdin`
  (токен с правом `read:packages`) или сделайте пакет публичным в его настройках.

## 5. Восстановление данных

База в томе `pgdata`. Резервная копия и восстановление:

```bash
docker compose exec -T db pg_dump -U "$DB_USER" "$DB_NAME" > backup.sql
docker compose exec -T db psql -U "$DB_USER" -d "$DB_NAME" < backup.sql
```

**Не выполняйте** `docker compose down -v`: флаг `-v` удаляет том с данными.

## 6. Как выпустить исправление

1. Исправить в ветке, открыть PR, дождаться зелёного CI, влить в `main`.
2. Дописать CHANGELOG, поставить тег: `git tag v0.1.1 && git push origin v0.1.1`.
3. Дождаться образа `v0.1.1` в Packages, выкатить: `IMAGE_TAG=v0.1.1 docker compose up -d app`.
