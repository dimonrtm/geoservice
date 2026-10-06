# День 2: результат реализации схемы первого сохранения

Дата: 1 октября 2026 года. [Спецификация](2026-10-01-day-2-first-save-schema-design.md) и [план](2026-10-01-day-2-first-save-schema-plan.md) реализованы в границах Дня 2.

## Изменения

Новая Alembic revision `b7d2e9f4a6c8` после `f8a7b6c5d4e3` добавляет в schema `work_order`:

- `edit_versions.draft_revision BIGINT NOT NULL DEFAULT 1` с положительным значением. Существующие версии и snapshot сохраняются.
- `edit_version_commands`: durable registry с неизменной identity, последним результатом, разрешёнными переходами и deferred запретом commit незавершённой команды.
- `edit_version_change_events`: история с проверками контекста, геометрии и revision. Обычные `UPDATE`, `DELETE`, `TRUNCATE` запрещены; новое событие добавляется через `INSERT`.

Registry связан с версией и feature. При удалении версии registry удаляется, история остаётся неизменной. Baseline geometry не дублируется в current snapshot; существующий baseline не меняется. `downgrade()` удаляет новые объекты в порядке зависимостей.

Исходники:

- [Migration](../../apps/backend/utility_service/infrastructure/postgresql/alembic/versions/b7d2e9f4a6c8_first_save_schema.py).
- [SQL fixtures](../../apps/backend/tests/integration_tests/first_save_schema_support.py).
- [Migration tests](../../apps/backend/tests/integration_tests/test_first_save_schema_migration.py).
- [Registry tests](../../apps/backend/tests/integration_tests/test_first_save_command_constraints.py).
- [History tests](../../apps/backend/tests/integration_tests/test_first_save_event_constraints.py).

## Проверка

- Три новых тестовых модуля: 78 сценариев; до финального review отдельный прогон — 78 passed, после исправлений все входят в полный успешный прогон.
- `infra\db-tests.cmd`: **125 passed**, exit code 0. Единственное предупреждение — устаревание `crypt` в зависимости `passlib`.
- Проверены upgrade чистой БД, upgrade существующего snapshot, ограничения registry/history, реальные commit/rollback, удаление версии с сохранением истории и атомарный откат ошибки события.
- Ruff и Black проверяют пять новых Python-файлов. `git diff --check` выполнен.
- Все DB-проверки выполнялись в изолированном Compose-проекте `geoservice-db-tests`, БД `geo_test`. Runner удалил тестовые контейнеры; рабочая БД не обновлялась.

Независимый review не обнаружил ошибок DDL. Замечания к доказательности тестов исправлены: identity проверяется вместе с допустимым переходом в success и точным именем constraint; running shape проверяется при INSERT; чужая версия проверяется при одинаковых feature UUID и actor. После исправлений повторён полный прогон.

## Границы результата

ORM/metadata parity, конкурентные сценарии и отдельный полный цикл acceptance upgrade/downgrade/upgrade остаются Дню 3. Save service, авторизация, fingerprint и HTTP replay относятся к последующим дням. Тестовые SQL-транзакции проверяют схему, но не заменяют реализацию этих сервисов.

Некоторые сценарии плана объединены параметризацией. Existing cleanup, ORM, API и seed не изменялись: полный regression не выявил необходимости корректировать их для этой migration. Изменения оставлены unstaged; staging, commit и push не выполнялись.

Отдельная agent memory и repository-change ingest не создавались: контракт, причины решений и ограничения сохранены в документах `docs/sprint_2`; дублирование этих материалов не требуется.

## Исправление проверки CI — 6 октября 2026 года

Обычный `backend_test` выявил ложное срабатывание `test_alembic_upgrade_safety.py`: поиск любого слова `TRUNCATE` принимал `BEFORE TRUNCATE ON ...` в объявлении защитного триггера за очистку таблицы. Предыдущие 125 passed относятся к отдельному DB-набору и не подтверждали прохождение обычного полного `pytest`.

Проверка теперь различает событие триггера (`TRUNCATE ON` / `TRUNCATE OR`) и команду очистки. Добавлены 10 регрессионных сценариев, включая реальные команды с `TABLE`, `ONLY`, quoted identifiers и отдельный `TRUNCATE` после объявления триггера. До исправления воспроизведены 4 failures (3 новых сценария и проверка migration); после исправления обычный полный набор с `RUN_DB_TESTS=0`: **380 passed, 135 skipped, 2 warnings**. Black, Ruff и `git diff --check` прошли. Migration не менялась; DB-набор при этом исправлении повторно не запускался.
