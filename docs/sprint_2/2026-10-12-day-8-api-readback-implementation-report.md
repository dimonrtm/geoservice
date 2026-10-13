# День 8 Sprint 2 — API и durable readback

Дата: 2026-10-12. Статус: реализация и проверки Дня 8 завершены.

Основание: [принятая спецификация](2026-10-12-day-8-api-readback-design.md),
[план](2026-10-12-day-8-api-readback-plan.md) и
[журнал исполнения](2026-10-12-day-8-execution-ledger.md).

## Результат

Добавлен публичный
`PUT /api/v1/work-orders/{work_order_id}/edit-versions/{edit_version_id}/features/{feature_id}/geometry`.
Он передаёт raw JSON существующему Decimal parser и вызывает готовый Save service.
Ответ сохраняет исходный payload команды, включая исторический результат replay.
PUT разрешён в CORS для настроенных origins.

Workspace GET возвращает обязательные `draftVersionToken`,
`hasPersistedChangeSet`, nullable `basicValidation` и nullable `changeSet`.
Непустой changeSet содержит featureId, индекс изменённой внутренней вершины,
полную baselineGeometry и operation. UI может получить baseline для Revert из API,
не зная seed coordinates. Revert выполняется тем же PUT с новым CommandId.

Revision, baseline и current читаются одним SQL snapshot. Полный набор пар
проверяется независимо от AOI-фильтра карты. EWKB decoding и projection выполняются
после access guards; чужой workspace остаётся 404 даже при повреждённой геометрии.
Несогласованный доступный контекст возвращает `422 WORKSPACE_CONTEXT_INVALID`.

Для PUT и workspace GET request/path errors имеют строгую форму
`{code,message,correlationId}`. Auth/domain/internal errors сохраняют действующие
коды и текущий correlationId. Generated OpenAPI описывает request, success,
nullable workspace fields и errors. List/open/legacy contracts сохранены.

## Проверки

Команды выполнены из корня репозитория; image пересобирался после изменений.

```powershell
docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml build backend_db_tests
docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml run --rm --no-deps -e RUN_DB_TESTS=0 backend_db_tests python -m black --check .
docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml run --rm --no-deps -e RUN_DB_TESTS=0 backend_db_tests python -m ruff check .
docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml run --rm --no-deps -e RUN_DB_TESTS=0 backend_db_tests python -m pytest . --tb=short
docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml up -d --force-recreate postgis_test
docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml run --rm backend_db_tests python -m pytest tests/integration_tests --tb=short
git diff --check
```

| Проверка | Фактический результат |
| --- | --- |
| Полная unit-регрессия | 610 passed, 269 skipped: DB отключена намеренно |
| Полная DB-регрессия на свежей geo_test | 270 passed, 0 skipped |
| Финальный Black | 314 files unchanged |
| Финальный Ruff | All checks passed |
| После стилевой правки review | 22 passed: workspace service, HTTP + DB и OpenAPI |
| AST / SQL tokens до и после стилевой правки | Не изменены в пяти затронутых файлах |
| git diff --check | Без ошибок |

В pytest остаются два предупреждения зависимостей: `passlib/crypt` и
`starlette/anyio BlockingPortal`. Они присутствовали в исходном baseline.

Первый полный DB-прогон на использованной несколькими committed сценариями
одноразовой БД дал 267 passed / 3 failed. Старые cross-context fixtures пытались
удалить working-copy rows, связанные с append-only history. Проверка после
пересоздания только `geoservice-db-tests/postgis_test` прошла полностью.
Production constraints и старые fixtures не менялись; demo БД не затрагивалась.

## Покрытие D8-01–D8-12

Пути тестов ниже относительны `apps/backend/`.

| ID | Доказательство |
| --- | --- |
| D8-01 | `web_api/tests/test_geometry_save_api.py::test_put_passes_exact_request_and_actor` (внутри `utility_service/`); HTTP + DB `test_http_open_save_readback_revert` |
| D8-02 | `test_put_format_errors_do_not_call_save`, path validation, `test_http_format_failure_does_not_reserve_id`: короткая/иная geometry не резервирует ID |
| D8-03 | Двухвершинный request в HTTP + DB даёт durable GEOMETRY_STRUCTURE_CHANGED без нового event; действующие Save rejection tests включены в полную регрессию |
| D8-04 | `test_http_current_authorization`: anonymous, reviewer, inactive, другой assignee, mismatched target и закрытый lifecycle для PUT/GET |
| D8-05 | `test_http_stale_and_old_replay`, corrected/reused ID и действующие command/rejection tests; строгие errors проверяют текущий correlationId |
| D8-06 | Initial → Save → no-op → Revert через HTTP; tokens 1/2/2/3, nullability, current geometry, validation и baseline changeSet |
| D8-07 | Старый replay A возвращает token2, новый GET после B — token3 и geometry B; состояние не откатывается |
| D8-08 | `test_workspace_draft_projection.py`: missing/mismatched baseline, operation/diff, multiple/endpoint/count/hidden/corrupt; repository DB test включает скрытые feature pairs |
| D8-09 | `test_workspace_save_concurrency.py`: Event barrier после write_current; независимый GET читает целиком старый snapshot до commit и новый после |
| D8-10 | Настоящие auth/service/repository, новая AsyncSession на запрос и новый app/client для readback; DefaultState не изменяется, события проверены независимым чтением |
| D8-11 | Exact Decimal около midpoint через HTTP, существующие parser/policy/fingerprint tests, `test_geometry_roundtrip.py` с согласованным off-grid baseline/current |
| D8-12 | `test_work_order_edit_contract.py`: разрешимые refs, UUID/XY, required nullable fields, strict errors, CORS и сохранение open validation; общая регрессия остальных routes |

## Независимое review

Fresh-context reviewer проверил tracked и untracked изменения относительно
`9d23ce97b8ec1081cd38854f00c24543fbcc20e4`, спецификацию и пять Review Focus плана.
Critical/Important замечаний нет. Единственное Minor касалось многострочного
форматирования новых вызовов/словарей/SQL; исправлено по принятому правилу проекта.
Неизменность AST и SQL tokens проверена отдельно, затронутые сценарии повторены.

Отложенные reviewer-ом вопросы оценены отдельно: повторная spatial/topology
validation при GET исключена дизайном; реальный restart относится к последующему
этапу; повторный полный набор на dirty disposable DB требует свежей fixture.
Ни один из этих пунктов не выдаётся за доказанную возможность Дня 8.

## Границы и документация

Фактический browser/backend restart не выполнялся. Новый client/app/session
подтверждает durable independent readback, но не заменяет restart smoke.
Frontend Save/Revert, S2-X01 и приёмка всего Sprint 2 остаются отдельными задачами.
Save service, parser rules, fingerprints, schema migrations и production baseline
не изменялись.

Новое устойчивое знание сохранено через `/ingest repository-change` в
`Code_wiki/архитектура/edit_version_api_readback.md`, обновлены технический индекс
и компактный реестр. В ноде зафиксирован follow-up к историческим описаниям
decoding и отсутствия PUT; старые утверждения вне разрешённой post-ingest
correction не переписывались. Wiki lint: 37 прежних `missing_frontmatter` только
в `RAW_inputs/`; новых ошибок вне RAW нет. Agent memory не дополнена: уникальное
знание уже сохранено в коде, спецификации и технической ноде.

Изменения оставлены unstaged для проверки пользователем в `first-edit-save`.
Git add/commit/push и создание PR не выполнялись.
