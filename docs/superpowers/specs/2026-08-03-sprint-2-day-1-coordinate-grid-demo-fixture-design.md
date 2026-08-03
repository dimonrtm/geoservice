# Sprint 2 Day 1: координатная сетка и воспроизводимая demo fixture

Дата: 2026-08-03

## Назначение

Первый день Sprint 2 должен подготовить устойчивый фундамент для сценария
`edit -> save -> readback -> restart -> revert`: зафиксировать конфигурацию
координатной сетки, сделать `L-003` единственной structurally eligible line с
одной внутренней вершиной и безопасно обновить старые двухвершинные demo
snapshots без удаления всего PostgreSQL volume.

Итоговое решение заменяет исходное требование об обязательном automatic
`full-clean`. Старый demo volume обновляется через отдельный атомарный
demo-only fixture upgrade. Ручной `full-clean` остаётся fallback для состояния,
которое нельзя обновить безопасно, и для уже известных несовместимых старых
schema volumes.

## Контекст текущего кода

- `Settings` пока не содержит geometry resolution и rounding mode.
- `L-003` в `seed_utility_dataset_specs.py` является двухвершинной.
- Utility dataset и `WO-001` создаются по create-once/no-op контракту.
- Geometry `L-003` может существовать в трёх materialized слоях:
  `NetworkFeature`, `DefaultStateFeature` и `EditVersionFeature`.
- Обычный restart не обновляет существующие snapshots.
- До Sprint 2 legitimate persisted geometry edit отсутствует, но upgrade всё
  равно обязан защищать `EditVersionFeature` с `operation != unchanged`.

## Цели

1. Добавить `UTILITY_GEOMETRY_XY_RESOLUTION` с default
   `0.0000001` градуса.
2. Добавить `UTILITY_GEOMETRY_ROUNDING_MODE` с единственным поддерживаемым
   значением `ROUND_HALF_AWAY_FROM_ZERO`.
3. Представлять resolution через `Decimal` и отклонять любое не конечное или
   неположительное значение.
4. Сделать `L-003` трёхвершинной line с единственной внутренней вершиной
   `index=1`.
5. Сохранить counts `19 features / 9 associations` и существующий graph.
6. Обновлять старые двухвершинные materialized-копии `L-003` атомарно и
   идемпотентно, не удаляя весь demo volume.
7. Не добавлять demo seeds или fixture upgrade в production startup и не
   менять пользовательскую семантику create-once seeds. Geometry settings при
   этом остаются доступными production-контуру как обычная конфигурация.

## Вне scope

- geometry canonicalizer и поведенческие midpoint tests;
- Save/Revert API, optimistic token, command registry и change events;
- общий versioned seed framework;
- автоматический repair отсутствующих, неверно типизированных или
  четырёхвершинных fixture rows;
- automatic `full-clean`;
- production-like data migration.

## Конфигурационный контракт

### Типы и defaults

В `utility_service/utils/settings.py` добавляется строковый enum:

```python
class UtilityGeometryRoundingMode(str, enum.Enum):
    HALF_AWAY_FROM_ZERO = "ROUND_HALF_AWAY_FROM_ZERO"
```

`Settings` получает поля:

```python
utility_geometry_xy_resolution: Decimal = Field(
    Decimal("0.0000001"),
    gt=0,
    allow_inf_nan=False,
    alias="UTILITY_GEOMETRY_XY_RESOLUTION",
)
utility_geometry_rounding_mode: UtilityGeometryRoundingMode = Field(
    UtilityGeometryRoundingMode.HALF_AWAY_FROM_ZERO,
    alias="UTILITY_GEOMETRY_ROUNDING_MODE",
)
```

Resolution принимает любое конечное `Decimal > 0`, включая шаги, не
являющиеся степенями десяти, например `0.00000025`. Искусственная верхняя
граница не вводится. Значения `0`, отрицательные числа, `NaN`, `Infinity`,
пустая строка и нечисловой текст отклоняются при создании settings.

Rounding mode регистрозависим. Другие значения блокируют startup. В будущем
geometry canonicalizer явно сопоставит
`ROUND_HALF_AWAY_FROM_ZERO -> decimal.ROUND_HALF_UP`; динамическое открытие
произвольных констант модуля `decimal` не допускается.

### Docker Compose

`utility_service` получает переменные через базовый Compose environment:

```yaml
UTILITY_GEOMETRY_XY_RESOLUTION: ${UTILITY_GEOMETRY_XY_RESOLUTION:-0.0000001}
UTILITY_GEOMETRY_ROUNDING_MODE: ${UTILITY_GEOMETRY_ROUNDING_MODE:-ROUND_HALF_AWAY_FROM_ZERO}
```

`infra/demo.env` фиксирует те же значения явно. Это делает demo-конфигурацию
видимой, сохраняя безопасные defaults внутри приложения.

## Demo fixture `L-003`

### Геометрия

Seed geometry меняется с:

```text
LINESTRING (65.520 44.820, 65.530 44.820)
```

на:

```text
LINESTRING (65.520 44.820, 65.525 44.8205, 65.530 44.820)
```

Стабильными остаются UUID, `assetCode=L-003`, `FeatureType.LINE`, имя,
описание, properties, endpoints и associations `D-002 -> L-003` и
`D-003 -> L-003`.

Внутренняя вершина `[65.525, 44.8205]`:

- имеет index `1`;
- лежит внутри AOI `WO-001`;
- не совпадает ни с junction, ни с device;
- лежит на default grid `0.0000001`;
- сохраняет line valid, simple и non-empty.

### Structural eligibility

Специальный `geometryEditable` property и hardcode по `assetCode` в рабочей
логике не вводятся. Line пригодна для текущего сценария, если:

```text
featureType == LINE
geometry.type == LineString
coordinates.length == 3
```

В fresh fixture этому условию соответствует ровно одна feature — `L-003`.
Остальные пять lines остаются двухвершинными.

## Transactional demo fixture upgrade

### Граница ответственности

Upgrade реализуется отдельно от create-once services:

```text
DemoFixtureUpgradeRepository
  -> блокировка, чтение и обновление materialized-копий

DemoFixtureUpgradeService
  -> полная проверка и расчёт target geometries

upgrade_demo_fixture runner
  -> startup entry point и диагностический результат
```

Планируемые файлы:

```text
apps/backend/seeds/repositories/demo_fixture_upgrade_repository.py
apps/backend/seeds/services/demo_fixture_upgrade_service.py
apps/backend/seeds/runners/upgrade_demo_fixture.py
```

`SeedUtilityDatasetService` и `SeedWorkOrderService` сохраняют текущую
create-once/no-op семантику. Upgrade является отдельным demo-only
startup-maintenance исключением.

### Порядок startup

`apps/backend/scripts/start_utility_service.sh` выполняет:

```text
alembic upgrade head
-> seed_demo_users
-> seed_utility_dataset
-> seed_work_orders
-> upgrade_demo_fixture
-> uvicorn
```

Upgrade расположен после seeds. На fresh DB seeds сразу создают правильные
трёхвершинные copies, и upgrade становится no-op. На старом volume create-once
seeds сохраняют существующие rows, после чего upgrade приводит только
двухвершинные copies к новой структуре.

`infra/dev-up.cmd` не получает host Python dependency и не выполняет
automatic `down -v`.

### Чтение и блокировка

В одной transaction строки блокируются в стабильном порядке:

1. `L-003` из `synthetic_utility_feeder_01` в
   `utility_network.network_features`.
2. `L-003` из `WO-001 DefaultState` в
   `utility_network.default_state_features`.
3. `L-003` из всех существующих `WO-001 EditVersion` в
   `work_order.edit_version_features`.

Repository возвращает source, owner id, geometry, geometry type,
`network_version` и, для edit copy, `default_state_id` и `operation`.

### Расчёт target geometry

Расчёт идёт по lineage `Feeder -> DefaultState -> EditVersion`.

Для feeder:

- две вершины — использовать точную новую seed geometry;
- три вершины — сохранить существующую geometry независимо от coordinates;
- четыре и более вершины или неверный type — ошибка.

Для DefaultState:

- две вершины — скопировать рассчитанную geometry feeder;
- три вершины — сохранить существующую geometry независимо от coordinates;
- четыре и более вершины или неверный type — ошибка.

Для EditVersion:

- `default_state_id` обязан совпадать с `WO-001 DefaultState.id`, иначе hierarchy invalid;
- две вершины и `operation=unchanged` — скопировать рассчитанную geometry
  соответствующего DefaultState;
- две вершины и `operation != unchanged` — unsafe state, ошибка;
- три вершины — сохранить существующую geometry независимо от coordinates;
- четыре и более вершины или неверный type — ошибка.

Таким образом, существующие трёхвершинные ручные coordinates не
перезаписываются, а stale downstream copy наследует geometry своего
непосредственного baseline.

### Полнота и атомарность

После обычных seeds существующий feeder без `L-003`, существующий
`DefaultState` без `L-003` или существующий `EditVersion` без `L-003`
считаются invalid. Upgrade не восстанавливает отсутствующие rows, counts или
associations.

Service применяет принцип `validate first, mutate second`:

```text
BEGIN
SELECT ... FOR UPDATE
validate complete hierarchy
calculate all target geometries
update only stale two-vertex copies
COMMIT
```

Любая ошибка приводит к rollback всей transaction и блокирует запуск API.
Частичное состояние `3/2/2` после неуспешного upgrade недопустимо.

### Version и audit semantics

Upgrade считается заменой устаревшей demo fixture, а не пользовательским
geometry edit:

- UUID, properties и associations не меняются;
- `network_version` сохраняется;
- `EditVersionFeature.operation` остаётся `unchanged`;
- `NetworkState.current_revision` не увеличивается;
- change event и user audit event не создаются;
- `updated_at` изменяется только как технический след изменённой строки;
- операция завершается до открытия API пользователям.

`DefaultState` остаётся immutable для пользовательских use cases. Этот
fixture upgrade является узким startup-maintenance исключением.

### Идемпотентность и диагностика

Первый запуск старого volume обновляет все безопасные двухвершинные copies.
Повторный запуск не выполняет updates. Result содержит число и источники
изменённых rows, а runner пишет понятный log без удаления данных.

Ручной demo-only `full-clean` предлагается только как fallback для unsafe или
invalid состояния. Автоматическое удаление volume отсутствует.

## Обработка ошибок

Startup блокируется с rollback, если:

- двухвершинная edit copy уже имеет `operation != unchanged`;
- `EditVersion.default_state_id` не совпадает с рассчитанным DefaultState;
- какая-либо обязательная copy отсутствует внутри существующего aggregate;
- geometry type не является `LineString`;
- copy имеет четыре или больше vertices;
- чтение, блокировка или update завершаются технической ошибкой.

Ошибка должна перечислять source и owner id проблемной copy и объяснять, что
автоматический repair не выполнен. Данные сохраняются. Для disposable demo DB
пользователь может осознанно применить документированную команду ручного
`full-clean`.

## Тестовый контракт

### Settings

`utility_service/utils/tests/test_settings.py` проверяет defaults, env aliases,
произвольный положительный finite resolution, отклонение zero/negative/
non-finite/non-numeric values, строгий rounding mode и неверный регистр.

### Seed specification

`seeds/tests/test_seed_utility_dataset_specs.py` с помощью `shapely.wkt.loads`
проверяет:

- counts `19/9` и breakdown `7/6/6`;
- ровно одну трёхвершинную line и её `assetCode=L-003`;
- точные coordinates, endpoints и внутреннюю вершину;
- совпадение endpoints с `J-003`/`J-004`;
- отсутствие совпадения внутренней вершины с point features;
- AOI coverage, valid/simple/non-empty geometry;
- неизменность association graph;
- двухвершинность остальных пяти lines.

### Upgrade service

Unit tests покрывают:

- no-op для полностью трёхвершинной hierarchy;
- обновление feeder из seed geometry;
- наследование geometry feeder двухвершинным DefaultState;
- наследование geometry DefaultState двухвершинным unchanged EditVersion;
- mixed `2/3/2` и `3/2/2` states;
- сохранение разных существующих `3A/3B/3C` geometries;
- rollback при `2 vertices + operation != unchanged`;
- rollback при missing copy, wrong type или `4+` vertices;
- отсутствие repository updates до завершения полной validation;
- точный result и идемпотентный повторный запуск.

Repository integration test на PostgreSQL/PostGIS проверяет фактическое
обновление трёх таблиц, неизменность ids/properties/versions/operation/counts/
associations, повторный no-op и полный rollback unsafe case. Тест не удаляет
Docker volume.

### Startup contract

`tests/test_compose_startup_contract.py` фиксирует порядок seeds, fixture
upgrade и `uvicorn`. Production `start_api.sh` не должен содержать demo seeds
или fixture upgrade. `dev-up.cmd` не должен выполнять automatic `down -v` для
обновления fixture.

## Документация

Реализация должна синхронно обновить:

- `README.md` — automatic in-place upgrade и manual fallback;
- `infra/demo.env` — явные geometry settings;
- `docs/sprint_2/2026-07-31-sprint-2-technical-requirements.md` — заменить
  обязательный automatic `full-clean` на transactional upgrade;
- `docs/sprint_2/2026-07-31-sprint-2-calendar-plan.md` — обновить результат и
  проверки дня 1;
- risk table — unsafe state блокирует startup, ручной `full-clean` остаётся
  fallback.

Существующее предупреждение о пересоздании несовместимых старых schema
volumes сохраняется: оно относится к production-like migration baseline, а не
к обновлению `L-003`.

## Критерии готовности

- Defaults равны `0.0000001` и `ROUND_HALF_AWAY_FROM_ZERO`.
- Invalid geometry settings блокируют startup.
- Fresh demo environment создаёт ровно 19 features и 9 associations.
- Fresh `L-003` имеет три coordinates и единственную внутреннюю вершину.
- Только `L-003` structurally eligible среди demo lines.
- Все безопасные двухвершинные materialized copies обновляются одной
  transaction.
- Существующие трёхвершинные coordinates сохраняются.
- Unsafe changed EditVersion блокирует startup и не допускает partial update.
- Повторный startup является no-op.
- Automatic `down -v` отсутствует.
- Production startup принимает geometry settings, но не запускает demo seeds
  или fixture upgrade.
- Settings, seed specification, upgrade service, repository integration и
  startup contract tests проходят.

## Планируемые затронутые области

- `apps/backend/utility_service/utils/settings.py`
- `apps/backend/utility_service/utils/tests/test_settings.py`
- `apps/backend/seeds/specs/seed_utility_dataset_specs.py`
- `apps/backend/seeds/tests/test_seed_utility_dataset_specs.py`
- новые repository/service/runner и их tests для fixture upgrade
- `apps/backend/scripts/start_utility_service.sh`
- `apps/backend/tests/test_compose_startup_contract.py`
- `infra/docker-compose.yml`
- `infra/demo.env`
- `README.md`
- документы Sprint 2, перечисленные выше
