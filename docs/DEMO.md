# Сценарий защиты

Повторяет пункты задания. Репозиторий на GitHub должен называться `guestbook`
(так compose собирает имя образа `ghcr.io/<логин>/guestbook`).

## Подготовка (один раз)

```bash
uv lock                                   # создаёт uv.lock, закоммитьте его
git add -A && git commit -m "feat: guestbook v0.1.0"
git remote add origin git@github.com:<логин>/guestbook.git
git push -u origin main
```

В GitHub: Settings → Actions → General → Workflow permissions → *Read and write permissions*.
Для демонстрации сделайте пакет публичным (Packages → guestbook → Package settings → Change visibility).

## Шаг 1. Изменение → зелёный CI → :latest

```bash
git switch -c feat/readme-tweak
# правка, например в README
git commit -am "docs: tweak readme" && git push -u origin feat/readme-tweak
# откройте PR, во вкладке Actions виден зелёный check
# после merge в main: job publish → образ :latest в Packages
```

## Шаг 2. Релиз v0.1.0

```bash
git switch main && git pull
git tag v0.1.0 && git push origin v0.1.0
# Actions → Release → в Packages появился образ v0.1.0
```

## Шаг 3. Релиз v0.2.0 с обратно совместимой миграцией

```bash
git switch -c feat/likes
cp docs/demo/002_add_entries_likes.sql migrations/
```

В `app/db.py` добавьте колонку в запросы: `SELECT id, author, message, likes, created_at ...`
и `RETURNING id, author, message, likes, created_at`; в `app/main.py` добавьте в `EntryOut`
поле `likes: int`. В тестах в `FakeStorage` в строки добавьте `"likes": 0`.
В `CHANGELOG.md` добавьте раздел `## [0.2.0]` (Added: счётчик `likes`, миграция 002).
Затем PR → merge → `git tag v0.2.0 && git push origin v0.2.0`.

## Шаг 4. Выкат и откат

```bash
cp .env.example .env     # DB_PASSWORD, GHCR_OWNER, IMAGE_TAG=v0.1.0
IMAGE_TAG=v0.1.0 docker compose up -d && curl localhost:8000/version   # v0.1.0

IMAGE_TAG=v0.2.0 docker compose pull app
IMAGE_TAG=v0.2.0 docker compose up -d app && curl localhost:8000/version  # v0.2.0
curl localhost:8000/entries                                               # есть likes

IMAGE_TAG=v0.1.0 docker compose up -d app && curl localhost:8000/version  # v0.1.0
curl localhost:8000/entries                                               # данные целы, сервис жив
```

Откат работает, потому что колонка `likes` в базе осталась, а код v0.1.0 её просто не читает.

## Шаг 5. Показать README.md и RUNBOOK.md

## Шаг 6. Что сказать про одно решение

**Почему миграция обратно совместима.** Новая версия кода выкатывается позже, а откатывается
быстрее, чем база. Если миграция ломает старый код (удаляет или переименовывает колонку,
добавляет `NOT NULL` без `DEFAULT`), откат кода больше не спасает: старая версия падает на новой
схеме. Поэтому схему меняем в два этапа (expand/contract): сначала только добавляем, и это
работает с обеими версиями кода. Удаляем старое в отдельном релизе, когда откат на версию,
которая это использовала, уже не нужен.
