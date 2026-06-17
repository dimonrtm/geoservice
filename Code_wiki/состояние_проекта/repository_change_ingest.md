---
title: Реестр Изменений Нод Code_wiki
type: state
status: active
created: 2026-05-30
updated: 2026-06-17
source: docs/superpowers/specs/2026-06-13-memory-knowledge-base-optimization-design.md
tags: [repository-change, code-wiki, ingest]
---

# Реестр Изменений Нод Code_wiki

Компактный реестр содержательных созданий и обновлений нод `Code_wiki`.
Строка добавляется только когда изменение ноды сохраняет новое устойчивое
техническое знание.

Завершение плана, commit, тестовый прогон и изменение служебных индексов сами
по себе не создают запись. Pre-commit не запускает и не проверяет этот процесс.

## Активный Реестр

| Дата | Нода | Причина | Источник |
| --- | --- | --- | --- |
| 2026-06-17 | [[deployment/docker_compose]] | Уточнен startup order `utility_service`: compose вызывает `bash scripts/start_utility_service.sh`, где после migrations запускаются `seed_demo_users`, `seed_utility_dataset`, `seed_work_orders`, затем API. | `infra/docker-compose.yml`, `infra/docker-compose.override.yml`, `apps/backend/scripts/start_utility_service.sh` |
| 2026-06-17 | [[dev_setup/local_development]] | Зафиксировано, что `dev_up.cmd` через compose запускает backend startup script, а тот создает WorkOrder seed после demo users и utility dataset. | `infra/dev-up.cmd`, `infra/docker-compose.override.yml`, `apps/backend/scripts/start_utility_service.sh`, `apps/backend/seeds/runners/seed_work_orders.py` |
| 2026-06-17 | [[архитектура/data_model]] | Зафиксирована таблица `utility_network.work_orders`, статусы `assigned`/`in_progress`, FK на users/AOI/feeder и create-once seed `WO-001`, где assignee lookup использует `SeedUserRepository`, а feeder/AOI dependencies читаются через `SeedUtilityDatasetRepository`. | `apps/backend/utility_service/infrastructure/postgresql/models/utility_network/work_order.py`, `apps/backend/seeds/specs/seed_work_order_specs.py` |
| 2026-06-17 | [[архитектура/backend]] | Зафиксирован backend foundation `WorkOrderService` без публичного endpoint: service принимает `actor_id`, загружает пользователя через `UserRepository`, применяет assignment guard, active Editor requirement и выполняет переход `assigned -> in_progress` внутри transaction boundary. | `apps/backend/utility_service/use_cases/services/work_order_service.py`, `apps/backend/utility_service/infrastructure/postgresql/repositories/work_order_repository.py` |
| 2026-06-17 | [[правила_и_стиль/testing_strategy]] | Добавлено устойчивое покрытие WorkOrder metadata, seed и use-case rules. | `apps/backend/utility_service/infrastructure/tests/test_network_model_metadata.py`, `apps/backend/seeds/tests/test_seed_work_order_service.py`, `apps/backend/utility_service/use_cases/tests/test_work_order_service.py` |
| 2026-06-16 | [[архитектура/backend]] | Зафиксированы package boundaries `utility_service`: `web_api -> use_cases -> infrastructure`, перенос `deps` и Pydantic schemas в `use_cases`. | `docs/superpowers/specs/2026-06-16-utility-service-refactor-links-design.md`, `apps/backend/utility_service/` |
| 2026-06-16 | [[deployment/docker_compose]] | Зафиксирован runtime contract: service/container `utility_service`, build context `apps/backend` и uvicorn path `utility_service.web_api.main:app`. | `infra/docker-compose.yml`, `apps/backend/Dockerfile` |
| 2026-06-16 | [[сборка/ci_and_quality]] | Обновлен CI contract для image tag `utility_service`, package-local backend tests и integration path `tests/integration_tests`. | `.github/workflows/ci.yml`, `apps/backend/pyproject.toml` |
| 2026-06-16 | [[правила_и_стиль/testing_strategy]] | Зафиксирована новая раскладка backend unit tests по пакетам и integration tests в `apps/backend/tests/integration_tests`. | `apps/backend/utility_service/*/tests`, `apps/backend/tests/integration_tests` |
| 2026-06-13 | [[состояние_проекта/_info]] | Repository-change log заменён компактным реестром с двухусловным gate. | `docs/superpowers/specs/2026-06-13-memory-knowledge-base-optimization-design.md` |
| 2026-06-13 | [[сборка/ci_and_quality]] | Добавлена read-only проверка жизненного цикла agent memory. | `docs/superpowers/specs/2026-06-13-memory-knowledge-base-optimization-design.md` |
| 2026-06-13 | [[правила_и_стиль/testing_strategy]] | Зафиксированы тесты и ручной workflow memory audit. | `docs/superpowers/specs/2026-06-13-memory-knowledge-base-optimization-design.md` |
| 2026-06-15 | [[архитектура/backend]] | Зафиксированы отдельный пакет `seeds` и single-query utility read path. | `apps/backend/app/seeds/`, `apps/backend/app/repositories/utility_network_repository.py` |
| 2026-06-15 | [[архитектура/api_and_realtime]] | Добавлен Editor-only feeder aggregate API и structured utility errors. | `apps/backend/app/api/utility_network.py` |
| 2026-06-15 | [[архитектура/data_model]] | Отражены utility schema, create-once dataset и aggregate spatial query. | `apps/backend/app/models/utility_network/`, `apps/backend/app/seeds/` |
| 2026-06-15 | [[dev_setup/local_development]] | Обновлены module runners demo users и utility dataset. | `apps/backend/app/seeds/runners/` |
| 2026-06-15 | [[deployment/docker_compose]] | Зафиксирован startup order migrations/users/utility/API и no-op restart. | `infra/docker-compose.yml` |
| 2026-06-15 | [[сборка/ci_and_quality]] | Добавлены utility DB tests, reseed после migration cycle и authenticated smoke. | `.github/workflows/ci.yml` |
| 2026-06-15 | [[правила_и_стиль/testing_strategy]] | Добавлено покрытие utility seed, spatial repository, mapping и access API. | `apps/backend/app/tests/test_utility_network_*.py` |
