---
title: Code_wiki
type: index
status: active
created: 2026-05-30
updated: 2026-07-03
source: repository-change:2026-07-03
tags: [code-wiki, technical-knowledge]
---

# Code_wiki

Технические знания для людей и агентов, работающих с кодом GeoService.

## Структура

- [[_templates/_info]] - шаблоны ADR, сервисов, runbook'ов, API endpoints и postmortems.
- [[архитектура/_info]] - архитектурные заметки и ADR.
- [[dev_setup/_info]] - локальная разработка.
- [[сборка/_info]] - сборка и CI.
- [[deployment/_info]] - deployment notes, runbook'и и postmortems.
- [[правила_и_стиль/_info]] - инженерные соглашения и правила review.
- [[глоссарий/_info]] - технический глоссарий.
- [[состояние_проекта/_info]] - текущее техническое состояние проекта,
  repository snapshot и реестр изменений нод `Code_wiki`.
- [[состояние_проекта/repository_snapshot]] - журнал `/ingest repository-snapshot`.
- [[состояние_проекта/repository_change_ingest]] - компактный реестр
  `/ingest repository-change`.

## Текущий Repository Snapshot

- [[архитектура/backend]] - backend FastAPI, auth, services, repositories и PostGIS.
- [[архитектура/frontend]] - Vue/MapLibre приложение, role-specific shell, state, map composables и polygon editing.
- [[архитектура/api_and_realtime]] - REST endpoints, WebSocket endpoint, Work Orders/Workspace API, contracts и ошибки.
- [[архитектура/api_contract_first_release_requirements]] - desired API contract Release 1 из RAW source.
- [[архитектура/data_model]] - tables, feature registry, spatial queries, schema boundaries, AOI scope и migration contracts.
- [[dev_setup/local_development]] - локальный Docker Compose сценарий и demo users.
- [[deployment/docker_compose]] - Dockerfile targets и Compose services.
- [[сборка/ci_and_quality]] - CI jobs, build/test/lint gates и wiki checks.
- [[правила_и_стиль/testing_strategy]] - backend/frontend/pipeline тестовая стратегия.
- [[глоссарий/technical_terms]] - термины текущей технической модели и desired vocabulary utility demo.
- [[../Vision_wiki/decisions/release_1_utility_workflow]] - активный desired contract нового Release 1; текущий код требует отдельной compliance matrix.
- [Code compliance matrix](../docs/requirements/release-1-utility-code-compliance.md) - фактические foundation/gap/superseded статусы перед реализацией.
- [Крупноуровневый план по спринтам](../docs/release_1/2026-06-11-release-1-utility-workflow-sprints.md) - семь двухнедельных продуктовых инкрементов нового Release 1.
- [Документы Спринта 1](../docs/release_1/sprint_1/README.md) - календарный план, контракты Дня 1, design/implementation plans Дней 2-4, backend foundation Work Orders Дня 5, EditVersion from Default Дня 8, Мои наряды Дня 11 и отделенные исторические generic-планы.

## Свежие Repository-Change Знания

- 2026-07-03: [[архитектура/api_and_realtime]] и [[архитектура/frontend]]
  отражают auth session strategy без долговременного `access_token` в
  `localStorage`: backend выдает HttpOnly `geoservice_session`, хранит только
  SHA-256 hash в `user.auth_sessions`, refresh атомарно ротирует session, а
  frontend держит Bearer token только in-memory и восстанавливается через
  cookie refresh.
- 2026-07-02: [[архитектура/api_and_realtime]], [[архитектура/backend]],
  [[архитектура/frontend]] и [[правила_и_стиль/testing_strategy]]
  отражают WebSocket auth через short-lived single-use ticket:
  HTTP Bearer выдает ticket, WebSocket принимает только `?ticket=...`,
  backend consumes ticket атомарно, frontend запрашивает новый ticket на
  initial connect/reconnect, а тесты проверяют отсутствие `token=`.
- 2026-06-29: [[архитектура/api_and_realtime]] и [[архитектура/frontend]]
  отражают strict structured error contract `{code, message, correlationId}`
  без `detail`/`details` для auth/utility/workflow ошибок; invalid login
  возвращает `INVALID_CREDENTIALS`, а `LoginScreen` читает только `message`.
- 2026-06-21: [[архитектура/api_and_realtime]] и [[архитектура/data_model]] отражают Workspace API `GET /api/v1/work-orders/{workOrderId}/edit-versions/{editVersionId}/workspace`, перенос AOI в `work_order` и чтение workspace из edit version с фильтрацией по `WorkOrder.scope.aoi`.
- 2026-06-22: [[архитектура/data_model]] отражает repair/idempotent migration contract для `c9d0e1f2a3b4`, `f2b3c4d5e6a7`, `a8c1f2d3e4b5`, `e4b7a9c2d5f8` и `d3a01f4e9c21`.
- 2026-06-22: [[архитектура/api_and_realtime]], [[архитектура/frontend]], [[dev_setup/local_development]], [[сборка/ci_and_quality]] и [[правила_и_стиль/testing_strategy]] отражают экран `Мои наряды`: Editor-only assigned list API, frontend shell с пустой basemap, локальную подсветку строки без открытия `EditVersion` и jsdom component tests.
- 2026-06-26: [[сборка/ci_and_quality]] и [[правила_и_стиль/testing_strategy]] отражают Day 13 full path API smoke: CI запускает `tests/smoke/full_path_workspace_smoke.py` внутри `utility_service`, проверяя `login -> assigned-to-me -> open/reopen EditVersion -> workspace` для seeded `WO-001`.
