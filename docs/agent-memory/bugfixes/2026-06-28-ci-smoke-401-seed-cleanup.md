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
- `apps/backend/tests/db_test_isolation.py`
- `infra/docker-compose.test.yml`
- `infra/db-tests.cmd`

## Summary

Destructive DB integration-тесты с real committed sessions нельзя запускать в
общей demo-БД. Восстановление canonical seed chain после cleanup недостаточно:
оно возвращает demo users и базовые seeds, но не пользовательскую `EditVersion`.
Весь `RUN_DB_TESTS=1` должен использовать отдельный disposable PostGIS и БД с
суффиксом `_test`.

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

Cleanup `remove_canonical_seed_chain()` затем `run_seed_chain()` был добавлен как
локальное исправление CI smoke. Он восстановил demo users, но сохранил скрытый
дефект: `run_seed_chain()` не открывает `EditVersion`. 2026-08-03 полный DB-run
против локальной demo-БД удалил существующую `EditVersion`, вернул `WO-001` в
`assigned` и оставил `0 EditVersion`; последующий `dev-up.cmd` только показал уже
изменённое состояние и не был источником удаления.

Устойчивое правило: tests с `RUN_DB_TESTS=1` выполняются только через
`infra/db-tests.cmd` или эквивалентный isolated Compose-проект
`geoservice-db-tests`. Guard требует `TEST_DATABASE_URL`, отдельное имя БД с
суффиксом `_test` и переключает `DATABASE_URL` до Alembic и collection. Cleanup
общей demo-БД больше не считается допустимой тестовой изоляцией.

## Actions

- 2026-06-28: Причина подтверждена красной postcondition: после concurrent
  integration-теста набор demo user emails был пустым.
- 2026-06-28: Cleanup concurrent open EditVersion regression test исправлен:
  после `remove_canonical_seed_chain(cleanup_session)` выполняется
  `run_seed_chain(cleanup_session)`.
- 2026-06-28: Добавлена postcondition, проверяющая восстановление demo users
  после сценария.
- 2026-08-03: Подтверждена потеря пользовательской `EditVersion` после committed
  cleanup: demo fingerprint содержал тот же `WorkOrder` и новый seed
  `DefaultState`, но `0 EditVersion`.
- 2026-08-03: Весь DB test suite перенесён в standalone `postgis_test/geo_test`
  на `tmpfs`; старый запуск без безопасного `TEST_DATABASE_URL` стал fail-closed.

## Verification

Проверки после изоляции:

- `infra\db-tests.cmd`: весь `tests/integration_tests` выполняется в disposable
  `geo_test`;
- вызов с `RUN_DB_TESTS=1` без `TEST_DATABASE_URL` завершается до SQL-доступа;
- fingerprint `WorkOrder`, `DefaultState`, `EditVersion` в demo-БД совпадает до
  и после полного DB-run;
- после прогона отсутствуют containers и volumes проекта
  `geoservice-db-tests`;
- CI API smoke продолжает работать с отдельным demo Compose после DB-tests.

## Retrieval Hints

CI 401 Unauthorized, urllib HTTPError 401, authenticated API smoke,
seed_utility_dataset, seed_work_orders, seed_demo_users, demo users missing,
remove_canonical_seed_chain, run_seed_chain, committed AsyncSession,
RUN_DB_TESTS, TEST_DATABASE_URL, geo_test, db-tests.cmd, concurrent open
EditVersion, demo fingerprint
