---
title: Code_wiki
type: index
status: active
created: 2026-05-30
updated: 2026-06-19
source: null
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
- [[архитектура/frontend]] - Vue/MapLibre приложение, state, map composables и polygon editing.
- [[архитектура/api_and_realtime]] - REST endpoints, WebSocket endpoint, contracts и ошибки.
- [[архитектура/api_contract_first_release_requirements]] - desired API contract Release 1 из RAW source.
- [[архитектура/data_model]] - tables, feature registry, spatial queries, migrations.
- [[dev_setup/local_development]] - локальный Docker Compose сценарий и demo users.
- [[deployment/docker_compose]] - Dockerfile targets и Compose services.
- [[сборка/ci_and_quality]] - CI jobs, build/test/lint gates и wiki checks.
- [[правила_и_стиль/testing_strategy]] - backend/frontend/pipeline тестовая стратегия.
- [[глоссарий/technical_terms]] - термины текущей технической модели и desired vocabulary utility demo.
- [[../Vision_wiki/decisions/release_1_utility_workflow]] - активный desired contract нового Release 1; текущий код требует отдельной compliance matrix.
- [Code compliance matrix](../docs/requirements/release-1-utility-code-compliance.md) - фактические foundation/gap/superseded статусы перед реализацией.
- [Крупноуровневый план по спринтам](../docs/release_1/2026-06-11-release-1-utility-workflow-sprints.md) - семь двухнедельных продуктовых инкрементов нового Release 1.
- [Документы Спринта 1](../docs/release_1/sprint_1/README.md) - календарный план, контракты Дня 1, design/implementation plans Дней 2-4, backend foundation Work Orders Дня 5, EditVersion from Default Дня 8 и отделенные исторические generic-планы.
