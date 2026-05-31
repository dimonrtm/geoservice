---
title: Repository Snapshot Ingest
type: state
status: active
created: 2026-05-30
updated: 2026-05-30
source: null
tags: [repository-snapshot, code-wiki, ingest]
---

# Repository Snapshot Ingest

Журнал первичных и периодических обзоров уже существующего состояния репозитория через `/ingest repository-snapshot`.

`repository-snapshot` нужен, когда знания нужно собрать не из `RAW_inputs` и не из `git diff`, а из текущей неизмененной кодовой базы. Он пишет только knowledge-документацию в `Code_wiki` и `memory`; код, конфигурация, миграции и тесты не меняются.

## Когда Вызывать

- Первичное наполнение `Code_wiki` для существующего проекта.
- Крупные изменения попали в репозиторий вне текущей агентской задачи.
- `Code_wiki` явно отстает от реальной структуры репозитория.

## Что Фиксировать

- Дату snapshot.
- Область обзора: весь репозиторий, backend, frontend, infra, scripts, docs.
- Прочитанные ключевые источники.
- Созданные или обновленные wiki-ноды.
- Пробелы, риски и follow-up'ы.

## Записи

### 2026-05-30 - Первичный Snapshot Репозитория

Область обзора: весь основной репозиторий без `.git/`, `.obsidian/`, wiki folders как объекта исходного кода, `node_modules/`, build artifacts и временных файлов.

Прочитанные источники:

- `README.md`, `AGENTS.md`, `CONTRIBUTING.md`, `docs/agent-memory/file-map.md`, `memory/project-state.md`, `Code_wiki/index.md`.
- `apps/backend/pyproject.toml`, `apps/backend/app/requirements.txt`, `apps/backend/app/main.py`, `core/settings.py`, `api/*`, `services/*`, `repositories/*`, `models/*`, `domain/*`, `alembic/versions/*`, `Dockerfile`.
- `apps/frontend/package.json`, `src/main.ts`, `App.vue`, `components/*`, `stores/*`, `api/*`, `composables/map/*`, `map/*`, `contracts/*`, `Dockerfile`.
- `.github/workflows/ci.yml`, `infra/docker-compose.yml`, `infra/docker-compose.override.yml`, `infra/docker-compose.full.yml`, `infra/.env.example`, `infra/docker/postgis/init/01-postgis.sql`.
- `scripts/README.md`, `scripts/lint-wiki.py`, `scripts/check-memory-needed.py`, `scripts/tests/*`.

Созданные wiki-ноды:

- [[../архитектура/backend]]
- [[../архитектура/frontend]]
- [[../архитектура/api_and_realtime]]
- [[../архитектура/data_model]]
- [[../dev_setup/local_development]]
- [[../deployment/docker_compose]]
- [[../сборка/ci_and_quality]]
- [[../правила_и_стиль/testing_strategy]]
- [[../глоссарий/technical_terms]]

Обновлены:

- [[../index]]
- [[../../memory/project-state]]
- `docs/agent-memory/file-map.md`
- `docs/agent-memory/sessions/2026-05-30-repository-snapshot-initial-inventory.md`

Наблюдения и пробелы:

- `infra/docker-compose.full.yml` существует, но пустой на дату snapshot.
- `scripts/dev.cmd`, `scripts/docker_full.cmd`, `scripts/infra_dev.cmd` существуют, но пустые на дату snapshot.
- `infra/.env.example` покрывает только DB-переменные и не отражает полный набор backend/frontend env vars.
- Snapshot фиксирует устойчивую структуру и контракты, но не заменяет отдельный API reference или ADR по realtime/editing.
