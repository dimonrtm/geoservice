# Cross-Context Consistency Checker

Дата: 2026-07-06
Статус: согласован для written spec
Расположение: `docs/superpowers/specs`

## Назначение

Добавить операционный read-only слой проверок согласованности для UUID-ссылок
между bounded contexts, которые намеренно не закреплены cross-schema FK.

Текущая модель данных осознанно не связывает будущие сервисные границы через
FK на уровне PostgreSQL. Это сохраняет DDD/anti-corruption boundary между
`auth`, `utility_network`, `work_order` и будущим `review_post`, но требует
отдельной наблюдаемости: эксплуатация должна видеть orphan UUID и semantic
mismatch до того, как они проявятся как случайные `not found`, 500 или
ошибка пользователя в позднем сценарии.

Checker не заменяет service-level validations. Сервисы отвечают на вопрос:
"можно ли выполнить конкретный use case сейчас?". Checker отвечает на вопрос:
"есть ли в базе поврежденные cross-context ссылки как класс?".

Базовый контракт:

```text
cross-schema FK запрещены
runtime use cases проверяют критичные команды
operational checker диагностирует всё состояние базы
```

## Контекст

В текущей архитектуре:

- `work_order.work_orders.assignee_user_id` и
  `work_order.work_orders.created_by_user_id` являются plain UUID ссылками на
  `"user".users.id`;
- `utility_network.default_states.work_order_id` является plain UUID ссылкой на
  `work_order.work_orders.id`;
- `work_order.edit_versions.default_state_id` является plain UUID ссылкой на
  `utility_network.default_states.id`;
- `work_order.edit_versions.owner_user_id` является plain UUID ссылкой на
  `"user".users.id`;
- FK внутри одной схемы и одного aggregate/baseline slice остаются допустимы,
  например `work_order.edit_version_associations` может ссылаться на
  `work_order.edit_version_features`.

Metadata tests уже защищают отсутствие запрещенных cross-schema FK. Новый
checker дополняет этот договор: раз БД не навязывает связи физически, CI/smoke
должны регулярно доказывать, что plain UUID links остаются согласованными.

## Scope Первого Increment

Первый increment покрывает только существующие таблицы и поля:

```text
work_order.work_orders.assignee_user_id -> "user".users.id
work_order.work_orders.created_by_user_id -> "user".users.id
utility_network.default_states.work_order_id -> work_order.work_orders.id
work_order.edit_versions.default_state_id -> utility_network.default_states.id
work_order.edit_versions.owner_user_id -> "user".users.id
```

Дополнительно вводится semantic check:

```text
work_order.edit_versions.default_state_id существует
and utility_network.default_states.work_order_id == work_order.edit_versions.work_order_id
```

То есть `EditVersion` должен ссылаться не просто на любой `DefaultState`, а на
baseline того же `WorkOrder`.

`review_post`, audit actor refs и будущие package links не входят в первый
increment, пока соответствующих таблиц нет. Компонент должен быть устроен так,
чтобы новые checks добавлялись явным расширением registry.

## Архитектура

Предлагаемое расположение:

```text
apps/backend/utility_service/infrastructure/postgresql/consistency/
  __init__.py
  contracts/
    __init__.py
    check.py
    report.py
  cross_context_checker.py
  cross_context_checks.py
```

Компонент находится в `infrastructure/postgresql`, потому что проверки являются
SQL-level и schema-level probes. Они знают имена схем, таблиц и колонок.
В `use_cases` не нужно переносить SQL проверок: это не пользовательский
business flow, а operational data integrity диагностика.

Основные типы:

```python
contracts/check.py
  Severity
  CrossContextConsistencyCheck

contracts/report.py
  CrossContextConsistencyIssue
  CrossContextConsistencyReport

CrossContextConsistencyChecker
  принимает AsyncSession
  запускает набор registered checks
  возвращает CrossContextConsistencyReport
```

Dataclass-контракты живут в отдельной папке `consistency/contracts`,
чтобы `cross_context_checker.py` оставался runner-ом, а
`cross_context_checks.py` - registry SQL-проб. Это разделяет форму данных, SQL
registry и исполнение проверок.

Checker не импортирует `web_api`, не выполняет writes, не исправляет данные и не
решает HTTP/status/error code. Он возвращает факты. Если future use case
переиспользует targeted checks перед `post` или `submit_for_review`, именно use
case решает, как превратить issue в `WORK_ORDER_CONTEXT_INVALID` или будущий
`POST_CONTEXT_INVALID`.

Явные SQL probes предпочтительнее generic dynamic SQL builder в первом
increment. Они проще читаются, дают точные sample rows и позволяют выражать
доменные semantic checks, например принадлежность `DefaultState` тому же
`WorkOrder`.

## Набор Checks

Все checks первого increment имеют `severity="error"`. Поле `warning`
предусматривается в модели, но текущие нарушения означают поврежденное
operational state, а не мягкую рекомендацию.

### `work_order_assignee_user_exists`

Проверяет:

```text
work_order.work_orders.assignee_user_id -> "user".users.id
```

Нарушение означает, что `WorkOrder` назначен на пользователя, которого нет.
Service-level flow может позднее вернуть `not found` или скрыть это как
недоступный work order, но operational report должен показать именно orphan
assignee reference.

Sample rows:

```json
{
  "workOrderId": "...",
  "assigneeUserId": "..."
}
```

### `work_order_created_by_user_exists`

Проверяет:

```text
work_order.work_orders.created_by_user_id -> "user".users.id
```

Нарушение означает, что audit/process attribution у `WorkOrder` указывает на
несуществующего пользователя.

Sample rows:

```json
{
  "workOrderId": "...",
  "createdByUserId": "..."
}
```

### `default_state_work_order_exists`

Проверяет:

```text
utility_network.default_states.work_order_id -> work_order.work_orders.id
```

Нарушение означает, что baseline projection существует для отсутствующего
`WorkOrder`. Это может появиться после неудачной миграции, ручного SQL или
неполного repair path.

Sample rows:

```json
{
  "defaultStateId": "...",
  "workOrderId": "..."
}
```

### `edit_version_owner_user_exists`

Проверяет:

```text
work_order.edit_versions.owner_user_id -> "user".users.id
```

Нарушение означает, что рабочая версия принадлежит пользователю, которого нет.
Для обычного user flow это может проявиться поздно, а для review/post должно
быть видимой причиной блокировки.

Sample rows:

```json
{
  "editVersionId": "...",
  "ownerUserId": "..."
}
```

### `edit_version_default_state_exists`

Проверяет:

```text
work_order.edit_versions.default_state_id -> utility_network.default_states.id
```

Нарушение означает, что `EditVersion` потеряла baseline, от которого была
создана.

Sample rows:

```json
{
  "editVersionId": "...",
  "defaultStateId": "..."
}
```

### `edit_version_default_state_matches_work_order`

Проверяет semantic consistency:

```text
edit_versions.default_state_id exists
and default_states.work_order_id == edit_versions.work_order_id
```

Нарушение означает, что `EditVersion` ссылается на существующий `DefaultState`,
но этот `DefaultState` принадлежит другому `WorkOrder`. Простая existence check
такой дефект не поймает.

Sample rows:

```json
{
  "editVersionId": "...",
  "editVersionWorkOrderId": "...",
  "defaultStateId": "...",
  "defaultStateWorkOrderId": "..."
}
```

## Report Contract

Report:

```python
@dataclass(frozen=True)
class CrossContextConsistencyReport:
    ok: bool
    checked_at: datetime
    checks_run: int
    error_count: int
    warning_count: int
    issues: list[CrossContextConsistencyIssue]
```

Issue:

```python
@dataclass(frozen=True)
class CrossContextConsistencyIssue:
    check_name: str
    severity: Literal["error", "warning"]
    message: str
    source: str
    target: str | None
    count: int
    sample_rows: list[dict[str, Any]]
```

`error_count` и `warning_count` считаются по числу issues, а не по числу
нарушенных rows. Количество строк конкретного нарушения хранится в
`issue.count`.

Каждый check возвращает total count и ограниченный набор sample rows. Значение
`sample_limit` по умолчанию: 10. Полный список поврежденных UUID не нужен для
первого отчета; оператору достаточно total count и примеров, чтобы определить
класс поломки.

SQL probe может использовать `count(*) over ()`, чтобы одним запросом получить
total count и samples:

```sql
select
  count(*) over () as issue_count,
  wo.id as work_order_id,
  wo.assignee_user_id
from work_order.work_orders wo
left join "user".users u on u.id = wo.assignee_user_id
where u.id is null
limit :sample_limit
```

Если rows нет, issue не создается. Если rows есть, issue создается с `count` из
`issue_count`.

## Error Policy

Checker не бросает доменные exceptions для найденных нарушений данных.

```text
orphan UUID found -> report.ok = false
checker itself broken -> exception / failed test
```

Python exception допустим только для технической невозможности выполнить
проверку:

- database unavailable;
- SQL syntax/regression error;
- missing table/column after migration drift;
- unexpected row shape.

Это разделяет поврежденные данные и баг самого checker-а. Smoke должен красиво
сообщать, какие данные повреждены. CI должен падать как на дефекте кода, если
checker больше не может выполниться.

## Entrypoints

### Integration Test

Добавить:

```text
apps/backend/tests/integration_tests/test_cross_context_consistency.py
```

Тест запускает checker на real PostgreSQL/PostGIS test DB с `RUN_DB_TESTS=1` и
падает, если есть `severity="error"` issues. Он проверяет не конкретный `WO-001`,
а общий invariant: все cross-context UUID links в базе согласованы.

### CI Wiring

DB integration tests сейчас запускаются в `.github/workflows/ci.yml` внутри
compose step `PostgreSQL/PostGIS network model tests` по отдельному списку
файлов. Новый тест должен быть явно добавлен в этот список:

```text
docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml exec -T utility_service env RUN_DB_TESTS=1 \
  pytest tests/integration_tests/test_cross_context_consistency.py -q
```

Обычный backend job `docker run --rm --entrypoint bash utility_service:dev -lc
"pytest"` остается быстрым suite. DB consistency contract должен жить в
compose-интеграционном CI шаге, потому что он проверяет состояние после
migrations/seed.

### Smoke/Ops Runner

Добавить read-only runner:

```text
apps/backend/tests/smoke/cross_context_consistency_smoke.py
```

Он запускается внутри живого compose service и печатает человекочитаемый отчет.
При `error` issue возвращает exit code `1`, при clean report - `0`.

Пример failed output:

```text
Cross-context consistency: FAILED

ERROR edit_version_default_state_matches_work_order
count: 1
sample:
  editVersionId=...
  editVersionWorkOrderId=...
  defaultStateId=...
  defaultStateWorkOrderId=...
```

В первый increment этот runner может не добавляться отдельным CI step, если
integration test уже включен в CI. Он нужен для локальной и операционной
диагностики.

### Future Runtime Reuse

Public HTTP endpoint не добавляется. API checker-а должен позволять запускать
subset checks:

```python
await checker.run([
    "edit_version_default_state_exists",
    "edit_version_default_state_matches_work_order",
])
```

Это оставляет путь для future `submit_for_review`/`post` gates без дублирования
SQL. Use case должен сам маппить issue в доменный error.

## Testing Strategy

### Unit Tests

Добавить:

```text
apps/backend/utility_service/infrastructure/tests/test_cross_context_checker.py
```

Покрыть:

- пустой result превращается в `ok=True`;
- result с rows превращается в issue;
- `error_count` и `warning_count` считаются по issues;
- subset checks запускает только выбранные checks;
- неизвестное имя check дает понятную ошибку;
- sample rows преобразуются к stable human-readable keys.

Unit tests не требуют реальной БД: можно проверять сборку report из synthetic
rows или использовать fake executor для checker-а.

### Integration Tests

Добавить:

```text
apps/backend/tests/integration_tests/test_cross_context_consistency.py
```

Покрыть:

- после migrations/seed все checks проходят;
- искусственно созданный orphan `owner_user_id=uuid4()` ловится
  `edit_version_owner_user_exists`;
- искусственно созданный semantic mismatch, где
  `edit_version.default_state_id` указывает на `DefaultState` другого
  `WorkOrder`, ловится `edit_version_default_state_matches_work_order`.

Negative cases должны выполняться внутри rollback transaction, чтобы не ломать
общий compose state для последующих smoke шагов.

### Smoke Formatting Tests

Добавить:

```text
apps/backend/tests/smoke/test_cross_context_consistency_smoke.py
```

Проверить форматирование success/failed output и exit code `0/1` без live DB.

## Non-Goals

В первый increment не входит:

- добавление cross-schema FK;
- repair/fix команды;
- public HTTP endpoint;
- scheduler/cron;
- Prometheus metrics;
- автоматическое блокирование всех use cases;
- generic dynamic SQL DSL;
- checks для будущих `review_post` таблиц;
- изменение существующих service errors, кроме возможного future reuse;
- изменение доменной модели `WorkOrder`, `DefaultState` или `EditVersion`.

## Acceptance Criteria

1. `CrossContextConsistencyChecker` запускает утвержденный набор read-only SQL
   checks.
2. Integration test доказывает, что текущее migration/seed состояние
   консистентно.
3. Negative integration cases доказывают, что orphan UUID и semantic mismatch
   ловятся конкретными checks.
4. Новый integration test явно добавлен в compose-интеграционный CI step.
5. Smoke runner печатает понятный отчет и возвращает ненулевой exit code при
   `error` issue.
6. Metadata tests по-прежнему подтверждают отсутствие запрещенных cross-schema
   FK.
7. Документация явно говорит, что checker не заменяет service-level validations
   и не исправляет данные.

## Последствия Решения

Плюсы:

- plain UUID links остаются архитектурным решением, а не дырой наблюдаемости;
- CI ловит drift после migrations/seed/repair paths;
- будущий `review_post`/`post` gate сможет переиспользовать targeted checks;
- операционный отчет отличает обычный service-level `not found` от повреждения
  данных.

Минусы:

- появляется еще один инфраструктурный компонент и набор SQL probes;
- новые cross-context plain UUID поля требуют явного добавления checks;
- checker не предотвращает нарушение в момент записи, если соответствующий use
  case не делает runtime validation.

Принятое ограничение: prevention остается ответственностью service-level write
paths, а checker отвечает за диагностику и CI/ops visibility.
