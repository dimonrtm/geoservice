# День 5 Sprint 2: план реализации атомарного repository context

> **Для агента-исполнителя:** использовать `superpowers:executing-plans` для последовательного исполнения либо `superpowers:subagent-driven-development`, если пользователь выберет этот способ. Прочитать спецификацию и этот план. Шаги отмечать через `- [x]` после проверки. Git staging, commit и push запрещены правилами репозитория; соответствующие шаги навыков не выполнять.

**Цель:** реализовать безопасные чтение, spatial validation и запись current geometry под блокировкой EditVersion, сохранив authoritative DefaultState.

**Архитектура:** EditVersionRepository относится к агрегату EditVersion и работает на AsyncSession вызывающего сервиса. Geometry — значение внутри его current feature; geometry-specific helpers не являются отдельным repository агрегата. Root lock предшествует новому SELECT контекста; подготовка candidate использует существующее Decimal-ядро. Проверенный результат связан с контекстом и transaction, UPDATE не делает commit и не управляет registry/history в рамках Дня 5.

**Стек:** Python 3.12, SQLAlchemy 2, asyncpg, GeoAlchemy2, Shapely, Decimal, PostgreSQL 16 / PostGIS 3.4, pytest; существующие зависимости.

**Спецификация:** [День 5: атомарный repository context](2026-10-10-day-5-repository-context-design.md), принята пользователем 10 октября 2026 года.

**Статус:** задачи 1–6 выполнены последовательно 10 октября 2026 года; M1 подтверждена. Результаты и отличия от исходного плана — в [отчёте](2026-10-10-day-5-repository-context-implementation-report.md) и [ledger](2026-10-10-day-5-execution-ledger.md).

## Общие ограничения

- Работать в согласованном scope Дня 5: без production Save endpoint, revision increment, registry/replay/event orchestration, UI и новых migrations.
- Transaction принадлежит вызывающему сервису; repository не вызывает begin/commit/rollback и не создаёт вторую session. Требуется активная внешняя transaction, READ COMMITTED, без savepoint-переходов во время жизни context.
- AOI, baseline и assignment считаются неизменными на время Save. Конкурирующие Save берут root lock; произвольные writers не защищаются новым механизмом.
- Порядок конфликтующих locks: EditVersion → command → feature. После root не брать writer lock WorkOrder. Чтение context не блокирует feature заранее.
- Geometry: XY, SRID 4326, X `[-180,180]`, Y `[-90,90]`; persisted GeometryPolicy root. Не менять алгоритмы Дня 4, не добавлять скрытого snapping/repair.
- No-op определяется numeric equality и не выполняет UPDATE. Возврат baseline сохраняет storage values; signed zero не создаёт искусственного diff.
- D5-Q1 временно запрещает любой нулевой сегмент после canonicalization; ожидаемый отказ — `GEOMETRY_INVALID`. Отметка «требует доменного уточнения» обязательна в отчёте.
- SQL mutation меняет только geometry/operation одной current feature. Draft revision, DefaultState, AOI, associations, properties и network_version неизменны.
- DB tests — только disposable `geoservice-db-tests` / `geo_test`, с существующим isolation guard. Demo-БД не использовать.
- Соблюдать `docs/agent-memory/patterns/2026-10-07-python-formatting-style.md`. Новые документы на русском в `docs/sprint_2`; изменения оставлять unstaged.

## Особое внимание при ревью

1. Context из завершённой transaction нельзя использовать после нового begin в той же session; одного `in_transaction()` недостаточно — задачи 1 и 4.
2. Два context одной версии, прочитанные до mutation: после записи через первый второй должен стать устаревшим, даже если transaction ещё активна — задача 4.
3. После ожидания чужого commit root и current должны быть свежими, даже если ORM identity map содержала старую feature — задача 5.
4. Candidate, valid/simple сам по себе, может выходить за вогнутую AOI или пересекать hole между разрешёнными vertices — задача 3.
5. Current содержит signed zero и baseline вне grid: no-op не должен переписывать bytes, а Revert должен восстановить baseline storage — задача 4.

## Структура файлов

В таблице и задачах пути относительны `apps/backend`, кроме путей с `docs/` и `infra/`.

| Действие | Путь и ответственность |
| --- | --- |
| Создать | `utility_service/infrastructure/postgresql/repositories/edit_version_repository.py` — persistence агрегата EditVersion и ограниченная запись дочерней feature |
| Создать | `utility_service/infrastructure/postgresql/repositories/edit_geometry_scope.py` — session/transaction provenance, поколения context и lifecycle handles |
| Создать | `utility_service/infrastructure/postgresql/repository_rows/edit_geometry.py` — frozen rows, context, prepared/validated handles и результаты |
| Создать | `utility_service/infrastructure/postgresql/repositories/edit_geometry_validation.py` — проверка исходного context и адаптация существующего geometry core |
| Создать | `utility_service/infrastructure/postgresql/sql/edit_geometry_context.sql` — проекция target/current/baseline/AOI и changed feature IDs |
| Создать | `utility_service/infrastructure/postgresql/sql/edit_geometry_spatial.sql` — shape/simple/valid/zero-segment и guarded AOI coverage |
| Создать | `utility_service/infrastructure/tests/test_edit_geometry_protocol.py` — provenance, порядок вызовов и отсутствие лишних UPDATE |
| Создать | `tests/integration_tests/edit_geometry_repository_support.py` — fixtures и snapshots только для новых tests |
| Создать | `tests/integration_tests/test_edit_geometry_context.py`, `test_edit_geometry_validation.py`, `test_edit_geometry_spatial.py`, `test_edit_geometry_mutation.py`, `test_edit_geometry_concurrency.py` |
| Переиспользовать | `domain_services/edit_geometry/`, `geometry_codec.py`, существующие `first_save_schema_support.py` и `first_save_orm_support.py` |
| Создать после реализации | `docs/sprint_2/2026-10-10-day-5-repository-context-implementation-report.md`; обновить `docs/sprint_2/README.md` |

Существующие production модули не менять без необходимости подтверждённой тестом. Не вводить общий framework UnitOfWork или registry handles для других repositories.

## Команды и критерии проверки

Команды выполняются в PowerShell из корня репозитория. Исходники копируются в Docker image: после изменения кода перед тестом пересобрать image.

```powershell
docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml build backend_db_tests
```

Далее обозначения **U(path)** и **D(path)** означают команды ниже с подставленным конкретным test path из задачи; `TEST_PATH` не shell variable.

```powershell
docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml run --rm --no-deps -e RUN_DB_TESTS=0 backend_db_tests python -m pytest TEST_PATH --tb=short
```

```powershell
docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml run --rm backend_db_tests python -m pytest TEST_PATH --tb=short
```

RED — падение целевого assertion или отсутствие ещё не созданного модуля. Ошибка Docker/network/dependency не считается RED. GREEN — exit code 0 и выполненные tests; skipped DB tests не подтверждают поведение.

Перед fresh DB-прогоном и после завершения тестовой работы, включая ошибку, использовать только тестовый Compose project:

```powershell
docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml down -v --remove-orphans
```

Перед исполнением проверить выбранный checkout/worktree и git status; сохранить пользовательские изменения. Планирование не создавало worktree и не запускало тестовую БД.

## Задача 1. Root lock и контекст одной transaction

**Файлы:** создать repository, scope, rows, context SQL, test support, `test_edit_geometry_context.py` и `test_edit_geometry_protocol.py` из таблицы.

**Интерфейсы:**

- `EditVersionRepository(session: AsyncSession)`.
- `async lock_version(*, work_order_id: UUID, edit_version_id: UUID) -> LockedEditVersion | None`.
- `async read_context(locked_version: LockedEditVersion, *, feature_id: UUID) -> EditGeometryContext | RepositoryRejection`.
- `RepositoryRejection(code: str, reason: str)` — frozen внутренний исход; `RepositoryProtocolError(RuntimeError)` — неверное использование handle/transaction, без public HTTP mapping.
- `LockedEditVersion`: id, work_order_id, default_state_id, base_network_revision, draft_revision, status и persisted policy fields; приватная принадлежность scope.
- `EditGeometryContext`: `root`, WorkOrder status/assignee, `current`, nullable `baseline`, nullable DefaultState metadata, AOI EWKB и `other_changed_feature_ids: tuple[UUID, ...]`; приватный scope/read generation.
- Feature row: feature_id, feature_type, operation для current, network_version, geometry_ewkb; nullable decoded geometry заполняется после распознавания поддерживаемого storage. DefaultState row: id, work_order_id, base_network_revision, status. Immutable bytes/tuples вместо mutable JSON geometry.

- [x] Добавить `seed_repository_context(connection: AsyncConnection) -> dict[str, UUID]` в test support: вызвать existing `seed_context`, установить WorkOrder `in_progress`, сохранить исходные UUID/geometry; новые generic fixtures создаются уникальными IDs, без изменения shared seed helpers.
- [x] Добавить `test_context_reads_linked_baseline_without_workspace_filter`: current feature за пределами AOI всё равно найдена; `context.root.default_state_id == ids['default_state_id']`; baseline EWKB соответствует именно root link.
- [x] Добавить cases missing version, mismatched work_order_id и missing current: отсутствие root → None, missing target → `RepositoryRejection(code='EDIT_VERSION_NOT_FOUND', ...)`; missing baseline не скрывает существующую current строку.
- [x] Добавить protocol tests: вызов без active transaction, handle другой session, handle после rollback/new begin и active savepoint дают `RepositoryProtocolError` до SQL mutation.
- [x] Выполнить U(`utility_service/infrastructure/tests/test_edit_geometry_protocol.py`) и D(`tests/integration_tests/test_edit_geometry_context.py`); подтвердить RED.
- [x] Реализовать scope с привязкой к identity внешней SQLAlchemy transaction и session, проверкой её активности и отсутствия nested transaction. Для обнаружения уже завершившегося savepoint внутри scope использовать session transaction lifecycle events с ограниченным временем регистрации; не полагаться только на текущее отсутствие nested transaction.
- [x] Реализовать отдельный root SELECT FOR UPDATE; затем `read_context` отдельным SQL statement. Использовать mappings/typed rows, LEFT JOIN для диагностируемых missing links; root и target фильтровать по составному контексту, AOI через WorkOrder. `other_changed_feature_ids` выбирает все `operation != 'unchanged'` кроме target, без spatial filter.
- [x] Подтвердить U/D GREEN. Scope не создаёт transaction, не делает commit/rollback и не добавляет feature lock при чтении.

## Задача 2. Исходные инварианты и подготовка candidate

**Файлы:** создать `edit_geometry_validation.py`, `test_edit_geometry_validation.py`; расширить repository/rows и protocol tests.

**Потребляет:** типы и `read_context` задачи 1, `decode_geometry`, `GeometryPolicy`, `prepare_geometry`, `validate_transition` из существующего кода.

**Производит:**

- `check_context(context: EditGeometryContext) -> RepositoryRejection | None` — проверки существования/eligibility/согласованности и numeric structure, без HTTP.
- `prepare_candidate(context: EditGeometryContext, request_geometry: GeometryValue) -> PreparedGeometryHandle | RepositoryRejection` — синхронный метод repository, использующий чистое ядро.
- `PreparedGeometryHandle`: `prepared: PreparedGeometry`, привязка к context и identity результата выдачи; его PreparedGeometry сохраняет rejection_code для fingerprint до spatial validation.

- [x] Добавить table-driven tests: Point, line из двух vertices, created/deleted → `FEATURE_NOT_EDITABLE`; created без baseline также не превращается в context-invalid.
- [x] Добавить tests missing baseline у unchanged/updated, чужой DefaultState, mismatched base revision/type и operation/diff contradiction → `WORK_ORDER_CONTEXT_INVALID`.
- [x] Добавить tests endpoints/current count/two moved vertices → context-invalid; корректный updated одной внутренней вершины допускается. Контекст сохраняет `other_changed_feature_ids`; отказ по ним проверяется в задаче 3, когда появится validation stage.
- [x] Добавить `test_prepare_uses_persisted_policy`: root grid `0.00000025`, request midpoint `0.000000375` даёт canonical ordinate `0.0000005`, независимо от default settings. Baseline fixture для этого scalar case не должен совпадать с rounded ordinate.
- [x] Выполнить D(`tests/integration_tests/test_edit_geometry_validation.py`), подтвердить RED.
- [x] Реализовать `check_context` с явным порядком eligibility → missing/mismatched baseline/AOI → numeric current invariants. Decoding испорченного storage отражается в context-invalid; нельзя перехватывать все ValueError как ошибки пользователя.
- [x] Реализовать `prepare_candidate` поверх existing core. Подготовка использует пригодный baseline/policy, но не выполняет current-dependent spatial/other-feature rejection: будущий fingerprint/replay должен быть доступен до этих guards. PreparedGeometry с rejection_code остаётся представлением намерения, а не разрешением записи.
- [x] Убедиться, что current/operation и other-feature checks выполняются при последующей validation; права и HTTP mapping не добавлены в repository. Подтвердить D GREEN и U существующих `test_geometry_canonicalization.py`/`test_geometry_structure.py` в `utility_service/domain_services/tests/`.

## Задача 3. Spatial validation точного candidate

**Файлы:** создать spatial SQL и `test_edit_geometry_spatial.py`; расширить validation/repository/rows.

**Потребляет:** `PreparedGeometryHandle`, context задачи 1 и `check_context` задачи 2; existing geometry codec.

**Производит:**

- `async validate_candidate(context: EditGeometryContext, prepared_geometry: PreparedGeometryHandle) -> ValidatedGeometryChange | RepositoryRejection`.
- `SpatialVerdict`: bool поля `shape_ok`, `nonempty`, `valid`, `simple`, `no_zero_segments`, `aoi_covered`.
- `ValidatedGeometryChange`: target IDs, `before_ewkb`, `after_ewkb`, `operation: Literal['unchanged','updated']`, `is_noop: bool`, `vertex_index: int | None`; внутренние context/generation/provenance. Это единственный допустимый вход `write_current`.
- SQL helper `async inspect_spatial(session: AsyncSession, *, geometry_ewkb: bytes, aoi_ewkb: bytes) -> SpatialVerdict` в validation module; внутренний, доступен тестам spatial слоя.

- [x] Добавить spatial fixtures с ожидаемыми исходами: `LINESTRING(0 0,1 1,2 0)` valid/simple; `LINESTRING(0 0,2 2,0 2,2 0)` valid, но non-simple; `LINESTRING(0 0,0 0,2 0)` содержит zero segment; `LINESTRING(0 0,0 0)` invalid. Для низкоуровневых predicates fixture может обходить structure guard, но не DB isolation.
- [x] Добавить AOI cases: квадрат `(0,0)-(4,4)` принимает line на boundary; квадрат с hole `(1,1)-(3,3)` отвергает segment `(0.5,2)-(3.5,2)` при внутренних endpoints; MultiPolygon из раздельных квадратов отвергает line через gap и принимает line внутри одного компонента.
- [x] Добавить `test_zero_segment_after_canonicalization_is_rejected_d5_q1`, `test_non_simple_current_is_context_invalid` и case ошибки исходной AOI. Candidate rejected кодами geometry-invalid/outside-AOI; исходный context — context-invalid. Другая changed feature, включая находящуюся вне workspace projection, даёт `MULTIPLE_FEATURE_CHANGE_NOT_ALLOWED`.
- [x] Выполнить D(`tests/integration_tests/test_edit_geometry_spatial.py`); подтвердить RED.
- [x] Реализовать shape/SRID/XY/nonempty/valid/simple checks, ordered `ST_DumpPoints` + соседние XY для D5-Q1. AOI coverage выполнять только после guards, не полагаясь на порядок SQL AND. Использовать parameter binding и exact EWKB.
- [x] Реализовать `validate_candidate`: проверить handle, `check_context`, spatial baseline/current/AOI, other changed feature, prepared rejection/structure/transition, spatial candidate. Перед existing strict zip проверить структуру. Кодирование допустимого candidate с потерей обратимости — internal failure.
- [x] При numeric candidate==current оставить current bytes и is_noop; иначе candidate==baseline использует baseline bytes; остальные candidate кодировать один раз. Проверять именно выбранные bytes, которые получит write.
- [x] Для каждого ожидаемого отказа выполнить `SELECT 1` в той же transaction: `assert value == 1`; snapshot не изменён. Подтвердить D GREEN и U protocol tests, включая отклонение самостоятельно сконструированного/подменённого handle.

## Задача 4. Ограниченная mutation и lifecycle context

**Файлы:** repository/scope/rows; создать `test_edit_geometry_mutation.py`; расширить protocol tests и test support.

**Потребляет:** `ValidatedGeometryChange` задачи 3.

**Производит:** `async write_current(validated_change: ValidatedGeometryChange) -> GeometryWriteResult`, где frozen `GeometryWriteResult` содержит `changed: bool`, `operation`, `before_ewkb`, `after_ewkb`. Результат не содержит нового draft token или registry state.

- [x] Добавить test support `snapshot_repository_state(connection, ids) -> dict[str, object]`: root включая revision, AOI, DefaultState root, все baseline features/associations и current features/associations; geometry отдельно как EWKB. Existing `snapshot_context` недостаточен: он исключает revision и не включает baseline associations.
- [x] Добавить tests обычного update и baseline restore: изменены только target geometry/operation; `after['baseline'] == before['baseline']`, revision и associations неизменны. После commit новая session читает exact after EWKB.
- [x] Добавить no-op test с наблюдением SQL UPDATE либо тестовым UPDATE-trigger counter: `assert content_update_count == 0`; сравнение только данных недостаточно.
- [x] Добавить off-grid и signed-zero cases: использовать baseline с `65.5200000499`; current/unchanged с numeric-equivalent signed zero остаётся byte-identical на no-op; после настоящего Revert `ST_AsEWKB(current) == baseline_ewkb`.
- [x] Добавить rollback injection после write: наблюдатель не видит uncommitted change; после исключения `after == before` для полного snapshot.
- [x] Добавить protocol cases old transaction, second session, повторное применение одного change, `dataclasses.replace` с другими bytes и два заранее прочитанных context одной версии. После первого применения второй context должен быть отклонён, fresh read в той же transaction допустим.
- [x] Выполнить D(`tests/integration_tests/test_edit_geometry_mutation.py`) и U protocol tests; подтвердить RED.
- [x] Реализовать UPDATE geometry/operation с составным WHERE и RETURNING, проверить одну строку. No-op не выполняет DML. После применения consume результата и invalidation всех прежних context/prepared/validated handles этой версии в scope, чтобы исключить второй stale write.
- [x] Проверять provenance по identity реально выданных objects плюс generation, а не только по совпадению полей frozen dataclass. Не объявлять это защитой от malicious in-process кода. Освобождать scope listeners/ссылки при завершении transaction.
- [x] Подтвердить U/D GREEN. В tests явно проверить, что repository сам не завершил transaction; exception владельца способен откатить успешный UPDATE.

## Задача 5. Реальная конкуренция и совместимость history

**Файлы:** создать `test_edit_geometry_concurrency.py`; расширить test support, при выявленных дефектах исправить только соответствующие repository/scope методы.

**Потребляет:** весь repository API задач 1–4; `run_committed_scenario`, command/event helpers из existing `first_save_schema_support.py`.

**Производит:** доказательства отсутствия stale read и обратного lock order; новых production interfaces нет.

- [x] В test support реализовать `wait_for_block(observer: AsyncConnection, *, waiter_pid: int, blocker_pid: int) -> None` по существующему образцу `pg_blocking_pids`, с bounded asyncio timeout; каждый scenario завершает transactions и tasks в finally.
- [x] Добавить `test_waiting_context_sees_commit` и rollback variant: T1 lock/write, T2 начинает lock и действительно блокируется, observer подтверждает PID; T1 завершается; T2 read_context видит соответственно after/before geometry. `SHOW transaction_isolation` даёт `read committed`.
- [x] Перед ожиданием намеренно загрузить старую ORM feature в T2 identity map; после root lock typed projection всё равно свежая. Проверить root revision через test-only writer, увеличивающий revision в T1 для этого сценария; repository сам revision не меняет.
- [x] Добавить `test_other_version_is_not_blocked` с разными roots и `test_reopen_and_repository_do_not_deadlock` в обоих порядках, вызывая existing reopen path на пригодной fixture. Проверить final last_opened_at и geometry без lost update.
- [x] Добавить compatibility scenario: root lock → existing running command helper → repository write → test-only revision+1 → existing finish success helper → existing insert_event → commit. Assert event before/after EWKB соответствуют old/new current, revision увеличена только test harness, один event. Полный replay не реализуется.
- [x] Выполнить D(`tests/integration_tests/test_edit_geometry_concurrency.py`); подтвердить RED новых сценариев или явно зафиксировать уже GREEN гарантии, если готовые primitives полностью обеспечивают поведение. Не вносить искусственную поломку ради RED.
- [x] Исправить выявленные расхождения; подтвердить D GREEN вместе с existing `test_first_save_event_concurrency.py` и `test_first_save_event_constraints.py`. Отдельно прогнать protocol test savepoint start/rollback после получения context, затем root transaction всё ещё active: использование context запрещено.

## Задача 6. Приёмка M1 и отчёт

**Файлы:** новый implementation report и `docs/sprint_2/README.md`; product files только для дефектов, выявленных проверками.

**Потребляет:** завершённые задачи 1–5, spec §11 и D5-Q1. **Производит:** проверяемый статус M1 и передача Дням 6–7.

- [x] Собрать свежий test image. Выполнить U для новых protocol tests, всех `utility_service/domain_services/tests`, `utility_service/infrastructure/tests`, `utility_service/use_cases/tests`, `utility_service/utils/tests`, `utility_service/web_api/tests` и `seeds/tests`; также existing test isolation/deployment contracts в `tests/`. Допускается единый `python -m pytest --tb=short` с `RUN_DB_TESTS=0`, но его skipped DB tests не заменяют следующий шаг.
- [x] Запустить полный isolated DB suite штатной командой `infra\db-tests.cmd` из корня. Она создаёт fresh окружение и удаляет только test project. Exit code 0, executed DB tests без необъяснимых skips — требуемый результат.
- [x] Выполнить проектные проверки backend из test image: `python -m black --check .` и `python -m ruff check .` через тот же Compose `run --rm --no-deps -e RUN_DB_TESTS=0 backend_db_tests`. Выполнить `git diff --check`. Несвязанные нарушения фиксировать отдельно, не форматировать весь репозиторий ради задачи.
- [x] Провести итоговое ревью по пяти focus cases, spec §11 и unstaged diff. Если выбранный execution workflow требует независимого reviewer, передать ему spec, plan и фактический diff, не выдавать self-review за независимое.
- [x] Написать report: реализованные гарантии, команды/результаты, фактический статус M1, ограничения и оставшееся D5-Q1. Если проверка недоступна или падает, M1 не считать пройденной. Отдельно указать, что production Save/replay/registry orchestration ещё нет.
- [x] Обновить README и отметить задачи плана только по evidence. Оценить необходимость `/ingest repository-change` по новой durable technical knowledge, а не по факту завершения; memory не дублировать поверх spec/report/wiki. Не выполнять staging/commit/push.

## Самопроверка плана и передача

| Требование спецификации | Задачи |
| --- | --- |
| Scope, root lock, fresh context, typed interfaces | 1 |
| Исходные инварианты, eligibility и ошибки | 2–3 |
| Policy/core, prepared provenance, spatial/AOI/D5-Q1 | 2–3 |
| Storage precision, ограниченная mutation, no-op/rollback | 4 |
| Конкуренция, reopen, registry/history compatibility | 5 |
| Полная матрица M1, регрессия, отчёт и follow-up | 6 |

План проверен на соответствие принятой спецификации, согласованность имён и типов, наличие теста для каждого review focus и отсутствие implementation steps за пределами Дня 5. Локальные Markdown-ссылки, placeholders, whitespace и конфликтные маркеры проверены; `git diff --check` выполнен для tracked изменений. Product tests при подготовке плана не запускались. D5-Q1 имеет однозначное временное поведение; его доменное уточнение не скрыто.

По инструкции пользователя «Приступай к реализации плана» выполнено последовательное исполнение в текущем чате с итоговым независимым review. Названия и группировка части тестов адаптированы; проверяемые контракты сохранены. Scope listeners живут до освобождения session, handles очищаются после transaction; отличие и цена зафиксированы в ledger. Штатный DB lifecycle выполнен эквивалентными Compose-командами из infra/db-tests.cmd.
