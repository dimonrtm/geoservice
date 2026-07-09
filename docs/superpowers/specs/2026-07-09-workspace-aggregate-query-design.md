# Оптимизация Workspace Aggregate Query

Дата: 2026-07-09
Статус: утвержден пользователем для written spec
Расположение: `docs/superpowers/specs`

## Назначение

`GET /api/v1/work-orders/{workOrderId}/edit-versions/{editVersionId}/workspace`
должен сохранить текущий публичный контракт, но подготовить read path к будущему
росту dataset. Сейчас `WorkOrderRepository.get_workspace_aggregate()` собирает
workspace через SQLAlchemy expression builder: features фильтруются по
`WorkOrder.scope.aoi`, а associations попадают в ответ только если оба endpoint
feature входят в workspace.

Проблема не проявляется на текущем seed dataset из 19 features и 9 associations.
Оптимизация нужна заранее, пока изменение можно сделать без смены API,
frontend-flow и доменной модели.

## Выбранный Подход

Вынести workspace aggregate query в отдельный raw SQL файл:

```text
apps/backend/utility_service/infrastructure/postgresql/sql/workspace_aggregate.sql
```

Запрос должен использовать CTE:

1. `workspace_context` находит `WorkOrder`, `EditVersion` и `AOI` по
   `work_order_id` / `edit_version_id`.
2. `workspace_features AS MATERIALIZED` один раз выбирает features текущей
   edit version, которые пересекают AOI через `ST_Intersects`.
3. `features_json` собирает features в тот же JSONB shape, который сейчас
   ожидает `WorkspaceService`.
4. `associations_json` выбирает associations текущей edit version только через
   join к `workspace_features` для `from_feature_id` и `to_feature_id`.
5. Финальный `SELECT` возвращает `WorkOrder`, `EditVersion`, AOI geometry,
   AOI extent, `features_data` и `associations_data`.

`WorkOrderRepository.get_workspace_aggregate()` остается публичной repository
границей для чтения workspace, но внутри использует `text(...).columns(...)` по
аналогии с `DefaultStateRepository` и
`infrastructure/postgresql/sql/default_state_aggregate.sql`.

## Почему Не Менять API

Текущая цель - оптимизировать внутреннюю форму чтения, а не менять продуктовый
контракт. Endpoint продолжает возвращать полный workspace aggregate одним DB
round trip. Frontend, DTO `schemas.workspace`, smoke path
`login -> assigned-to-me -> open/reopen EditVersion -> workspace` и доменное
правило "AOI является серверной границей workspace" не меняются.

Если будущий dataset вырастет до десятков тысяч features в одном AOI и узким
местом станет payload/rendering, отдельный workspace-specific bbox/tile/page API
будет следующим архитектурным решением. Этот spec сознательно не вводит такой
API, потому что текущий рост пока ожидаемый, а не фактический.

## Компоненты

`workspace_aggregate.sql` отвечает только за SQL shape и фильтрацию workspace
membership. Он не должен содержать authorization rules: actor, role, assignee,
status и structured errors остаются в `WorkspaceService`.

Существующие индексы остаются частью текущей схемы: `ix_aois_geometry` для
`work_order.aois`, `ix_network_features_geometry` для authoritative network
features, lookup indexes на `work_order.work_orders` и
`uq_edit_versions_open_work_order` для одной open version. Этот refactor не
утверждает, что индексов нет.

В scope также входит небольшой index hardening для working-copy таблиц:

- `ix_edit_version_features_geometry` как явный GiST index на
  `work_order.edit_version_features.geometry`;
- `ix_edit_version_associations_edit_version_to_feature_id` как lookup index на
  `work_order.edit_version_associations(edit_version_id, to_feature_id)`.

Первый индекс поддерживает AOI membership check внутри workspace copy. Второй
закрывает второй endpoint association join: существующий unique directed-edge
constraint начинается с `(edit_version_id, from_feature_id, ...)`, но не является
эквивалентной lookup-границей для `to_feature_id`.

`WorkOrderRepository` добавляет module-level SQLAlchemy statement:

```text
WORKSPACE_AGGREGATE_SQL = text(...).columns(...)
```

Repository преобразует row в существующий `WorkspaceAggregateRow` и
`WorkspaceAoiRow`. Dataclass shape можно сохранить без изменения публичного
use-case слоя.

`WorkspaceService.workspace_from_aggregate()` не должен меняться, кроме случая,
если raw SQL вернет scalar enum values вместо Python enum objects. В таком
случае нормализация должна остаться локальной и не менять response contract.

## Data Flow

1. `WorkspaceService.get_workspace()` проверяет actor через `UserRepository`.
2. Service вызывает `WorkOrderRepository.get_workspace_aggregate()`.
3. Repository выполняет один raw SQL statement с параметрами `work_order_id` и
   `edit_version_id`.
4. SQL один раз материализует `workspace_features`.
5. Features JSON строится из materialized set.
6. Associations JSON строится через два join к тому же materialized set.
7. Service проверяет assignee/status и собирает `WorkspaceOut`.

Такой flow убирает повторное вычисление AOI membership для associations и делает
запрос удобным для `EXPLAIN (ANALYZE, BUFFERS)`.

## Error Handling

Если пара `work_order_id` / `edit_version_id` не найдена, repository возвращает
`None`, а `WorkspaceService` сохраняет текущий `404 EDIT_VERSION_NOT_FOUND`.

Если workspace context поврежден и SQL вернул данные, которые нельзя
преобразовать в DTO, `WorkspaceService` сохраняет текущий
`422 WORKSPACE_CONTEXT_INVALID`.

Если SQL возвращает пустые features или associations, это валидный workspace
slice: `features_data` и `associations_data` должны быть `[]`, а не `null`.

## Testing

Обязательные проверки:

- metadata tests подтверждают ровно один GiST index на
  `EditVersionFeature.geometry` и lookup index на
  `EditVersionAssociation(edit_version_id, to_feature_id)`;
- migration contract `test_edit_version_migration.py` требует эти index names
  после upgrade;
- существующий integration test
  `test_seed_chain_workspace_aggregate_returns_work_order_scope` остается
  зеленым и подтверждает 19 features / 9 associations для seeded workspace;
- новый regression test подтверждает association filtering: association не
  попадает в workspace, если хотя бы один endpoint feature не входит в AOI;
- repository test или integration assertion подтверждает, что raw SQL возвращает
  тот же shape: `work_order`, `edit_version`, AOI geometry/extent,
  `features_data`, `associations_data`;
- smoke runner `tests/smoke/full_path_workspace_smoke.py` не требует изменений.

Желательная проверка после реализации:

```text
EXPLAIN (ANALYZE, BUFFERS)
```

для нового `workspace_aggregate.sql` на seeded dataset и, при появлении larger
fixture, на увеличенном workspace. Результат benchmark не входит в этот scope,
потому что роста dataset сейчас еще нет.

## Out Of Scope

Не входит в scope:

- изменение public API `GET .../workspace`;
- изменение frontend;
- workspace paging, bbox API, vector tiles или tile cache;
- изменение доменной модели `WorkOrder`, `EditVersion`, `AOI`;
- реализация benchmark harness для больших synthetic datasets.

Иные дополнительные индексы для edit-version working-copy таблиц следует
добавлять отдельным решением после измерений или после появления реального
larger fixture. Не нужно расширять schema дальше только из-за новой формы SQL.

## Последствия

Workspace read path становится более явным и ближе к существующему паттерну
`DefaultStateRepository`: сложный aggregate SQL хранится в `sql/*.sql`, а Python
repository отвечает за параметры и shape результата.

Решение снижает будущий риск повторного spatial membership вычисления, сохраняя
текущую простоту продукта: один endpoint, один DB round trip, тот же DTO contract.

## Проверка Spec

Документ не требует изменения API или frontend. Scope достаточно мал для одного
implementation plan: добавить raw SQL файл, подключить его в repository,
сохранить DTO shape, добавить два working-copy index contracts и закрепить
association filtering regression test. В документе нет незаполненных разделов;
будущие дополнительные индексы и bbox/tile API явно отнесены к out-of-scope.
