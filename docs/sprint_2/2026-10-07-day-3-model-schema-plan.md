# День 3 Sprint 2: план реализации соответствия моделей схеме

> **Для агента-исполнителя:** план выполнен последовательно в текущем чате через `superpowers:executing-plans` по запросу пользователя 7 октября 2026 года. Правило репозитория запрещает агентам staging, commit и push. Фактические результаты и решения описаны в [отчёте](2026-10-07-day-3-model-schema-implementation-report.md).

**Цель:** отразить объекты Дня 2 в ORM и доказать соответствие metadata, корректность ORM-транзакций, обратимость структуры миграции и поведение конкурентного удаления версии.

**Архитектура:** две явные declarative models и поле revision в существующей модели. Alembic создаёт полноценную схему; независимые metadata, catalog и transaction tests проверяют её контракт. Сервисы Save/Revert не добавляются.

**Стек:** Python 3.12, SQLAlchemy 2.0.36, Alembic 1.14.0, asyncpg 0.30.0, GeoAlchemy2 0.16.0, PostgreSQL 16 / PostGIS 3.4, pytest.

**Спецификация:** [День 3: соответствие моделей схеме](2026-10-06-day-3-model-schema-design.md), принята пользователем 7 октября 2026 года.

## Общие ограничения

- Scope: `EditVersion.draft_revision`, `work_order.edit_version_commands`, `work_order.edit_version_change_events` и их непосредственные зависимости. Не проводить аудит всей metadata.
- Полноценную схему создаёт только Alembic. Не добавлять triggers/functions в `create_all`, не переписывать существующую revision ради повторного использования runtime-констант.
- У history нет FK, relationships/cascade и spatial indexes. Geometry — LINESTRING, SRID 4326, dimension 2, `spatial_index=False`.
- `response_payload` использует `JSONB(none_as_null=True)`; `command_id` передаётся явно, не генерируется ORM.
- Запись: lock root → INSERT running + flush → UPDATE snapshot/root/terminal command + flush → INSERT event → общий commit.
- DB tests только в isolated Compose `geoservice-db-tests`, disposable `geo_test`. Не использовать demo-БД, не отключать isolation guard.
- Человекочитаемые артефакты — на русском в `docs/sprint_2`. Код/API/идентификаторы не переводить.
- `git add`, `git commit`, `git push` запрещены агентам. Все изменения оставить unstaged.

## Особое внимание при ревью

1. Явный `response_payload=None` при INSERT и повторной попытке должен давать SQL NULL, а JSON null должен отвергаться формой running/rejected — задача 3.
2. BIGINT revision выше `2**31-1` не должна сужаться до INTEGER при ORM round-trip — задача 3.
3. Случайный предварительный импорт моделей не должен скрывать пропуск Alembic регистрации — задача 1, отдельный процесс.
4. После downgrade current geometry уже отличается от baseline; повторное событие обязано описывать новый переход, а не повторять старую fixture — задача 4.
5. Видимое ожидание конкурентного запроса должно относиться к INSERT trigger, а не предшествующему UPDATE root; deadlock не равен успешному ожиданию — задача 5.

## Файлы и ответственность

Пути ниже относительны `apps/backend`, кроме явно указанных `docs/` и `infra/`.

| Файл | Действие и ответственность |
| --- | --- |
| `utility_service/infrastructure/postgresql/models/work_order/edit_version_command.py` | Создать: registry model и state enum |
| `utility_service/infrastructure/postgresql/models/work_order/edit_version_change_event.py` | Создать: history model и event type enum |
| `utility_service/infrastructure/postgresql/models/work_order/edit_version.py` | Изменить: revision и CHECK |
| `utility_service/infrastructure/postgresql/models/work_order/__init__.py` | Изменить: exports четырёх новых публичных типов |
| `utility_service/infrastructure/postgresql/alembic/env.py` | Изменить: импорт обеих моделей |
| `utility_service/infrastructure/tests/test_network_model_metadata.py` | Изменить: точные exports и contract EditVersion |
| `utility_service/infrastructure/tests/test_first_save_model_metadata.py` | Создать: полный metadata contract новых объектов и изолированная регистрация Alembic |
| `tests/integration_tests/test_first_save_model_parity.py` | Создать: metadata против migrated PostgreSQL |
| `tests/integration_tests/first_save_orm_support.py` | Создать: узкие ORM fixtures для commit/rollback; не production service |
| `tests/integration_tests/test_first_save_model_integration.py` | Создать: ORM запись/чтение и отказоустойчивость транзакции |
| `tests/integration_tests/test_first_save_schema_migration.py` | Расширить: полный lifecycle и восстановление guards |
| `tests/integration_tests/test_first_save_event_concurrency.py` | Создать: две очередности INSERT/DELETE |
| `docs/sprint_2/2026-10-07-day-3-model-schema-implementation-report.md` | Создать после исполнения: реальные результаты и ограничения |
| `docs/sprint_2/README.md` | Обновить ссылки и статусы артефактов |

Использовать существующий `tests/integration_tests/first_save_schema_support.py`: `seed_context(connection, **overrides)`, `snapshot_context(connection, edit_version_id)`, `run_scenario(scenario)`, `run_committed_scenario(scenario)`, `persist_sql_change(...)`, `insert_event(...)`. Этот модуль остаётся независимым от новых ORM models.

## Команды проверки

Все команды этого раздела запускаются из корня репозитория в PowerShell. Они используют существующий Docker dev image и отдельный test Compose, без установки зависимостей в пользовательское окружение.

Сборка после изменения исходников:

```powershell
docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml build backend_db_tests
```

Автономные metadata tests (команда M):

```powershell
docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml run --rm --no-deps -e RUN_DB_TESTS=0 backend_db_tests python -m pytest utility_service/infrastructure/tests/test_network_model_metadata.py utility_service/infrastructure/tests/test_first_save_model_metadata.py --tb=short
```

Фокусированный DB-прогон (команда D; последний путь заменяется файлом текущей задачи):

```powershell
docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml run --rm backend_db_tests python -m pytest tests/integration_tests/test_first_save_model_parity.py --tb=short
```

Compose запускает только test PostGIS; `apps/backend/conftest.py` проверяет изоляцию и применяет head до collection. Не задавать `DATABASE_URL` равным `TEST_DATABASE_URL` вручную: guard сам переключает его. После DB-прогонов обязательно выполнить cleanup даже при ошибке:

```powershell
docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml down -v --remove-orphans
```

Ожидаемый успех каждой проверки — exit code 0 и соответствующие tests passed. Skip DB tests не считается подтверждением. Ошибки Docker/network/import не являются ожидаемым RED тестом; сначала восстановить окружение. После каждой правки собирать image перед следующим прогоном, поскольку исходники копируются Dockerfile, а не монтируются.

## Задача 1. Declarative models и регистрация metadata

**Файлы:** пять production-файлов моделей/exports/env и два metadata test-файла из таблицы.

**Интерфейсы:**

- `EditVersion.draft_revision: Mapped[int]`, BIGINT NOT NULL DEFAULT 1.
- `EditVersionCommand(Base)`, `EditVersionCommandState`: RUNNING=`running`, SUCCEEDED=`succeeded`, REJECTED=`rejected`.
- `EditVersionChangeEvent(Base)`, `EditVersionChangeEventType`: CHANGE_SET_PERSISTED=`change_set_persisted`, CHANGE_SET_CLEARED=`change_set_cleared`.
- Колонки обеих новых моделей, длины и все имена constraints точно заданы разделом 3 спецификации. UUID — `Mapped[uuid.UUID]`; JSON payload — `Mapped[dict[str, Any] | None]`; даты — `datetime`, nullable completed_at — `datetime | None`; geometry соответствует принятому стилю `Mapped[object]`.

- [x] Добавить metadata tests `test_command_metadata_contract`, `test_event_metadata_contract`, `test_revision_metadata_contract`. Зафиксировать точные колонки, defaults, типы, nullable, все определения CHECK и имена/колонки constraints. Основные отрицательные ожидания:

```python
assert len(EditVersionCommand.__table__.foreign_key_constraints) == 2
assert not EditVersionChangeEvent.__table__.foreign_key_constraints
assert not EditVersionChangeEvent.__table__.indexes
assert EditVersionCommand.__table__.c.response_payload.type.none_as_null is True
assert EditVersionChangeEvent.__table__.c.before_geometry.type.spatial_index is False
assert EditVersionChangeEvent.__table__.c.after_geometry.type.srid == 4326
```

- [x] Добавить `test_alembic_registers_first_save_models_in_fresh_process`. В дочернем Python процессе выполнить реальный `env.py` через `runpy.run_path`; подменить только Alembic context: `config=Config()`, `is_offline_mode=True`, `configure` захватывает `target_metadata`, `begin_transaction` возвращает `nullcontext`, `run_migrations` ничего не делает. До env не импортировать модели. Проверить обе schema-qualified таблицы и revision в захваченной metadata. БД не подключать.
- [x] Обновить точные ожидания exports и `EditVersion` в существующем test-файле; проверить отсутствие новых relationships и успешный `configure_mappers()`.
- [x] Собрать image и запустить M. До реализации ожидаются ошибки отсутствующих новых imports/колонки — сохранить фактический RED.
- [x] Реализовать модели и enums; явно именовать PK через `PrimaryKeyConstraint`, перенести CHECK из migration без её runtime-импорта, сохранить non-native enums и длины 16/32. У revision использовать server default `1`; дополнительные client defaults не нужны. Добавить exports/imports.
- [x] Повторить M. Ожидается PASS; отсутствие enum-generated CHECK и лишних geometry indexes проверено точными множествами.

## Задача 2. Parity с реально применённой migration

**Файл:** `tests/integration_tests/test_first_save_model_parity.py`.

**Потребляет:** модели задачи 1, `run_scenario`, migrated schema из conftest.

**Локальные интерфейсы:** `assert_table_parity(connection: AsyncConnection, table: Table) -> None`; `canonical_check_definitions(connection: AsyncConnection, table: Table) -> dict[str, str]`. Эти helpers остаются в одном test-модуле, не становятся универсальным framework.

- [x] Написать `test_first_save_tables_match_migrated_schema` для двух новых таблиц: columns/types/nullability/defaults, PK/FK/UNIQUE, CHECK, indexes, geometry typmod. Expected contract брать из спецификации, metadata — из моделей, actual — из PostgreSQL; не строить expected из actual.
- [x] Сравнивать CHECK после PostgreSQL parsing: в rollback transaction создать отдельную TEMP probe table с теми же именами/типами колонок и только CHECK из metadata; получить `pg_get_constraintdef` для probe и migrated table. TEMP probe не содержит FK, PK, indexes или triggers, не использует `Base.metadata.create_all()` и не заменяет схему приложения. Сравнить именованные определения, затем удалить probe. Для колонок брать storage types (VARCHAR вместо SAEnum), чтобы probe не создавал enum checks/типы; у Geometry выключить automatic spatial index. Это избегает самодельного SQL parser и удаления значимых частей выражения.
- [x] Добавить `test_first_save_dependency_contract`: новая revision, referenced composite key snapshot, FK actions associations/features и ровно один GiST snapshot. Проверить `geometry` type/SRID и `spatial_index=False` в metadata.
- [x] Добавить catalog assertions: история имеет ровно два B-tree backing indexes, registry — PK backing index и `ix_ev_commands_version_feature`; проверить отсутствие лишних indexes/FK, наличие четырёх функций/пяти triggers и deferred terminal trigger. Различать UNIQUE constraint и его backing index.
- [x] Выполнить D для этого файла. Новая проверка существующей схемы может сразу пройти; не придумывать обязательный RED. При расхождении воспроизвести конкретную причину и исправить mapping/helper, не ослабляя ожидаемый контракт и не меняя migration без разбора. Отсутствующая reflected FK action означает PostgreSQL default NO ACTION; RESTRICT не нормализовать к NO ACTION.
- [x] Повторить фокусированную проверку после исправлений; сохранить PASS и выполнить cleanup. Для defaults сравнивать каноническое PostgreSQL представление или вычисленное значение, не стирать произвольные casts регулярным выражением.

## Задача 3. ORM round-trip и границы transaction

**Файлы:** `first_save_orm_support.py`, `test_first_save_model_integration.py` в integration_tests.

**Потребляет:** модели задачи 1, `seed_context`, `run_committed_scenario`, `BASELINE`, `MOVED` из SQL support.

**Производит test-only helper:** `persist_orm_change(session: AsyncSession, context: dict[str, UUID], command_id: UUID, *, before_geometry: str, after_geometry: str) -> None`. Он выполняет lock root, running INSERT/flush, snapshot/revision/terminal UPDATE/flush, event INSERT/flush; commit остаётся вызывающему тесту. Geometry передаётся через `WKTElement(..., srid=4326)`. Production repositories/services не вызываются и не добавляются.

- [x] Добавить `test_orm_change_round_trip`: committed SQL setup, вызов helper в отдельной session, общий commit, чтение третьей session. Проверить command ID/state, JSON payload object, timezone-aware даты, before/after EWKB/SRID и revisions `1 -> 2`.
- [x] Добавить `test_orm_revision_server_default_and_reopen` и параметризацию `test_orm_bigint_revision_round_trip` со стартом `2**31 + 7`. Создание root через ORM без revision даёт 1; UPDATE `last_opened_at` не меняет revision; event BIGINT значения сохраняются без сужения.
- [x] Добавить `test_orm_rejection_uses_sql_null`, `test_orm_json_null_is_rejected`, `test_orm_access_retry`: явный None проверяется SQL `IS NULL`; явный `JSON.NULL` для running/rejected отклоняется; retry проходит через настоящий flush running и завершение, identity/created_at сохраняются.
- [x] Добавить `test_orm_running_commit_is_rejected` с настоящим commit, не savepoint. После SQLSTATE 23514 rollback и новая session доказывают отсутствие command.
- [x] Добавить `test_orm_event_failure_rolls_back_change`: после flush изменённых root/feature/command вызвать invalid event, например `after_geometry=before_geometry`; rollback возвращает original snapshot/revision и убирает новую command/history.
- [x] Добавить `test_orm_history_survives_parent_deletion`, `test_orm_history_update_delete_rejected`. Использовать full fixture с associations; удалить associations перед root, затем читать orphan history новой session. UPDATE/DELETE history через ORM должны дать DB rejection, после rollback содержание неизменно.
- [x] Собрать image и выполнить D для ORM test-файла до реализации helper; ожидается отсутствие helper. Реализовать helper и локальные fixtures, повторить прогон; любые дефекты mappings исправлять минимально, сохраняя sequence flush и внешний commit.
- [x] Выполнить M и D для parity/ORM после изменения модели. Не дублировать все SQL constraint permutations Дня 2: новые tests доказывают именно путь ORM. Cleanup обязателен.

## Задача 4. Полный lifecycle с populated schema

**Файл:** `tests/integration_tests/test_first_save_schema_migration.py`.

**Потребляет:** существующие SQL support functions. ORM helpers не использовать при работе на предыдущей revision: в ней нет новой колонки.

- [x] Добавить `test_first_save_populated_upgrade_downgrade_upgrade` с фиксированными revision IDs `f8a7b6c5d4e3` и `b7d2e9f4a6c8`. До первого upgrade заполнить SQL context, зафиксировать snapshot и baseline.
- [x] После первого upgrade проверить revision 1 и отсутствие synthetic commands/events; создать SQL change и сохранить состояние непосредственно перед downgrade.
- [x] После downgrade проверить отсутствие новых таблиц, четырёх функций, пяти triggers, revision column/CHECK. Проверить сохранение root без revision, features, associations и baseline. Проверять catalog безопасными запросами, не приводя имя уже удалённой таблицы к regclass.
- [x] После повторного upgrade проверить структуру/количество объектов, пустые registry/history и revision 1. Новое событие строить как обратное фактическое изменение `MOVED -> BASELINE`, тип `change_set_cleared`, operation `unchanged`, revision `1 -> 2`.
- [x] В отдельных transaction проверить реальные guards после повторного upgrade: running commit rejected, прямой terminal INSERT rejected, корректное событие committed, неверный context rejected, UPDATE/DELETE/TRUNCATE history rejected. Negative cases не должны быть отклонены случайным UNIQUE violation: использовать корректную исходную fixture и точный constraint/SQLSTATE.
- [x] Запустить D для migration test-файла. Проверка существующей migration может быть зелёной сразу; исправлять test defects по фактической причине, не изменять миграцию ради ожидаемого результата. В `finally` восстановить head; все engine/session закрыть до Alembic DDL. Сохранить отдельный existing fresh-upgrade test.

## Задача 5. Конкурентные проверки и итоговый regression

**Файл:** `tests/integration_tests/test_first_save_event_concurrency.py`; затем отчёт и индекс Sprint 2.

**Потребляет:** `run_committed_scenario`, `seed_context`, `persist_sql_change(..., emit_event=False)`, `insert_event`.

**Локальные интерфейсы:** `wait_until_blocked(observer: AsyncConnection, *, waiter_pid: int, blocker_pid: int, timeout: float = 5.0) -> None`; `delete_version(connection: AsyncConnection, edit_version_id: UUID) -> None`. Удаление блокирует root через FOR UPDATE, удаляет associations, затем root. Это только test helper.

- [x] Добавить `test_event_insert_blocks_root_deletion`. Setup commit создаёт подходящие root/snapshot/succeeded command без history. Первая transaction вставляет history и остаётся открытой. Вторая запускает удаление, observer подтверждает blocker PID через `pg_blocking_pids`. Commit INSERT освобождает удаление; после его commit history неизменна, root/commands/features/associations отсутствуют, baseline сохранён.
- [x] Добавить `test_root_deletion_blocks_and_rejects_event_insert`. Первая transaction удаляет root и остаётся открытой. Вторая выполняет INSERT history; observer подтверждает ожидание. После commit DELETE вставка завершается SQLSTATE `23514`, constraint `ck_ev_events_context`; rollback второй transaction, нового события нет.
- [x] Реализовать bounded polling observer через monotonic deadline; это короткие проверки реального состояния PostgreSQL, а не фиксированная задержка как доказательство. Операции ограничить общим deadline 15 секунд; неожиданные timeout/deadlock приводят к failure. Observer использует отдельное соединение, два рабочих соединения заняты transactions.
- [x] Выполнить D для concurrency test-файла. Обязательно дождаться результатов обеих async tasks; в `finally` отменить/дождаться незавершённых задач и откатить оставшиеся transactions. Ошибки не поглощать. После прохода выполнить cleanup.
- [x] Собрать итоговый image и выполнить M, обычный backend suite и format/lint в том же dev image:

```powershell
docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml run --rm --no-deps -e RUN_DB_TESTS=0 backend_db_tests python -m pytest --tb=short
docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml run --rm --no-deps -e RUN_DB_TESTS=0 backend_db_tests python -m black --check .
docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml run --rm --no-deps -e RUN_DB_TESTS=0 backend_db_tests python -m ruff check .
```

- [x] Выполнить полный isolated DB suite и проверку whitespace:

```powershell
.\infra\db-tests.cmd
git diff --check
```

- [x] Проверить отсутствие оставшихся контейнеров test project через `docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml ps -a`; при остатках выполнить cleanup. Не запускать повторно успешный полный suite без новых изменений/неразрешённых сомнений.
- [x] Записать фактические команды, результаты и ограничения в отчёт; обновить README. Не переносить прошлые 125/380 passed как результаты новой реализации. Проверить `git status --short`, оставить все изменения unstaged.

## Самопроверка и передача исполнения

Соответствие спецификации: модели/exports — задача 1; schema parity/functions/triggers — задача 2; ORM/NULL/BIGINT/rollback — задача 3; populated lifecycle — задача 4; конкуренция и regression — задача 5. Все пять пунктов особого внимания закреплены конкретными tests. Новые production сервисы, миграции и зависимости не планируются.

План принят к исполнению 7 октября 2026 года. Пять задач выполнены последовательно в текущем чате; результаты проверок и финального ревью фиксируются в отчёте. Task 2/4/5 проверяют существующую migration и могли пройти без изменения production DDL; обязательный искусственный RED не создавался. Некоторые сценарии объединены параметризацией с сохранением проверяемого поведения.

Отдельная agent memory и repository-change ingest на этапе планирования не нужны: решения и причины сохранены спецификацией и этим планом.
