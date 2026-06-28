# CI Smoke 401 After Seed Cleanup

Date: 2026-06-28
Type: bugfix
Tags: ci, backend, integration-tests, seed, auth, work-order
Related files:

- `.github/workflows/ci.yml`
- `apps/backend/tests/integration_tests/test_work_order_seed_chain_integration.py`
- `apps/backend/seeds/runners/seed_utility_dataset.py`
- `apps/backend/seeds/runners/seed_work_orders.py`
- `apps/backend/scripts/start_utility_service.sh`

## Summary

Если DB integration-тесты работают с real committed sessions и вызывают
`remove_canonical_seed_chain()`, они не должны оставлять базу без demo users.
Иначе следующий CI authenticated API smoke может упасть с
`urllib.error.HTTPError: HTTP Error 401: Unauthorized` на `/api/v1/auth/login`.

## Context

В CI `utility_service` при старте прогоняет `seed_demo_users`,
`seed_utility_dataset` и `seed_work_orders`. Затем workflow запускает DB
integration-тесты, а после них smoke-шаги. Smoke для utility dataset перед
логином повторно запускает только `python -m seeds.runners.seed_utility_dataset`;
этот runner не создает demo users.

Новый concurrent open EditVersion regression test использовал отдельные
committed `AsyncSession` вместо rollback transaction fixture. Его cleanup
вызывал `remove_canonical_seed_chain()`, что удаляло canonical WorkOrder,
utility dataset и demo users. Сам тест проходил, но следующий smoke логинился
уже в базу без demo users и получал `401 Unauthorized`.

Правило для будущих DB integration-тестов: если тест вне rollback fixture
удаляет canonical seed chain или demo users, cleanup обязан восстановить
стартовое seed-состояние, например `remove_canonical_seed_chain()` затем
`run_seed_chain()`. Добавляйте postcondition, что `{spec.email for spec in
SEED_DEMO_USER_SPECS}` снова присутствует, когда тест может повлиять на
последующие CI smoke-шаги.

## Actions

- 2026-06-28: Причина подтверждена красной postcondition: после concurrent
  integration-теста набор demo user emails был пустым.
- 2026-06-28: Cleanup concurrent open EditVersion regression test исправлен:
  после `remove_canonical_seed_chain(cleanup_session)` выполняется
  `run_seed_chain(cleanup_session)`.
- 2026-06-28: Добавлена postcondition, проверяющая восстановление demo users
  после сценария.

## Verification

Проверки после исправления:

- `docker compose -f docker-compose.yml exec -T utility_service env RUN_DB_TESTS=1 pytest tests/integration_tests/test_work_order_seed_chain_integration.py::test_concurrent_open_seeded_edit_version_returns_one_created_and_one_reopened -q`
- `docker compose -f docker-compose.yml exec -T utility_service env RUN_DB_TESTS=1 pytest tests/integration_tests/test_work_order_seed_chain_integration.py -q`
- CI utility authenticated API smoke: `seed_utility_dataset` затем login и
  feeder API вернули `utility dataset api ok`.
- CI workspace authenticated API smoke: `seed_work_orders` затем login,
  open EditVersion и workspace API вернули `workspace api ok`.

## Retrieval Hints

CI 401 Unauthorized, urllib HTTPError 401, authenticated API smoke,
seed_utility_dataset, seed_work_orders, seed_demo_users, demo users missing,
remove_canonical_seed_chain, run_seed_chain, committed AsyncSession,
RUN_DB_TESTS, concurrent open EditVersion
