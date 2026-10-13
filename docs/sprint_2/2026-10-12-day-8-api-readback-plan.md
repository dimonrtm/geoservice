# День 8 Sprint 2 — план реализации API и durable readback

> **Для агента-исполнителя:** обязательный навык — `superpowers:executing-plans` для последовательного исполнения либо `superpowers:subagent-driven-development`, если пользователь выберет этот способ. Читать план вместе со спецификацией. Шаги отмечать после проверки. Запрет репозитория на git add/commit/push имеет приоритет над навыками; вместо commit оставлять изменения unstaged.

**Цель:** подключить публичный Save и вернуть в workspace согласованные current geometry, token, validation и baseline change set для Save/Revert.

**Архитектура:** готовый raw JSON parser вызывает существующий Save service. Workspace расширяется в существующем repository одним SQL snapshot; geometry decoding и проверка diff выполняются после access guards. Новых таблиц, fingerprint-протоколов и Save transactions нет.

**Стек:** Python 3.12, FastAPI/Pydantic, SQLAlchemy 2/asyncpg, PostgreSQL 16/PostGIS 3.4, Decimal, pytest/httpx, существующие зависимости.

**Спецификация:** [API и durable readback](2026-10-12-day-8-api-readback-design.md), принята пользователем 2026-10-12.

**Статус:** реализация завершена последовательным исполнением в текущем чате; независимое review и проверки зафиксированы в отчёте и execution ledger.

## Общие ограничения

- Сохранить parser Дня 4: LineString, минимум две XY-пары, конечные JSON numbers, X `[-180,180]`, Y `[-90,90]`, числовой token до 64 символов, модуль явной exponent до 324; запрет extras/duplicate keys.
- Ошибки parser/path validation: `422 REQUEST_VALIDATION_ERROR` до Save, без новой registry row. Не вводить обобщённую geometry-модель или `geom-rejected-v1`.
- Точное Decimal parsing до float; existing EWKB codec для current/baseline; никакой canonicalization при GET.
- Строгая error shape `{code,message,correlationId}` локальна geometry PUT и workspace GET. List/open/legacy не менять.
- Существующие Save service, root lock, fingerprint, replay, rejection/access retry, revision и event semantics сохраняются.
- Workspace показывает текущий snapshot всей версии; старый replay не заменяет current. GET не пишет registry/history/revision и не берёт Save lock.
- Проверять diff всей версии до AOI-фильтра. Сохранять старый состав отображаемых features/associations.
- Tests только в isolated `geoservice-db-tests` / `geo_test`. Не сбрасывать demo/production данные. Новая session не является фактическим restart процесса.
- Без frontend, S2-X01, dependencies, migration, baseline repair/backfill и нового endpoint Revert.
- Документы по-русски в `docs/sprint_2`; стиль кода и SQL — `docs/agent-memory/patterns/2026-10-07-python-formatting-style.md`.
- Перед исполнением проверить checkout и пользовательские изменения. Worktree при планировании не создавать; isolation решается при выбранном способе исполнения.

## Особое внимание при review

1. Браузерный OPTIONS preflight не разрешает PUT в текущем CORS: настроенный origin должен получить разрешение PUT, посторонний — отказ; задача 1.
2. Повреждённый EWKB чужого workspace не должен обходить assignment masking и раскрывать corruption через 422 вместо 404; задача 3.
3. Геометрия изменена вне AOI или оставлена operation=unchanged: нельзя выдавать ложный чистый change set; задачи 2–3.
4. Parser получает повторяющиеся ключи или число около midpoint: автоматическая FastAPI/Pydantic float-конверсия не должна предшествовать raw parser; задача 1.
5. Existing off-grid test меняет current без baseline: обновить создание fixture под новый invariant, не ослабляя проверку lossless round trip; задачи 2–4.

## Файлы и зависимости

Backend paths ниже относительны `apps/backend/`.

| Область | Файлы и ответственность |
| --- | --- |
| HTTP | Изменить `utility_service/web_api/api/work_orders.py`; создать `work_order_edit_route.py` и `geometry_save_contract.py` рядом: локальный error adapter и request OpenAPI schema |
| Browser access | Изменить `utility_service/web_api/main.py`: добавить PUT в existing CORS allow_methods |
| Shared response types | Создать `utility_service/use_cases/schemas/edit_version/geometry_contract.py`: BasicValidationOut, UpdatedFeatureOut, GeometrySaveResponseOut; существующие result dataclasses/builder не перестраивать |
| Workspace rows/SQL | Изменить `utility_service/infrastructure/postgresql/repository_rows/workspace.py`, `sql/workspace_aggregate.sql`, `repositories/work_order_repository.py` |
| Projection | Создать `utility_service/use_cases/services/workspace_draft_projection.py`, изменить `workspace_service.py` |
| Workspace schemas | Создать `utility_service/use_cases/schemas/workspace/change_set_out.py`, изменить `edit_version_workspace_out.py` и exports |
| API tests | Создать `utility_service/web_api/tests/test_geometry_save_api.py`, `test_work_order_edit_contract.py`; использовать существующие auth/build_app helpers |
| Unit tests | Расширить `utility_service/infrastructure/tests/test_work_order_repository_workspace_aggregate.py`, `utility_service/use_cases/tests/test_workspace_service.py`, `test_workspace_schemas.py`; создать `test_workspace_draft_projection.py` |
| DB tests | Создать `tests/integration_tests/test_workspace_draft_readback.py`, `test_geometry_save_api_integration.py`, `test_workspace_save_concurrency.py`, helper `workspace_api_support.py` |
| Existing fixture | Обновить `tests/integration_tests/first_save_schema_support.py`, `test_geometry_roundtrip.py` для согласованного off-grid baseline/current |
| Документы | Актуализировать README и после реализации создать `docs/sprint_2/2026-10-12-day-8-api-readback-implementation-report.md` с фактическими доказательствами |

Порядок исполнения: 1 → 2 → 3 → 4 → 5 → 6. Setup и fixtures входят в задачу, которая их использует. Каждый этап завершить целевыми тестами и review diff; staging/commit отсутствуют.

## Команды проверки

PowerShell из корня репозитория. Test image копирует исходники: после изменений перед запуском пересобрать его.

```powershell
docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml build backend_db_tests
```

Ниже U(`PATH`) означает:

```powershell
docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml run --rm --no-deps -e RUN_DB_TESTS=0 backend_db_tests python -m pytest PATH --tb=short
```

D(`PATH`) означает:

```powershell
docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml run --rm backend_db_tests python -m pytest PATH --tb=short
```

PATH — перечисленные в задаче backend-relative пути, допускается несколько путей через пробел. RED — конкретное ожидаемое падение теста из-за отсутствующей функциональности; network/Docker/dependency errors не считаются RED. GREEN — exit 0 с выполненными assertions; обязательные DB tests не должны быть skipped. План не утверждает, что окружение или тесты уже запускались.

## Задача 1. Geometry PUT, локальные ошибки и CORS

**Файлы:** HTTP/shared response types/browser access/API tests из таблицы. Переиспользовать `web_api/parsers/geometry_save_request.py` без смены правил.

**Потребляет:** `parse_geometry_save_request(body: bytes) -> GeometrySaveRequest`, `EditVersionService.save_geometry(..., request: GeometrySaveRequest) -> SaveGeometryResult`, `require_editor`, `structured_error_response`.

**Предоставляет:**

```python
class WorkOrderEditRoute(APIRoute):
    def get_route_handler(self) -> Callable[[Request], Awaitable[Response]]

async def save_feature_geometry(
    work_order_id: UUID,
    edit_version_id: UUID,
    feature_id: UUID,
    request: Request,
    user: AuthUserDTO,
    edit_version_service: EditVersionService,
) -> JSONResponse
```

Dependency defaults реализовать через существующий Depends pattern. В `work_orders.py` выделить дочерний router с route_class=WorkOrderEditRoute только для GET workspace и PUT geometry; включить его в существующий work_orders_router. List/open остаются на прежнем route class. Wrapper ловит RequestValidationError и GeometryRequestFormatError, возвращает 422 REQUEST_VALIDATION_ERROR через existing structured helper; auth/domain/internal handlers остаются действующими.

`GeometrySaveResponseOut` описывает прежний successful payload; `BasicValidationOut` содержит четыре Literal-поля принятых значений. Nullable basicValidation обязательна. В `geometry_save_contract.py` определить `WorkOrderEditErrorOut(BaseModel)` с extra=forbid и обязательными code:str, message:str, correlation_id:str (alias correlationId); использовать в responses PUT/GET. Request schema `GEOMETRY_SAVE_REQUEST_SCHEMA: dict[str, Any]` в том же файле — самодостаточная inline OpenAPI schema без неразрешимых `$defs` references, описывает реальный parser. Endpoint читает `await request.body()` и возвращает `JSONResponse(status_code=result.status_code, content=result.payload)`; raw body не объявлять как float Pydantic argument. Response model документируется, а equality JSON payload проверяется тестом без пересборки replay.

- [x] Написать `test_put_passes_exact_request_and_actor`: body содержит `0.000000149999999999999999999`, token `"01"`; переданный DTO сохраняет Decimal и token точно, actor берётся из auth; JSON ответа равен service payload, status 200.
- [x] Написать `test_put_format_errors_do_not_call_save`: параметризовать короткую линию, MultiLineString, Z/M, duplicate key, extras, NaN/Infinity, invalid UUID/token, число вне диапазона/лимита; assert status=422, code=REQUEST_VALIDATION_ERROR, set(body)={code,message,correlationId}, service call count=0. Отдельно path UUID ошибки PUT/GET.
- [x] Написать `test_edit_route_error_scope`: parser и workspace path ошибки имеют strict body; контрольная ошибка list/open или legacy сохраняет прежний handler behavior.
- [x] Написать `test_put_guards_and_domain_errors`: anonymous/inactive/reviewer не вызывают Save; WorkOrderApiError service double отображается без изменения status/code/message, header/body correlationId совпадают; unexpected exception даёт existing INTERNAL_ERROR.
- [x] Написать `test_put_cors_preflight` на `web_api.main.app`: OPTIONS с настроенным Origin и Access-Control-Request-Method=PUT разрешает метод; неподходящий Origin не разрешён. Не запускать startup/lifespan с подключением к demo DB.
- [x] Выполнить U(`utility_service/web_api/tests/test_geometry_save_api.py utility_service/web_api/tests/test_work_order_edit_contract.py`), зафиксировать RED.
- [x] Реализовать перечисленные interfaces/models/route wrapper, добавить PUT в CORS без расширения origins и проверить OpenAPI registration.
- [x] Пересобрать image, выполнить те же U и существующий `test_geometry_save_request_parser.py`; GREEN и review diff. Нельзя исправлять тесты расширением parser/fingerprint.

## Задача 2. Один SQL snapshot current и baseline

**Файлы:** rows/SQL/repository, repository unit tests, новый `test_workspace_draft_readback.py`.

**Потребляет:** существующий `get_workspace_aggregate(*, work_order_id: UUID, edit_version_id: UUID) -> WorkspaceAggregateRow | None`.

**Предоставляет:** сохранить signature; добавить `draft_revision: int`, `default_state_id: UUID` в WorkspaceEditVersionRow. Новые frozen rows:

```python
WorkspaceBaselineStateRow(id: UUID, work_order_id: UUID, base_network_revision: int, status: str)
WorkspaceDraftFeaturePairRow(
    feature_id: UUID,
    current_feature_type: str | None,
    baseline_feature_type: str | None,
    current_geometry_ewkb: str | None,
    baseline_geometry_ewkb: str | None,
    operation: str | None,
    visible: bool,
)
```

В WorkspaceAggregateRow добавить `baseline_state: WorkspaceBaselineStateRow | None`, `draft_feature_pairs: tuple[WorkspaceDraftFeaturePairRow, ...]`; aoi сделать `WorkspaceAoiRow | None`, чтобы отсутствующая AOI не стирала найденную версию. Геометрия здесь — EWKB hex, ещё не decoded. В existing features_data сохранять geometry_ewkb вместо geometry_data; decoding переносится в service после guards. Это внутреннее изменение mapping, внешний features contract прежний.

SQL ограничивает baseline через context.default_state_id, собирает пары всех current/baseline features версии, включая отсутствующую сторону пары. Не применять AOI к этому набору. Existing workspace_features остаётся AOI-filtered для карты/associations; visible отмечает принадлежность пары этому набору. Не использовать ST_Equals как замену точному сравнению упорядоченных координат. Missing baseline/AOI не должны исчезать через INNER JOIN и превращаться в «version missing»: сохранить root row, чтобы service классифицировал контекст.

- [x] Написать `test_workspace_snapshot_includes_revision_and_all_baseline_pairs`: mapping содержит revision/default_state/metadata и скрытую AOI пару; один session.execute, нет дополнительных SELECT. Missing baseline/current side представлены None.
- [x] Написать DB `test_readback_pairs_use_version_baseline`: при наличии другого Default выбирается исходный default_state_id; AOI по-прежнему ограничивает displayed features и associations, но не полный набор пар.
- [x] Выполнить U(repository test) и D(`tests/integration_tests/test_workspace_draft_readback.py`) для RED.
- [x] Расширить SQL, rows и mapping без decoding EWKB в repository. Existing missing target возвращает None; corruption доступного root не скрывается missing-target результатом.
- [x] Обновить repository unit expectations для raw EWKB и выполнить U/D для GREEN. Проверить отсутствие второго read query и mutation locks.

## Задача 3. Производный change set и workspace contract

**Файлы:** projection, workspace schemas/service и unit tests из таблицы; existing `test_geometry_roundtrip.py` fixture.

**Потребляет:** rows задачи 2 и BasicValidationOut задачи 1; existing decode_geometry/geometry_to_geojson и числовое сравнение GeometryValue.

**Предоставляет:**

```python
class WorkspaceChangeSetOut(BaseModel):
    # aliases: featureId, vertexIndex, baselineGeometry; operation = Literal["updated"]
    ...

@dataclass(frozen=True)
class WorkspaceDraftProjection:
    draft_version_token: str
    has_persisted_change_set: bool
    basic_validation: BasicValidationOut | None
    change_set: WorkspaceChangeSetOut | None

def project_workspace_draft(aggregate: WorkspaceAggregateRow) -> WorkspaceDraftProjection
```

ChangeSet fields: feature_id:UUID, vertex_index:int>=1, baseline_geometry:GeoJSONLineString, operation:Literal["updated"]. Helpers чистые, без БД/global settings. WorkspaceEditVersionOut получает четыре обязательных поля с camelCase serialization aliases, nullable поля без default omission.

Projection сравнивает все пары численно без округления: missing side/type mismatch/неподдерживаемая operation → invalid; равные geometries требуют unchanged. Непустой diff допустим только для одной видимой line с baseline минимум 3 вершины, той же структурой и одной изменённой внутренней вершиной, operation=updated. Равные unchanged points/двухвершинные lines допустимы. Signed zero не создаёт ложный diff, но baseline codec сохраняет исходное представление. Invalid context поднимает InvalidGeometryContext/ValueError; WorkspaceService преобразует в 422 WORKSPACE_CONTEXT_INVALID после role/assignment/lifecycle guards.

- [x] Написать `test_workspace_projection_states`: initial token1→Save token2→Revert token3; expected false/null/null, true/summary/changeSet, false/null/null; vertexIndex=1 и baseline точны, current остаётся в features.
- [x] Написать `test_workspace_projection_rejects_inconsistent_pairs`: missing baseline, mismatched baseline root, operation/diff mismatch, multiple changed, endpoint/count changes, hidden changed feature → 422, без repair. Отдельный case changed geometry с operation=unchanged вне AOI.
- [x] Написать `test_unchanged_points_and_short_lines_are_not_edit_candidates`: такие baseline/current пары не делают clean workspace ошибочным.
- [x] Написать `test_foreign_workspace_masks_corrupt_ewkb`: для того же corrupt aggregate чужому actor 404, назначенному actor 422; malformed raw EWKB декодируется только после guards.
- [x] Написать schema test обязательных nullable полей и equality current/response geometry; выполнить U(`utility_service/use_cases/tests/test_workspace_draft_projection.py utility_service/use_cases/tests/test_workspace_service.py utility_service/use_cases/tests/test_workspace_schemas.py`) для RED.
- [x] Реализовать projection и service integration; формировать summary current draft из подтверждённой persisted структуры, не из последнего command payload и не через новую external/spatial validation при GET.
- [x] Для off-grid regression добавить keyword `baseline_wkt: str = BASELINE` в existing seed_context и использовать его при INSERT исходника. Передавать off-grid WKT при создании fixture в test_geometry_roundtrip вместо изменения только current после копирования. Default поведения helper для остальных тестов не менять; production baseline не обновлять.
- [x] Пересобрать image, выполнить целевые U, D(`tests/integration_tests/test_geometry_roundtrip.py tests/integration_tests/test_workspace_draft_readback.py`) и прежние API workspace tests; добиться GREEN.

## Задача 4. Полный HTTP-путь с реальной БД

**Файлы:** `tests/integration_tests/workspace_api_support.py`, `test_geometry_save_api_integration.py`.

**Потребляет:** существующие `run_committed_scenario`, `seed_save_context`, `snapshot_save_state`; handlers/routes задач 1–3.

**Предоставляет:** `build_workspace_api(engine: AsyncEngine) -> FastAPI` — приложение с correlation middleware, handlers, auth/work_orders routers и override только get_session на fresh AsyncSession(engine) на каждый HTTP request. Использовать настоящие auth repositories/services; JWT строить existing create_access_token. AsyncClient/ASGITransport запускать внутри одного event loop сценария. Для open-chain fixture подготовить assigned WorkOrder, DefaultState и Editor без открытой EditVersion до обращения к POST; не выдавать service doubles за HTTP + DB доказательство.

- [x] Написать `test_http_open_save_readback_revert`: Open→initial GET→PUT→новый client GET→PUT baseline→GET; tokens 1/2/3, changeSet/null, exact baseline, два events, immutable DefaultState. Fresh sessions подтверждаются dependency, ответ Save соответствует committed independent DB read.
- [x] Написать `test_http_format_failure_does_not_reserve_id`: короткая линия/MultiLineString дают 422 REQUEST_VALIDATION_ERROR и отсутствие command row; исправленный запрос с тем же ID может успешно выполниться. Двухвершинная линия даёт durable GEOMETRY_STRUCTURE_CHANGED; её исправление с прежним ID даёт COMMAND_ID_REUSED.
- [x] Написать `test_http_stale_and_old_replay`: Save A(token1), Save B(token2), replay A возвращает исходный token2, GET показывает B/token3; новый stale ID возвращает строгий 409 и durable rejection. Geometry/revision/events не изменяются retry.
- [x] Написать `test_http_current_authorization`: anonymous/reviewer/inactive, другой assignee, несовпадающая пара WorkOrder/EditVersion и закрытый lifecycle; real dependencies дают принятые коды без данных чужой версии.
- [x] Выполнить D(`tests/integration_tests/test_geometry_save_api_integration.py`) для RED; реализовать только необходимый test harness/fixture и исправления интеграции в пределах спецификации.
- [x] Повторить D для GREEN; unexpected SQL/transaction/protocol error не маскировать handler-ом expected domain error. Сопоставить результаты с D8-01–D8-08, D8-10–D8-11.

## Задача 5. Конкурентное чтение и финальный OpenAPI contract

**Файлы:** `test_workspace_save_concurrency.py`, API contract tests задачи 1; при необходимости точечные исправления SQL/schema wiring.

**Потребляет:** HTTP harness задачи 4, one-statement readback и existing Save repository; новых production hooks не добавляет.

- [x] Написать `test_workspace_read_during_uncommitted_save`: test-only wrapper complete_command приостанавливает Save после write_current на asyncio.Event; отдельный GET до commit возвращает старые geometry/token/changeSet без ожидания Save lock; после release и commit новый GET возвращает целиком новое состояние. Использовать bounded wait_for, не timing sleeps.
- [x] Написать `test_openapi_matches_save_and_workspace`: разрешить все schema refs, проверить PUT method, path UUID, request additionalProperties=false, type LineString, XY/minItems, required nullable output fields; 422 с code/message/correlationId и без detail. Прогнать реальные success/error responses через соответствующие модели; response JSON replay не меняется.
- [x] Написать regression test старых list/open schemas/status и существующего parser exact-number behavior через HTTP; request schema не должна скрывать фактические числовые ограничения — непредставимые lexical rules описаны текстом.
- [x] Выполнить D(concurrency) и U(API contract) для RED; завершить недостающий wiring, повторить для GREEN.
- [x] Просмотреть generated OpenAPI: nullability, aliases, модели BasicValidation/ChangeSet, описания replay/stale и error responses соответствуют спецификации. Не включать unsupported geometry types ради OpenAPI.

## Задача 6. Регрессия, review и отчёт

**Файлы:** изменённые файлы задач 1–5; README и будущий implementation report.

- [x] Выполнить backend format/lint: в isolated image `python -m black --check .`, `python -m ruff check .` через тот же compose run с RUN_DB_TESTS=0; исправлять только затронутый код. Проверить SQL formatting вручную.
- [x] Выполнить U(`.`), затем D(`tests/integration_tests`) после последней пересборки. Полная DB regression нужна из-за изменения shared workspace mapping/fixture; не повторять полные прогоны без новых изменений или непокрытого риска.
- [x] Выполнить `git diff --check`; проверить фактический diff на отсутствие изменений baseline, Save semantics, parser rules, fingerprint, frontend, schema migration и сторонних API. Разрешение PUT в CORS — ожидаемое изменение.
- [x] Провести review выбранным пользователем способом. Проверить все пять Review Focus и сопоставить D8-01–D8-12 с конкретными результатами. Замечания исправить и повторить только затронутые проверки.
- [x] Создать implementation report с фактическими командами/результатами, ограничениями и отметкой, проводился ли настоящий restart. Не выдавать тесты новой session за restart; не объявлять Sprint 2 целиком завершённым.
- [x] Обновить docs/sprint_2/README.md. Решить необходимость durable knowledge ingest по AGENTS.md отдельно: новый API/readback может потребовать обновления Code_wiki по источникам; размер задачи/успех тестов не являются триггером. Не дублировать спецификацию в agent memory.
- [x] Оставить изменения unstaged. Не выполнять git add/commit/push и не создавать PR.

## Покрытие спецификации и самопроверка плана

| Требование | Задачи |
| --- | --- |
| PUT/parser/strict errors/Editor/CORS | 1, 4, 5 |
| One-snapshot baseline/current/revision | 2, 3, 5 |
| Nullable summary/changeSet, Revert, exact codec | 3, 4 |
| Existing replay/access/domain semantics | 1, 4, регрессия 6 |
| Corrupt context и AOI masking | 2, 3, 4 |
| OpenAPI/runtime parity | 1, 5 |
| Durable DB readback и граница restart | 4, 6 |

Самопроверка: signatures соседних задач согласованы; parser/fingerprint не переписываются; новые файлы имеют отдельную ответственность; тесты Review Focus распределены по владельцам. Кодовые фрагменты задают interfaces и assertions, а не готовую реализацию. Фактические команды, результаты и отклонения от порядка RED/GREEN отражены в execution ledger; задачи 4–5 подтвердили уже реализованный wiring с первого запуска.

## Передача в исполнение

После проверки плана пользователь выбирает последовательное исполнение в этом чате (`superpowers:executing-plans`) либо исполнение по задачам с субагентами (`superpowers:subagent-driven-development`). Для этого плана рекомендовано последовательное исполнение: HTTP, row contracts, projection и интеграционные fixtures тесно связаны; отдельное итоговое review проверит полный путь. Само создание плана не запускает реализацию.

## Фактическое исполнение

Пользователь поручил реализацию 2026-10-12. Последовательное исполнение завершено; [отчёт](2026-10-12-day-8-api-readback-implementation-report.md) содержит матрицу D8-01–D8-12 и границы проверки. Отметки плана обозначают достигнутый результат; фактический порядок RED/GREEN и первые зелёные интеграционные прогоны описаны в [журнале](2026-10-12-day-8-execution-ledger.md).
