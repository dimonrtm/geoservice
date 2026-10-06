# День 2: схема первого сохранения — план реализации

> **Для агента-исполнителя:** обязательный навык выполнения — `superpowers:executing-plans` при работе основным агентом или `superpowers:subagent-driven-development` при выбранном пользователем выполнении через субагентов. Выполнять задачи последовательно и отмечать шаги `- [ ]`. Команды `git add`, `git commit`, `git push` запрещены правилами репозитория.

**Цель:** реализовать migration для draft revision, durable registry и защищённой append-only истории, сохранив существующие данные.

**Архитектура:** одна новая Alembic revision в существующей schema `work_order`. Registry имеет FK на удаляемые рабочие строки; history хранит самостоятельные идентификаторы и проверяет контекст при INSERT. SQL constraints и triggers обеспечивают согласованные гарантии, а Save/ORM остаются следующими этапами.

**Стек:** Python 3.12, Alembic, SQLAlchemy, asyncpg, PostgreSQL 16, PostGIS 3.4, pytest; существующий Docker Compose runner.

**Спецификация:** [2026-10-01-day-2-first-save-schema-design.md](2026-10-01-day-2-first-save-schema-design.md), принята пользователем.

Статус плана: выполнен 1 октября 2026 года. Результаты и границы проверки — в [отчёте реализации](2026-10-01-day-2-first-save-schema-implementation-report.md).

## Общие ограничения

- Все новые объекты: schema `work_order`; baseline `utility_network.default_state_features` не меняется.
- `draft_revision BIGINT NOT NULL DEFAULT 1`, CHECK `draft_revision >= 1`; existing geometry и UUID сохраняются.
- Старый head `f8a7b6c5d4e3`; новая revision `b7d2e9f4a6c8`. Перед началом проверить отсутствие другого нового head и коллизии ID; при внешнем изменении цепочки сначала согласовать обновление плана, старые migrations не переписывать.
- Не добавлять ORM fields/models, Save service, API, frontend, fingerprint algorithm или новые зависимости.
- Один UUID команды обозначает неизменную identity; access rejection может повторяться, success и остальные rejections не переписываются.
- Команда не остаётся `running` после commit. No-op не создаёт history.
- History не изменяется и не удаляется обычным UPDATE/DELETE/TRUNCATE. Удаление версии удаляет registry, но сохраняет event.
- Данные тестов только в isolated Compose-проекте `geoservice-db-tests`, БД `geo_test`; `RUN_DB_TESTS=1` без `TEST_DATABASE_URL` запрещён.
- Не менять `C:\Repositories\ai-po-template-experiments`; не выполнять staging/commit/push. Изменения остаются для review пользователя.

## Особое внимание при review

1. SQL CHECK допускает UNKNOWN: неполные NULL-поля и JSONB null не должны проходить как successful/rejected result — задача 1.
2. Deferred trigger видит промежуточный INSERT running: завершённая команда должна проходить commit, незавершённая — нет; rollback возобновления должен сохранить старый отказ — задача 2.
3. Одинаковый feature UUID в разных версиях и чужой actor не должны дать событию неправильный контекст — задачи 1 и 3.
4. Сложный существующий snapshot с associations и registry должен удаляться без потери history; cleanup не должен удалять историю — задача 5.
5. Ошибка добавления события должна откатить уже записанные snapshot/revision/successful result; одинаковая geography при разных координатах не должна ошибочно считаться no-op — задачи 3 и 5.

## Карта файлов

| Файл | Ответственность |
| --- | --- |
| `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/b7d2e9f4a6c8_first_save_schema.py` | Создать: самодостаточная migration, DDL и PL/pgSQL definitions, upgrade/downgrade |
| `apps/backend/tests/integration_tests/first_save_schema_support.py` | Создать: уникальные SQL fixtures, snapshots, connection helpers без ORM новых таблиц |
| `apps/backend/tests/integration_tests/test_first_save_schema_migration.py` | Создать: fresh/populated upgrade и root revision |
| `apps/backend/tests/integration_tests/test_first_save_command_constraints.py` | Создать: registry FK/CHECK/transitions/commit |
| `apps/backend/tests/integration_tests/test_first_save_event_constraints.py` | Создать: event context, geometry, immutable history, deletion и rollback |
| `apps/backend/tests/integration_tests/test_cross_context_consistency.py` | Условно изменить только cleanup, если regression воспроизводит конфликт порядка удаления с новым registry FK |
| `docs/sprint_2/README.md` | В конце связать документы с фактическим результатом, не писать отчёт об успешных тестах до их выполнения |

Migration не импортирует текущие ORM-модели или mutable runtime SQL-файлы. SQL definitions хранятся в самой migration, чтобы её поведение не менялось при последующих изменениях приложения.

## Запуск проверок

Все команды ниже выполняются из корня репозитория. Это инструкции будущему исполнителю; при составлении плана команды не запускались.

Первоначально подготовить только isolated stack:

```powershell
docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml build backend_db_tests
docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml up -d --wait postgis_test
```

Перед каждым запуском после изменения исходников повторять `build backend_db_tests`: Dockerfile копирует код в image, исходники не смонтированы. Targeted command:

```powershell
docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml run --rm --no-deps backend_db_tests python -m pytest tests/integration_tests/test_first_save_schema_migration.py -v --tb=short
```

В задачах заменяется только путь test module. Ожидаемый красный запуск — assertion/DB constraint failure по проверяемой причине, а не ошибка соединения или отсутствующая зависимость. Зелёный запуск — exit 0, все выбранные tests passed, DB tests не skipped.

Окончательный regression запускается штатным `infra\db-tests.cmd`: он пересоздаёт только isolated stack. Не запускать его одновременно с targeted tests. После прерванного выполнения очищать только этот же project:

```powershell
docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml down -v --remove-orphans
```

## Задача 1. Upgrade и структура root/registry

**Файлы:** создать migration, support, migration tests и command tests из карты файлов.

**Интерфейсы:** migration экспортирует `upgrade() -> None`, `downgrade() -> None`, `revision = 'b7d2e9f4a6c8'`, `down_revision = 'f8a7b6c5d4e3'`. Support экспортирует `seed_context(connection: AsyncConnection) -> dict[str, UUID]`, `snapshot_context(connection: AsyncConnection, edit_version_id: UUID) -> dict[str, Any]`; ключи IDs: `work_order_id`, `default_state_id`, `edit_version_id`, `feature_id`, `actor_user_id`. UUID создаются заново для каждого сценария. Fixture создаёт AOI, baseline, версию и line, а также endpoint features и association для проверки удаления.

- [x] Написать `test_fresh_upgrade_creates_first_save_objects`: в isolated БД downgrade до base, upgrade до новой revision, проверить root column и registry через catalog; always restore head в finally. В задаче 3 этот же test расширяется проверкой history. Это проверка fresh chain, не полный цикл acceptance Дня 3.
- [x] Написать `test_populated_upgrade_preserves_snapshot`: downgrade до старого head, SQL fixture без draft column, снять UUID/поля/EWKB/properties/associations snapshot, upgrade, проверить равенство исходного snapshot, revision 1 и пустой registry. Проверка пустой history добавляется в задаче 3.
- [x] Добавить `test_draft_revision_default_and_positive_check` с assertions: omitted -> 1; NULL -> SQLSTATE 23502; 0/-1 -> 23514. Повторный UPDATE `last_opened_at` не меняет revision.
- [x] Добавить parametrized `test_command_result_shape_constraints`: missing completed_at, JSONB null/array вместо object, payload в rejected, rejection в succeeded, running с результатом, пустой fingerprint и invalid state отклоняются. Допустимые формы соответствуют таблице спецификации; SQL fixtures используют полный исходный successful response, а не произвольный `{}`.
- [x] Добавить `test_command_feature_fk_is_version_scoped`: feature из другой версии и отсутствующая feature дают 23503. Добавить duplicate `command_id` в другой версии: 23505.
- [x] Запустить оба test modules, подтвердить ожидаемые failures до реализации: root column или registry отсутствуют. В задаче 1 tests ещё не требуют history.
- [x] Реализовать root column, command table/FK/CHECK/index в `upgrade()`, обратные операции в `downgrade()`. Типы/defaults точно из спецификации. Команда INSERT с final state будет запрещена guard из задачи 2; setup SQL заранее использует running -> terminal.
- [x] Повторить оба модуля до pass. На этом этапе доказаны root/registry и сохранность existing data; history добавляется следующими задачами.

Не создавать лишний index на draft revision. Для command FK/index использовать согласованные `(edit_version_id, feature_id)`. CHECK retry flag: только rejected/404/`EDIT_VERSION_NOT_FOUND` допускает true.

Ключевые assertions после SQL reads (snapshot helper возвращает только исходные поля, без новой draft column):

```python
assert after_snapshot == before_snapshot
assert draft_revision == 1
assert command_count == 0
assert fk_error.orig.sqlstate == "23503"
```

## Задача 2. Переходы registry и запрет committed running

**Файлы:** изменить migration, support и `test_first_save_command_constraints.py`.

**Интерфейсы:** PL/pgSQL функции `work_order.guard_edit_command_transition() RETURNS trigger`, `work_order.ensure_edit_command_terminal() RETURNS trigger`. Support добавляет `insert_running_command(connection: AsyncConnection, context: dict[str, UUID], command_id: UUID) -> None`, `finish_command(connection: AsyncConnection, command_id: UUID, *, state: str, retry_on_access_change: bool = False) -> None` для валидных terminal fixtures.

- [x] Написать `test_terminal_command_commits_after_running_insert` отдельно для succeeded/rejected и `test_running_command_cannot_commit`. Использовать настоящее `engine.begin()`/commit; общий rollback helper сам по себе не проверяет deferred commit trigger.
- [x] Добавить `test_successful_noop_without_event_can_commit`: successful result с unchanged/current token допускает commit без event; отсутствие события само по себе не означает незавершённую команду. До задачи 3 отсутствие history table не мешает этой проверке; после задачи 3 дополнительно проверяется отсутствие строки event.
- [x] Написать `test_command_identity_is_immutable`, параметризуя UUID identity, actor, fingerprint и created_at; mutation отклоняется, строка остаётся прежней.
- [x] Написать `test_only_access_rejection_can_resume`: access rejected -> running -> succeeded разрешён; обычный rejected и succeeded -> running запрещены; direct INSERT succeeded/rejected запрещён.
- [x] Написать `test_failed_access_retry_preserves_previous_result`: committed access rejection, новая transaction переводит в running, затем rollback; повторный SELECT видит прежний отказ и created_at. Завершённый success/rejection response также нельзя заменить прямым UPDATE.
- [x] Запустить command tests, подтвердить failures из-за пока отсутствующих guards.
- [x] Добавить BEFORE INSERT/UPDATE transition guard. Использовать `IS DISTINCT FROM` при сравнении immutable полей; разрешать только согласованные переходы. Guards выбрасывают SQLSTATE 23514 с устойчивым именем constraint в диагностике.
- [x] Добавить `AFTER INSERT OR UPDATE ... DEFERRABLE INITIALLY DEFERRED` constraint trigger. Он перечитывает строку по command_id: отсутствующая строка не является pending command; существующая running блокирует commit. Terminal NEW при более раннем deferred running event не должен ошибочно блокироваться.
- [x] Добавить обратное удаление triggers/functions в downgrade; повторить command tests до pass.

При ожидаемой ошибке тест использует отдельную transaction/savepoint и не продолжает SQL внутри aborted transaction. Для проверки deferred guard использовать именно commit; `SET CONSTRAINTS ... IMMEDIATE` допустим только как дополнительная локальная проверка, не замена commit test.

Ключевые assertions после настоящего commit/rollback и повторного SELECT:

```python
assert commit_error.orig.sqlstate == "23514"
assert resumed["state"] == "succeeded"
assert resumed["created_at"] == original["created_at"]
assert after_failed_retry == original_access_rejection
```

## Задача 3. Event table и проверка контекста INSERT

**Файлы:** изменить migration и support; создать `test_first_save_event_constraints.py`.

**Интерфейсы:** PL/pgSQL `work_order.validate_edit_change_event() RETURNS trigger`. Support добавляет `persist_sql_change(connection: AsyncConnection, context: dict[str, UUID], command_id: UUID, *, emit_event: bool = True) -> None`: фиксированный fixture-переход между трёхвершинными LineString, root 1 -> 2, operation updated, running -> succeeded, затем event. Это тестовая SQL fixture, не production Save implementation.

- [x] Написать `test_event_insert_matches_successful_command`: корректный fixture создаёт ровно одну строку с before 1/after 2 и полными контекстными UUID.
- [x] Добавить `test_revert_event_preserves_previous_geometry`: после первого события выполнить SQL Revert 2 -> 3 с operation unchanged, before равным moved geometry и after равным baseline; принять `change_set_cleared`, сохранить оба события.
- [x] Добавить negative cases для missing root/command/feature, чужой version/actor/feature, running/rejected command, неверных work_order/default_state/base revision, несовпадающей after revision/geometry и event_type/operation.
- [x] Добавить `test_event_local_constraints`: duplicate command и duplicate `(edit_version_id, draft_revision_after)` дают 23505; отрицательная revision/неверный шаг/type отклоняются; POINT, другой SRID, empty, non-simple geometry не принимаются.
- [x] Добавить exact-coordinate cases: одинаковые before/after отклоняются; две простые LineString с разными внутренними координатами на одном прямом участке допускаются как разные координатные snapshots, даже когда топологически равны. Это тест сравнения history, не утверждение допустимости любой такой команды Save.
- [x] Запустить event tests и подтвердить ожидаемые failures.
- [x] Добавить event table по спецификации: PK command_id, UNIQUE версии/new revision, CHECK и PostGIS LINESTRING/4326 без implicit spatial index. Именованные constraints должны быть короче PostgreSQL identifier limit и проверяемы по catalog.
- [x] Реализовать INSERT guard с порядком root `FOR UPDATE` -> command `FOR SHARE` -> feature `FOR SHARE`. Проверки и SQLSTATE 23514 для несовместимого контекста; after geometry сравнить через `ST_AsEWKB`. Для persisted требовать operation updated, для cleared — unchanged.
- [x] Расширить fresh/populated tests задачи 1 проверкой history table, её constraints/index и отсутствием artificial events после upgrade. Выполнить три модуля до pass; проверить отсутствие unintended spatial indexes.

Перед прямым negative INSERT создать валидную команду/контекст, иначе тест может упасть по более ранней причине и не доказать нужный invariant. Проверка `before_geometry` ограничивается формой и отличием; восстановление прежнего snapshot — обязанность будущего Save.

Ключевые assertions event reads:

```python
assert event["draft_revision_after"] - event["draft_revision_before"] == 1
assert event["command_id"] == command_id
assert revert_event["event_type"] == "change_set_cleared"
assert revert_after_ewkb == baseline_ewkb
assert history_count == 2
```

## Задача 4. Append-only защита

**Файлы:** изменить migration и event tests.

**Интерфейсы:** PL/pgSQL `work_order.reject_edit_change_event_mutation() RETURNS trigger`, используемая row trigger на UPDATE/DELETE и statement trigger на TRUNCATE. Ошибка SQLSTATE 23514 с устойчивым диагностическим именем `ck_ev_events_append_only`.

- [x] Написать `test_event_history_rejects_update_delete_truncate`: создать committed event, для каждой операции отдельная transaction, проверить ошибку и byte-equivalent snapshot строки после rollback.
- [x] Включить `UPDATE ... SET actor_user_id = actor_user_id` и `INSERT ... ON CONFLICT (command_id) DO UPDATE`: даже замаскированный UPDATE не меняет событие. Для конфликтного INSERT использовать согласованный контекст, чтобы доказать именно append-only guard.
- [x] Запустить cases, подтвердить failures без защиты.
- [x] Добавить row BEFORE UPDATE OR DELETE и statement BEFORE TRUNCATE triggers; функция всегда raises. INSERT не блокируется этой функцией.
- [x] Добавить удаления новых triggers/functions в downgrade; повторить event tests до pass.

Не добавлять runtime-флаг отключения защиты, специальный DELETE endpoint или cleanup bypass. Административный DDL остаётся вне DML-гарантии.

Assertions после каждой отдельной запрещённой операции:

```python
assert error.orig.sqlstate == "23514"
assert saved_event_after == saved_event_before
```

## Задача 5. Lifecycle, атомарность и итоговая проверка

**Файлы:** изменить event/migration tests и при доказанной необходимости существующий cleanup из карты файлов; завершить downgrade migration и документацию.

**Интерфейсы:** использовать fixtures задач 1–3. SQL fixture удаления сначала удаляет associations выбранной версии, затем root; root cascades registry и features. History не участвует в DELETE. Production delete API в рамках задачи не создаётся.

- [x] Написать `test_deleting_version_preserves_history`: committed context/change/event; удалить associations и root одной transaction; проверить root/registry/current rows absent, event полностью прежний, baseline прежний.
- [x] Написать `test_event_failure_rolls_back_entire_change`: committed исходный context; в следующей transaction обновить geometry/root и завершить команду, затем вставить event с неверной after revision; после rollback проверить прежние geometry/revision, отсутствие новой команды/event. SQL exception ожидается и не подменяет assertions после rollback.
- [x] Добавить `test_explicit_rollback_discards_change_and_event`: после валидной mutation/result/event выполнить rollback, проверить тот же исходный snapshot. Все проверки читать через новую connection.
- [x] Запустить эти tests; при конфликте FK проверить statement/transaction ordering и диагностическое constraint name. Не ослаблять history и не удалять существующие FK наугад. Если согласованная операция удаления невыполнима без изменения existing constraints, остановить соответствующий шаг и предложить конкретную корректировку спецификации до расширения DDL.
- [x] Проверить downgrade order: убрать новые triggers и функции с учётом зависимостей, удалить history/registry, убрать root CHECK/column; не менять existing geometry. Полный отдельный upgrade/downgrade/upgrade acceptance остаётся Дню 3, но downgrade обязан работать для изолированных migration tests текущего дня.
- [x] Выполнить три новых модуля вместе, затем один полный `infra\db-tests.cmd`. Existing cleanup, удаляющий feature до root при наличии registry, исправлять только после воспроизводимого failure: удалить associations, затем root с cascades, убрать избыточный DELETE features. History не удалять.
- [x] Запустить ruff/black checks только изменённых Python files внутри test image. Использовать `python -m ruff check <files>` и `python -m black --check <files>` через тот же `docker compose ... run --rm --no-deps backend_db_tests`; заменять `<files>` точными путями из карты, от корня `/app`, не оставлять placeholder в фактической команде.
- [x] Проверить `git diff --check`, фактический список изменённых файлов и отсутствие правок ORM/API/seeds. Описать tests passed/skipped/blocked честно, отметить оставшиеся проверки Дня 3. Оставить изменения unstaged.

Ключевые assertions lifecycle/rollback:

```python
assert version_count == command_count == feature_count == association_count == 0
assert retained_event == original_event
assert retained_baseline == original_baseline
assert after_rollback_snapshot == before_snapshot
assert after_rollback_revision == 1
```

## Проверка покрытия и передача

| Раздел спецификации | Задачи или граница |
| --- | --- |
| Размещение, root revision, existing data | 1 |
| Registry columns/FK/CHECK/index | 1 |
| Immutable identity, transitions, final running guard | 2 |
| Event columns/geometry/context/indexes | 3 |
| Append-only | 4 |
| Удаление версии, rollback, isolated DB | 5 |
| Replay, fingerprint, stale/auth HTTP handling | Схема поддерживает через сохранённый результат и retry flag; production use cases остаются Дням 4–8 |
| ORM parity, конкурентность, полный cycle | День 3, без переноса в реализацию Дня 2 |

План проверен по принятой спецификации: пять review risks привязаны к тестам, имена support interfaces согласованы, изменения ограничены migration/tests/docs. Отдельная agent memory и `/ingest repository-change` на этапе планирования не нужны: код ещё не реализован, решения сохраняются в спецификации и плане.

Рекомендуемый способ выполнения — основным агентом через `superpowers:executing-plans`: все пять задач последовательно меняют одну migration, поэтому параллельная реализация создаёт лишние зависимости. Альтернатива — последовательное выполнение через субагентов с review каждой задачи. До реализации пользователь просматривает план и выбирает способ выполнения.
