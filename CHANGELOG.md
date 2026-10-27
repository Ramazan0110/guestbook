# Changelog

Формат: [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/), версии: [SemVer](https://semver.org/lang/ru/).

## [Unreleased]

## [0.2.0] - 2026-10-27

### Added
- Счётчик `likes` в записях (миграция 002, обратно совместима: колонка с DEFAULT 0).

## [0.1.0] - 2026-10-22

### Added
- API гостевой книги: `GET/POST /entries`, `GET /health`, `GET /version`.
- Миграции схемы при старте (`migrations/*.sql`, таблица `schema_migrations`).
- Упаковка: uv, Dockerfile, Docker Compose с PostgreSQL, конфиг через pydantic-settings.
- CI (Ruff + pytest), публикация `:latest` в ghcr.io, релизный workflow по тегу `vX.Y.Z`.
- README и RUNBOOK.
