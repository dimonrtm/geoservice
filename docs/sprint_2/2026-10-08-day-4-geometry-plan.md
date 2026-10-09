# День 4 Sprint 2: план реализации детерминированной геометрии

> **Для агента-исполнителя:** обязательный навык — `superpowers:executing-plans` для последовательного исполнения либо `superpowers:subagent-driven-development`, если пользователь выберет этот способ. Сначала прочитать спецификацию и этот план. Задачи отмечаются через `- [x]`. Агентам запрещены staging, commit и push; соответствующие шаги навыков не выполняются.

**Цель:** реализовать воспроизводимые canonical geometry и fingerprint, закрепить policy за EditVersion и сохранить точность baseline при storage/readback.

**Архитектура:** чистое Decimal-ядро отделено от точного JSON parser, EWKB codec и persistence. Canonical intent зависит от baseline и persisted policy; проверка перехода отдельно зависит от current. Новые policy fields неизменяемы после создания или однократного backfill.

**Стек:** Python 3.12, Decimal, hashlib/json, FastAPI 0.115.6, Pydantic 2.10.4, SQLAlchemy 2.0.36, Alembic 1.14.0, asyncpg 0.30.0, GeoAlchemy2 0.16.0, Shapely 2.0.6, PostgreSQL 16 / PostGIS 3.4, pytest. Новых зависимостей нет.

**Спецификация:** [Детерминированная геометрия Дня 4](2026-10-08-day-4-geometry-design.md), принята 8 октября 2026 года.

**Статус:** реализация выполнена последовательно в текущем чате; результаты и финальное ревью отражены в implementation report.

## Общие ограничения

- Grid default/minimum `0.0000001`, maximum `360`, точное целое `grid * 10^9`; SRID 4326, XY, origin `(0,0)`, `ROUND_HALF_AWAY_FROM_ZERO`, policy version 1.
- JSON number token не длиннее 64 ASCII-символов, абсолютная явная exponent не больше 324; X `[-180,180]`, Y `[-90,90]`. Parser читает исходные bytes до любого float-преобразования.
- Grid-equivalent baseline ordinates восстанавливаются точно. Current и baseline целиком не перенормализуются. Переход с изменённой A на B требует отдельного Revert.
- Fingerprint `geom-v1:sha256:<hex>` не зависит от current, CommandId или global settings; bytes и golden vectors заданы спецификацией.
- Полный PUT Save, mutation/replay orchestration, spatial validation/AOI и UI не реализуются. Readback меняется только ради точности geometry features.
- DB tests — только isolated Compose `geoservice-db-tests` / `geo_test`, с сохранением isolation guard. Demo-БД и её volume не использовать для тестов.
- Migration требует согласованной geometry configuration и остановленного старого API. Полноценную схему создаёт Alembic, не `create_all`.
- Соблюдать многострочное форматирование Python/SQL из `docs/agent-memory/patterns/2026-10-07-python-formatting-style.md`; не менять несвязанные файлы ради стиля.
- Артефакты на русском в `docs/sprint_2`. `git add`, `git commit`, `git push` не выполнять; изменения остаются unstaged.

## Особое внимание при ревью

1. Внешний Decimal context с маленькой precision и включёнными Inexact/Rounded traps не должен менять результат — задачи 1–2.
2. Grid с дополнительными конечными нулями, например `0.0000002500`, должен приниматься без молчаливого округления недопустимых значений — задачи 1 и 5.
3. Baseline чуть ниже midpoint с более чем 9 fractional digits не должен сдвигаться после workspace readback; signed zero не создаёт искусственного изменения — задача 7.
4. SQL fixtures работают и на historical schema без policy fields; их адаптация не должна менять смысл старых migration tests — задача 5.
5. Ошибка нового backfill откатывает DDL целиком; отсутствие JWT settings у migrator не подменяет geometry configuration — задача 5.

## Структура файлов

Все пути в задачах относительны `apps/backend`, если не начинаются с `infra/` или `docs/`.

| Область | Файлы и ответственность |
| --- | --- |
| Чистое ядро | Создать `utility_service/domain_services/edit_geometry/__init__.py`, `types.py`, `policy.py`, `canonicalization.py`, `structure.py`, `fingerprint.py` |
| Domain tests | Создать `utility_service/domain_services/tests/test_geometry_policy.py`, `test_geometry_canonicalization.py`, `test_geometry_structure.py`, `test_geometry_fingerprint.py` и узкий `geometry_test_support.py` |
| Parser и DTO | Создать `utility_service/web_api/parsers/__init__.py`, `geometry_save_request.py`; `utility_service/use_cases/schemas/edit_version/geometry_save_in.py`; `utility_service/web_api/tests/test_geometry_save_request_parser.py` |
| Settings | Изменить `utility_service/utils/settings.py` и `utility_service/utils/tests/test_settings.py` |
| Policy schema | Изменить `utility_service/infrastructure/postgresql/models/work_order/edit_version.py`; создать revision `c8e3f0a5b7d9_edit_version_geometry_policy.py` после `b7d2e9f4a6c8` |
| Open flow | Изменить `utility_service/use_cases/services/edit_version_service.py`, `utility_service/use_cases/deps.py`, `utility_service/infrastructure/postgresql/repositories/work_order_repository.py` |
| Codec | Создать `utility_service/infrastructure/postgresql/geometry_codec.py`, `utility_service/infrastructure/tests/test_geometry_codec.py` |
| Workspace | Изменить `utility_service/infrastructure/postgresql/sql/workspace_aggregate.sql` и workspace projection в repository; публичную schema не расширять |
| Новые DB tests | Создать `tests/integration_tests/test_geometry_policy_migration.py`, `test_geometry_policy_lifecycle.py`, `test_geometry_roundtrip.py` |
| Существующие schema tests | Обновить `first_save_schema_support.py`, `test_first_save_schema_migration.py`, `test_first_save_model_integration.py`, `test_first_save_model_parity.py`, `test_edit_version_migration.py` в `tests/integration_tests/`; metadata tests в `utility_service/infrastructure/tests/` |
| Deployment | Изменить `infra/docker-compose.yml`, `tests/test_compose_security_contract.py`; test Compose менять только при необходимости явной geometry configuration |
| Документы | Создать `docs/sprint_2/2026-10-08-day-4-geometry-runbook.md` при задаче 5 и implementation report после выполнения всех задач; обновить README |

Новая revision ID предварительно проверяется на отсутствие коллизии перед созданием. Не переписывать существующие migrations и не добавлять общий registry policies.

## Команды проверки

Команды выполняются из корня репозитория в PowerShell. Python на host не требуется. Исходники копируются в Docker image: после изменения файлов перед следующим прогоном выполнить сборку.

```powershell
docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml build backend_db_tests
```

**Команда U** — автономные тесты. Вместо `TEST_PATH` подставляется указанный в задаче файл/каталог; это обозначение аргумента, не переменная shell.

```powershell
docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml run --rm --no-deps -e RUN_DB_TESTS=0 backend_db_tests python -m pytest TEST_PATH --tb=short
```

**Команда D** — isolated DB tests с тем же правилом подстановки пути.

```powershell
docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml run --rm backend_db_tests python -m pytest TEST_PATH --tb=short
```

RED означает падение требуемого assertion или отсутствие ещё не созданного целевого модуля. Docker/network/неверный импорт зависимости не является доказательством RED. GREEN — exit code 0 и passed; skipped DB tests не считаются подтверждением.

По завершении DB-проверок, в том числе при ошибке, очистить только тестовый проект:

```powershell
docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml down -v --remove-orphans
```

## Задача 1. Policy и точный scalar grid

**Файлы:** `edit_geometry/types.py`, `policy.py`, `canonicalization.py`, package `__init__.py`; `test_geometry_policy.py`, `geometry_test_support.py`; settings и его tests.

**Интерфейсы:** frozen `GeometryPolicy(xy_resolution: Decimal, rounding_mode: str, version: int)` валидирует контракт v1; `quantize_ordinate(value: Decimal, policy: GeometryPolicy) -> Decimal`; `decimal_text(value: Decimal) -> str`. `Position` — `tuple[Decimal, Decimal]`. Модуль types также определяет frozen `GeometryValue(type: Literal['Point','LineString'], coordinates: tuple[Position, ...], srid: int = 4326)`; Point представлен одной позицией. `GeometryRuleError(code: str)` несёт domain code; `InvalidGeometryContext` отдельно обозначает повреждённый baseline/current.

- [x] Добавить parametrized tests: `assert quantize_ordinate(Decimal('0.00000015'), policy) == Decimal('0.0000002')`; отрицательный случай даёт `-0.0000002`; below-midpoint из spec даёт `0.0000001`; проверить grid `0.00000025` и `0.0000003`.
- [x] Добавить policy cases: `0.0000001`, `0.0000002500`, `360` принимаются; `0.000000099`, `360.000000001`, `0.0000001001`, `NaN`, Infinity, `1E+1000`, unknown mode/version отвергаются. Для `decimal_text`: `assert decimal_text(Decimal('-0.00')) == '0'`, `assert decimal_text(Decimal('1.00')) == '1'`.
- [x] Выполнить U для `utility_service/domain_services/tests/test_geometry_policy.py`; подтвердить RED.
- [x] Реализовать policy, scalar quantization и text formatting по spec §3 и §5.1. Precision рассчитывать по целому N/D; использовать новый Context, не наследовать traps. Типы не импортируют infrastructure. Перенести/переэкспортировать existing rounding enum без изменения доступного import из settings.
- [x] Подключить runtime policy validation к Settings; заменить тест принятия `1E+1000` отказом, сохранить non-default `0.00000025`. Добавить cross-check с независимым integer quotient/remainder oracle и внешним precision=2/Inexact trap.
- [x] Выполнить U для policy tests и `utility_service/utils/tests/test_settings.py`; подтвердить GREEN.

## Задача 2. Baseline-aware candidate и transition guard

**Файлы:** `canonicalization.py`, `structure.py`, `types.py`; `test_geometry_canonicalization.py`, `test_geometry_structure.py`, `geometry_test_support.py`.

**Интерфейсы:** `PreparedGeometry(representation: Literal['baseline_aligned','unmatched_structure'], geometry: GeometryValue, vertex_index: int | None, rejection_code: str | None)` — frozen результат; `prepare_geometry(request: GeometryValue, baseline: GeometryValue, policy: GeometryPolicy) -> PreparedGeometry`. Для bad count/Point baseline возвращается полный raw geometry с tag и error code, а не исключение до fingerprint. `TransitionResult(operation: Literal['unchanged','updated'], is_noop: bool, vertex_index: int | None)`; `validate_transition(baseline: GeometryValue, current: GeometryValue, prepared: PreparedGeometry) -> TransitionResult` поднимает GeometryRuleError или InvalidGeometryContext.

- [x] Добавить точные assertions восстановления: `assert prepared.geometry.coordinates[1][0] == Decimal('65.52500004')` для request X `65.52500003`; при изменении X неизменный off-grid Y сохраняется. Проверить то же правило для endpoints, обеих ординат одной вершины и нескольких raw отличий, исчезающих на сетке.
- [x] Добавить cases count mismatch без усечения, Point/two-vertex baseline → `FEATURE_NOT_EDITABLE`, endpoint/multiple internal → `GEOMETRY_STRUCTURE_CHANGED`, candidate вне диапазона → `GEOMETRY_INVALID`; structure имеет приоритет. `assert prepare_geometry(prepared.geometry, baseline, policy).geometry == prepared.geometry` для допустимого candidate.
- [x] Добавить таблицу переходов spec §6: `assert result.is_noop is True` только при equality с current; A→baseline даёт unchanged и не no-op; A→B вызывает structure rejection. Malformed current поднимает InvalidGeometryContext, не исправляется.
- [x] Выполнить U для двух новых test-файлов; подтвердить RED.
- [x] Реализовать candidate и guards. Не требовать current при prepare; не округлять current; не бросать domain rejection до построения PreparedGeometry. Signed-zero numeric equality не подменяет исходные Decimal baseline значения при копировании.
- [x] Выполнить U для `utility_service/domain_services/tests`; подтвердить GREEN, включая изменённый внешний Decimal context.

## Задача 3. JSON parser без промежуточного float

**Файлы:** `web_api/parsers/geometry_save_request.py`, его package `__init__.py`, `use_cases/schemas/edit_version/geometry_save_in.py`, `test_geometry_save_request_parser.py`.

**Интерфейсы:** frozen `GeometrySaveRequest(command_id: UUID, draft_version_token: str, geometry: GeometryValue)`; `parse_geometry_save_request(body: bytes) -> GeometrySaveRequest`; `GeometryRequestFormatError(ValueError)` — ошибка формата. HTTP mapping подключается в будущем endpoint, здесь нет registry/FastAPI dependency.

- [x] Написать тест исходных bytes с `0.000000149999999999999999999`: `assert request.geometry.coordinates[1][0] == Decimal('0.000000149999999999999999999')`, и связать с prepare/quantize, ожидая нижний узел. DTO не содержит float.
- [x] Добавить scientific notation, int/decimal equality, `-0`, token `"01"` без нормализации, boundary длины/exponent; bool/string/null/non-finite, duplicate keys, unknown fields, Z, пустой/одноточечный массив и MultiLineString вызывают GeometryRequestFormatError. Двухточечный LineString проходит parser и получает structure error относительно baseline из трёх точек.
- [x] Выполнить U для `utility_service/web_api/tests/test_geometry_save_request_parser.py`; подтвердить RED.
- [x] Реализовать stdlib JSON hooks для parse_int/parse_float/parse_constant/object_pairs_hook с проверкой исходных number tokens до Decimal. Проверять форму явно либо строго типизированным DTO без coercion. Не изменять общую GeoJSON float schema и не регистрировать PUT.
- [x] Выполнить U для parser tests и domain tests; подтвердить GREEN.

## Задача 4. Canonical envelope и SHA-256

**Файлы:** `fingerprint.py`, `types.py`, `test_geometry_fingerprint.py`, `geometry_test_support.py`.

**Интерфейсы:** frozen `FingerprintContext(work_order_id: UUID, edit_version_id: UUID, feature_id: UUID, actor_user_id: UUID, default_state_id: UUID, base_network_revision: int, draft_version_token: str)`; `baseline_structure_hash(baseline: GeometryValue) -> str`; `fingerprint_payload(context: FingerprintContext, baseline: GeometryValue, policy: GeometryPolicy, prepared: PreparedGeometry) -> bytes`; `command_fingerprint(context, baseline, policy, prepared) -> str`, с теми же типами параметров. CommandId/current не принимаются этими функциями.

- [x] Скопировать независимые golden bytes из spec §7.6 в test fixtures: `assert baseline_structure_hash(baseline) == 'sha256:342079da420e7190d6e5156e1ba210a5c41147c464569c4b8578f3568e8e8a39'`; command ожидает `geom-v1:sha256:1d01069ca8b22bf671865e99d831dc1ebc0fa2f65d71b64c972d99e2c414b622`. Проверять и bytes, и digest.
- [x] Добавить parametrized чувствительность к каждому context/policy/geometry field; token `1` и `01` различаются, альтернативные записи UUID/чисел нормализуются. Новый CommandId не влияет. Идентичный intent после изменения current/global settings сохраняет digest. Порядок вершин не сортируется.
- [x] Проверить endpoint/multiple-vertex candidate и unmatched count/Point baseline: весь request сохраняется, vertexIndex соответствует spec, нормализация записи не делает fallback grid-equivalent. Для двух fallback requests с разными точными значениями `assert fingerprint_a != fingerprint_b`.
- [x] Выполнить U для `utility_service/domain_services/tests/test_geometry_fingerprint.py`; подтвердить RED.
- [x] Реализовать exact envelope spec §7 с `sort_keys=True`, compact separators, `ensure_ascii=True`, UTF-8 без newline. Decimal strings получать через функцию задачи 1, без float; result/rejection_code не включать.
- [x] Выполнить U для fingerprint и parser tests; подтвердить GREEN. Не реализовывать command registry transactions ради этих тестов.

## Задача 5. Schema policy, backfill и окружение обновления

**Файлы:** новая revision `c8e3f0a5b7d9_edit_version_geometry_policy.py`, EditVersion model; `test_geometry_policy_migration.py`, `test_first_save_model_parity.py`, metadata tests; перечисленные в структуре старые migration/ORM fixtures; `infra/docker-compose.yml`, `tests/test_compose_security_contract.py`; новый runbook.

**Интерфейсы:** ORM поля `geometry_xy_resolution: Decimal` (NUMERIC без scale), `geometry_rounding_mode: str` (VARCHAR(32)), `geometry_policy_version: int` (SMALLINT). Имена CHECK: `ck_edit_versions_geometry_grid`, `ck_edit_versions_geometry_rounding`, `ck_edit_versions_geometry_policy_version`. Function/trigger: `work_order.guard_edit_version_geometry_policy` / `trg_edit_version_geometry_policy`; ошибка изменения использует constraint name `ck_edit_versions_geometry_policy_immutable` и SQLSTATE 23514.

- [x] Добавить metadata/DB tests обязательных полей без defaults, точного NUMERIC, NaN/Infinity/range/scale, mode/version; прямой UPDATE каждого policy field отклоняется, обновление revision/last_opened_at разрешено. Проверить лишние конечные нули grid.
- [x] Добавить populated upgrade с env grid `0.00000025`: `assert stored_grid == Decimal('0.00000025')`, geometry/revision/history snapshot неизменен; повтор upgrade и новая session сохраняют grid. Invalid configuration оставляет schema на предыдущей revision без частично добавленных fields. Проверить upgrade/downgrade/upgrade с фиксацией потери policy при downgrade.
- [x] Выполнить U для metadata и D для `tests/integration_tests/test_geometry_policy_migration.py`; подтвердить RED.
- [x] Реализовать migration-local validation без импорта runtime Settings. Backfill связанными параметрами Decimal; DDL+данные одной transaction; NOT NULL/CHECK/immutability без server defaults. Добавить ORM поля и совпадающие CHECK. Не менять старую revision.
- [x] Передать geometry env с одинаковыми defaults в migrate/API. Добавить test отсутствия зависимости migration от JWT settings и совпадения таблицы valid/invalid inputs migration/runtime. Runbook задаёт остановку API, non-default env, migration/start и последствия downgrade.
- [x] Обновить `seed_context` явным keyword `include_geometry_policy: bool = True`; для historical schema вызовы передают False. Два фиксированных INSERT shape выбираются флагом, без скрытого анализа каталога. Head fixtures включают три policy values. Обновить direct ORM/SQL inserts и exact metadata assertions. Historical tests сохраняют свои pinned revisions; их finally восстанавливает head.
- [x] Выполнить U для metadata и Compose contract tests; D для новой migration, старых migration tests и `test_first_save_model_parity.py`. GREEN требует действительных SQL проверок, а не skip.

## Задача 6. Назначение policy при open и сохранение при reopen

**Файлы:** EditVersionService, deps, WorkOrderRepository; `utility_service/use_cases/tests/test_edit_version_service.py`, `utility_service/infrastructure/tests/test_work_order_repository.py`, `utility_service/web_api/tests/test_work_orders_api.py`; новый `test_geometry_policy_lifecycle.py`.

**Интерфейсы:** `EditVersionService.__init__` получает keyword-only `geometry_policy: GeometryPolicy`; `WorkOrderRepository.create_open_edit_version` сохраняет прежние параметры и получает обязательный `geometry_policy: GeometryPolicy`. Deps создаёт policy из проверенных settings; сервис передаёт её только в ветке создания. `touch_edit_version` не принимает policy.

- [x] Добавить service test `assert create_call.kwargs['geometry_policy'] == configured_policy`; reopen/recovery existing open не вызывает create и не переназначает поля. Все конструкторы сервиса в тестах получают явную policy.
- [x] Добавить DB scenario: создать версию при `1e-7`, открыть повторно сервисом с `2.5e-7`, прочитать из новой session — grid остаётся `1e-7`; другая новая версия получает `2.5e-7`. Snapshot root+policy записывается атомарно, rollback не оставляет неполную версию.
- [x] Выполнить U для open/repository tests и D для `tests/integration_tests/test_geometry_policy_lifecycle.py`; подтвердить RED.
- [x] Реализовать DI и явное присвоение трёх ORM полей. Не читать global settings внутри repository и не менять API response contract. Адаптировать mocks/fixtures без ослабления assertions существующего open flow.
- [x] Выполнить U для существующих service/repository/API tests и D для lifecycle плюс `tests/integration_tests/test_work_order_seed_chain_integration.py`; подтвердить GREEN.

## Задача 7. Lossless codec, workspace readback и итоговая приёмка

**Файлы:** новый `geometry_codec.py`, workspace SQL и repository projection; `test_geometry_codec.py`, `test_work_order_repository_workspace_aggregate.py`, workspace/API tests; новый `test_geometry_roundtrip.py`; implementation report и README после выполнения.

**Интерфейсы:** `decode_geometry(ewkb: bytes) -> GeometryValue` сохраняет конечные 2D Decimal ordinates через `Decimal(repr(float_value))`; `encode_geometry(value: GeometryValue) -> bytes` возвращает EWKB с SRID и проверкой обратимости; `geometry_to_geojson(value: GeometryValue) -> dict[str, object]` возвращает JSON-compatible numbers. Для signed zero codec сохраняет знак Decimal до storage serialization; `decimal_text` применяется к fingerprint, а не к копированию baseline. SQL key `geometry_ewkb` содержит hex; repository отдаёт прежний `geometry_data` после decoding.

- [x] Добавить codec tests Point/LineString, wrong SRID/type/dimensions/non-finite, signed zero и round-trip guard. Для candidate grid `assert decoded == candidate`; для baseline дополнительно сверить storage ordinates и нормализованный PostGIS EWKB. Unsupported geometry не обрезается до XY.
- [x] Добавить DB/HTTP cases baseline `65.5250000499` при grid `1e-7` и другие значения по обе стороны midpoint: existing workspace response не округляет их до 9 fractional digits. Assert: untouched ordinates и полный Revert сохраняют EWKB, canonical grid после JSON parsing даёт прежние Decimal. Использовать существующий GET workspace с test auth/session dependency overrides и реальным repository, без создания PUT.
- [x] Выполнить U для codec tests и D для `tests/integration_tests/test_geometry_roundtrip.py`; подтвердить RED. Убедиться, что старый `ST_AsGeoJSON` путь действительно теряет контрольный baseline разряд.
- [x] Реализовать codec на установленных GeoAlchemy2/Shapely. Изменить только geometry feature projection на EWKB hex; сохранить один aggregate SQL execute, фильтр ST_Intersects, порядок features/associations, поля properties и публичную форму ответа. AOI display projection и legacy APIs не перестраивать.
- [x] Выполнить U для codec/workspace/API regression и D для roundtrip; подтвердить GREEN с новым чтением/session. Проверить bounded work на representative line без введения benchmark-подсистемы.
- [x] После последней правки пересобрать image. Выполнить полный автономный pytest через U без аргумента TEST_PATH; полный isolated DB набор через D с `tests/integration_tests`; затем Black/Ruff командами ниже. Разобрать каждый failure, не расширять scope несвязанными исправлениями без основания.
- [x] Проверить spec coverage, реальные результаты записать в `docs/sprint_2/2026-10-08-day-4-geometry-implementation-report.md`, обновить README/runbook. Оценить необходимость repository-change ingest по новым durable техническим знаниям, не по факту завершения плана. Изменения оставить unstaged.

Итоговое форматирование/линт из корня:

```powershell
docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml run --rm --no-deps -e RUN_DB_TESTS=0 backend_db_tests python -m black --check .
docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml run --rm --no-deps -e RUN_DB_TESTS=0 backend_db_tests python -m ruff check .
git diff --check
```

## Покрытие спецификации и порядок исполнения

| Раздел спецификации | Задачи |
| --- | --- |
| 1–3: scope, архитектура, policy | 1, 5, 6 |
| 4: request format/parser | 3 |
| 5–6: canonicalization, структура, transitions | 1, 2 |
| 7: fingerprint/golden/rejections | 4 |
| 8: durable policy/backfill | 5, 6 |
| 9: storage/readback | 7 |
| 10–13: integration, приёмка, документы | 5–7 и финальная проверка |

Рекомендуемый порядок — задачи 1–7 последовательно. Tasks 3/4 используют контракты ядра; schema/open/readback связаны существующими fixtures. Параллельное изменение shared files не требуется.

План прошёл самопроверку покрытия spec, согласованности имён/типов, независимых test cycles и пяти review-focus рисков. Все implementation checkbox выполнены. Фактические команды и результаты сохранены в 2026-10-08-day-4-geometry-implementation-report.md.

Следующий этап — просмотр плана пользователем и выбор способа исполнения. Для этого тесно связанного набора задач рекомендуется последовательная реализация в текущем чате через `superpowers:executing-plans`; альтернативный вариант — отдельные implementer/reviewer subagents по задачам после выбора пользователя. До этого product changes не выполняются.
