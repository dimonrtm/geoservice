# Техническое задание Sprint 2: первое сохранение геометрии

## 1. Назначение

Сейчас workspace позволяет открыть `WorkOrder` и посмотреть сеть, но не даёт пройти полный путь редактирования. Sprint 2 должен добавить первый законченный пользовательский сценарий: Editor меняет геометрию существующей линии, сохраняет её в `EditVersion`, видит то же изменение после обновления страницы и перезапуска backend, а затем возвращает линию к исходному состоянию.

Это ТЗ описывает ожидаемое поведение системы. Оно не предписывает структуру каждого метода и не является журналом выполнения работ.

## 2. Ожидаемый результат

В demo environment пользователь `alexey.editor@example.local`:

1. Открывает `WO-001`.
2. Выбирает существующую line feature `L-003`.
3. Перемещает её единственную внутреннюю вершину.
4. Нажимает Save и получает подтверждение сохранения.
5. Обновляет страницу и видит сохранённую геометрию.
6. Перезапускает backend и снова видит ту же геометрию.
7. Нажимает Revert и возвращает линию к immutable baseline.

Сценарий считается полноценным только при наличии UI, durable persistence, защиты от повторных запросов и автоматических проверок.

## 3. Границы работ

### Входит в Sprint 2

- редактирование одной существующей line feature;
- перемещение одной внутренней shape vertex;
- synchronous Save;
- durable readback после refresh и backend restart;
- Cancel локального несохранённого изменения;
- Revert сохранённого изменения к baseline;
- optimistic concurrency через `DraftVersionToken`;
- idempotency через `CommandId`;
- durable command registry;
- append-only history фактических изменений;
- базовая structural/spatial validation;
- полноценный UI-demo.

### Не входит в Sprint 2

- редактирование attributes и associations;
- изменение endpoints;
- добавление или удаление вершин;
- одновременное изменение нескольких вершин или features;
- split, merge и generic drawing framework;
- topology validation и электрические расчёты;
- reconcile, conflicts, review и post;
- подтверждение positional accuracy;
- async operations и polling;
- realtime broadcast изменений;
- UI истории команд и долгосрочная retention automation.

## 4. Основные понятия

### Baseline

Исходная геометрия берётся из `utility_network.default_state_features`. Она является authoritative и не изменяется при Save или Revert.

### Current snapshot

Текущее состояние draft хранится в `work_order.edit_version_features`. Это существующая модель, поэтому отдельная копия baseline geometry в ней не создаётся.

### DraftVersionToken

Внутри `EditVersion` хранится положительный `BIGINT draft_revision` со стартовым значением `1`. В API он передаётся строкой `draftVersionToken` и считается opaque: frontend не вычисляет и не изменяет его самостоятельно.

Content-changing Save и Revert увеличивают revision на `1`. No-op и повтор уже выполненной команды revision не меняют.

### CommandId

Каждая попытка логического Save или Revert получает глобально уникальный UUID `commandId`.

- Повтор того же `commandId` с тем же содержимым возвращает сохранённый terminal result и не выполняет mutation второй раз.
- Тот же `commandId` с другим содержимым отклоняется как `COMMAND_ID_REUSED`.
- После неопределённого сетевого исхода frontend повторяет запрос с прежним `commandId`.
- После исправления данных пользователем frontend создаёт новый `commandId`.

## 5. Demo data

Для сценария используется `L-003`:

```text
Baseline: LINESTRING (65.520 44.820, 65.525 44.8205, 65.530 44.820)
Moved:    LINESTRING (65.520 44.820, 65.525 44.8215, 65.530 44.820)
Vertex:   index 1
```

Внутренняя координата:

- находится внутри AOI `WO-001`;
- не совпадает с junction или device;
- не меняет общее количество demo features и associations: 19 и 9 соответственно.

Seed остаётся create-once. После user, utility dataset и work order seeds demo
startup запускает отдельный transactional fixture upgrade. Он рассчитывает target
geometry по lineage `Feeder -> DefaultState -> EditVersion`:

- двухвершинный feeder получает точную seed geometry `L-003`, трёхвершинный сохраняется;
- двухвершинный `DefaultStateFeature` получает рассчитанную feeder geometry, трёхвершинный сохраняется;
- двухвершинный `EditVersionFeature` с `operation=unchanged` получает рассчитанную default geometry, трёхвершинный сохраняется независимо от coordinates;
- несовпадающий `EditVersion.default_state_id`, двухвершинный edit с `operation != unchanged`, missing copy, неверный geometry type или `4+` vertices блокируют startup.

Сначала валидируется вся существующая hierarchy, затем geometry-only updates
выполняются одной transaction. UUID, properties, associations,
`version/network_version`, operation и `NetworkState.current_revision` не меняются.
Fresh fixture и повторный startup являются no-op.

Destructive demo-only `full-clean` остаётся ручным fallback для unsafe/invalid
fixture или несовместимого disposable volume:

```powershell
Set-Location infra
docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml down -v
```

Команда удаляет локальные demo data. Её нельзя применять к production-like данным,
и она не выполняется автоматически.

## 6. Правила редактирования геометрии

1. SRID остаётся `4326`.
2. Storage grid настраивается через `UTILITY_GEOMETRY_XY_RESOLUTION`.
3. Универсальное default-значение — `0.0000001` градуса.
4. Режим округления — `ROUND_HALF_AWAY_FROM_ZERO`; Python-реализация использует `Decimal` и `ROUND_HALF_UP`.
5. Клиент передаёт полную GeoJSON `LineString`, а server возвращает canonical geometry.
6. Количество частей и координат не меняется.
7. Обе endpoint coordinates остаются без изменений.
8. Отличаться может ровно одна внутренняя вершина.
9. Линия не должна быть empty, collapsed, invalid или non-simple.
10. Результирующая линия должна полностью покрываться AOI.
11. Если в `EditVersion` уже изменена другая feature, новая feature не сохраняется.
12. Отсутствие утверждённой positional specification возвращает `POSITIONAL_ACCURACY_UNVERIFIED`, но не блокирует технический Save.

Storage grid является правилом детерминированного хранения, а не допуском positional accuracy.
При resolution `0.0000001` точные midpoint округляются от нуля:
`+0.00000015 -> +0.0000002`, `-0.00000015 -> -0.0000002`.
Day 1 фиксирует configuration contract; canonicalization algorithm реализуется на
следующем этапе.

## 7. Сохранение и транзакционность

Save остаётся одной synchronous database transaction.

В рамках транзакции система:

1. Находит доступный пользователю `WorkOrder` и `EditVersion`.
2. Блокирует `EditVersion` от конкурирующих Save.
3. Проверяет lifecycle, assignment и `draftVersionToken`.
4. Резервирует `commandId` или возвращает ранее сохранённый terminal result.
5. Читает current feature, baseline и AOI.
6. Канонизирует и проверяет geometry.
7. Обновляет current snapshot и operation.
8. Увеличивает revision только при фактическом изменении.
9. Записывает append-only change event только при фактическом изменении.
10. Сохраняет точный successful или rejected terminal result.
11. Commit делает результат видимым целиком.

Частично сохранённого состояния быть не должно. Revert использует тот же механизм Save, но передаёт baseline geometry.

## 8. Хранение команд и событий

### `work_order.edit_version_commands`

Registry хранит:

- `command_id`;
- `edit_version_id` и `feature_id`;
- actor;
- request fingerprint;
- state `running|succeeded|rejected`;
- точный response payload либо rejection status/code/message;
- время создания и завершения.

### `work_order.edit_version_change_events`

Append-only history хранит:

- ссылку на `EditVersion` и `CommandId`;
- event type `change_set_persisted|change_set_cleared`;
- feature и actor;
- before/after geometry;
- base network revision;
- draft revision до и после изменения;
- время события.

Для одного `CommandId` создаётся не более одного change event. No-op и idempotent retry нового события не создают.

## 9. API сохранения

### Endpoint

```http
PUT /api/v1/work-orders/{workOrderId}/edit-versions/{editVersionId}/features/{featureId}/geometry
```

### Request

```json
{
  "commandId": "2cf0b2ec-d963-49c2-98a1-44efb5d305f7",
  "draftVersionToken": "1",
  "geometry": {
    "type": "LineString",
    "coordinates": [
      [65.52, 44.82],
      [65.525, 44.8215],
      [65.53, 44.82]
    ]
  }
}
```

Request не принимает неизвестные поля. `commandId` должен быть UUID, `draftVersionToken` — непустой строкой, `geometry` — GeoJSON `LineString`.

### Successful response

```json
{
  "commandId": "2cf0b2ec-d963-49c2-98a1-44efb5d305f7",
  "commandState": "succeeded",
  "draftVersionToken": "2",
  "operation": "updated",
  "hasPersistedChangeSet": true,
  "updatedFeature": {
    "id": "L-003 feature UUID",
    "geometry": {
      "type": "LineString",
      "coordinates": [
        [65.52, 44.82],
        [65.525, 44.8215],
        [65.53, 44.82]
      ]
    }
  },
  "basicValidation": {
    "geometryStatus": "passed",
    "aoiStatus": "passed",
    "positionalAccuracyStatus": "POSITIONAL_ACCURACY_UNVERIFIED",
    "dirtyRelativeToBaseline": "passed"
  }
}
```

UI всегда заменяет local draft на `updatedFeature` из response, потому что canonical server geometry имеет приоритет.

## 10. Workspace readback

Workspace response дополнительно возвращает:

- `draftVersionToken`;
- `hasPersistedChangeSet`;
- `basicValidation`;
- optional `changeSet`.

Если изменение сохранено, `changeSet` содержит:

- `featureId`;
- `vertexIndex`;
- `baselineGeometry`;
- `operation`.

Baseline geometry приходит с backend. Frontend не хранит seed coordinates в коде и не пытается восстановить baseline самостоятельно.

Если изменение отсутствует:

```json
{
  "draftVersionToken": "1",
  "hasPersistedChangeSet": false,
  "basicValidation": null,
  "changeSet": null
}
```

Readback должен возвращать одинаковый current snapshot после нового HTTP session, browser refresh и backend restart.

## 11. Ошибки

Все application errors используют строгую форму:

```json
{
  "code": "DRAFT_VERSION_STALE",
  "message": "Человекочитаемое сообщение",
  "correlationId": "correlation UUID"
}
```

Дополнительные поля в error body не добавляются.

| HTTP | Code | Когда возвращается | Что делает UI |
| --- | --- | --- | --- |
| 404 | `EDIT_VERSION_NOT_FOUND` | Work order, version или feature не видны Editor | Показывает отсутствие доступного объекта |
| 409 | `DRAFT_VERSION_STALE` | Token устарел | Перечитывает workspace, не повторяет Save автоматически |
| 409 | `COMMAND_ID_REUSED` | CommandId использован с другим содержимым | Останавливает retry и предлагает новую пользовательскую попытку |
| 409 | `MULTIPLE_FEATURE_CHANGE_NOT_ALLOWED` | Уже изменена другая feature | Объясняет ограничение текущего спринта |
| 409 | `SAVE_CONTEXT_CLOSED` | Lifecycle запрещает Save | Блокирует редактирование |
| 422 | `FEATURE_NOT_EDITABLE` | Feature не является eligible existing line | Снимает режим редактирования |
| 422 | `GEOMETRY_STRUCTURE_CHANGED` | Изменены endpoints, parts, vertex count или больше одной вершины | Возвращает пользователя к допустимой геометрии |
| 422 | `GEOMETRY_INVALID` | Линия empty, collapsed, invalid или non-simple | Оставляет draft для исправления |
| 422 | `GEOMETRY_OUTSIDE_AOI` | Линия не покрывается AOI | Оставляет draft для исправления |

Ошибки валидации request до входа в use case не резервируют `CommandId`. Domain rejection после входа в use case сохраняется как terminal `rejected` result.

## 12. Требования к UI

### Выбор и редактирование

- В workspace можно выбрать eligible line.
- Для `L-003` показывается один draggable handle на внутренней вершине.
- Endpoints не получают draggable handles.
- Drag меняет только local draft до нажатия Save.
- Новые frontend dependencies не добавляются; используется MapLibre `Marker`.

### Save

- Кнопка активна только при допустимом local change.
- Во время запроса повторное нажатие блокируется.
- После успеха UI показывает canonical geometry и новый token.
- Неопределённый сетевой исход сохраняется в `sessionStorage` и может быть повторён с тем же `CommandId`.

### Cancel

- Отменяет только несохранённый local draft.
- Не вызывает backend.
- Возвращает карту к последнему current snapshot.

### Revert

- Доступен только при `hasPersistedChangeSet=true`.
- Использует `baselineGeometry` из workspace readback.
- Отправляется как новая команда с новым `CommandId` и текущим token.
- После успеха operation становится `unchanged`, а `hasPersistedChangeSet` — `false`.

### Состояния и доступность

- UI показывает dirty, saving, saved, stale и rejected states.
- `POSITIONAL_ACCURACY_UNVERIFIED` отображается как известное ограничение, а не как успешная positional validation.
- Управление доступно с клавиатуры; controls имеют понятные labels и disabled states.
- Основной сценарий работает в desktop layout; на узком экране controls остаются доступными без перекрытия карты.

## 13. Затрагиваемые области проекта

ТЗ не требует общей перестройки архитектуры. Изменения ограничены следующими областями:

| Область | Что меняется |
| --- | --- |
| Backend settings | Настройки координатной сетки и режима округления |
| Demo seeds | Трёхвершинная `L-003`, transactional in-place fixture upgrade и проверки воспроизводимости |
| PostgreSQL/PostGIS | `draft_revision`, command registry, change events, spatial checks и migration |
| Domain/use cases | Команда Save/Revert, optimistic concurrency, idempotency и validation summary |
| API/workspace readback | Новый `PUT` contract и baseline-aware projection для восстановления после restart |
| Frontend | TypeScript contracts, API client, Pinia state, MapLibre marker и Save/Cancel/Revert controls |
| Tests/CI | Unit, migration, integration, API, frontend и restart smoke matrix |
| Документация | Календарный план, это ТЗ и итоговый acceptance report в `docs/sprint_2/` |

В доменной модели `EditVersion` остаётся владельцем current draft и получает revision token. `DefaultStateFeature` остаётся immutable baseline. Command registry хранит идемпотентный результат команды, а change event history — доказательство фактического изменения. Новые bounded contexts или aggregates в этом спринте не вводятся.

## 14. Критерии приёмки

### AC-01. Настраиваемая сетка

Default resolution равен `0.0000001`, invalid/zero value блокирует startup, положительные и отрицательные midpoint округляются одинаково.

### AC-02. Demo fixture

На fresh volume и после automatic upgrade совместимого старого volume линия
`L-003` имеет три coordinates, внутренняя вершина пригодна для drag, counts
остаются 19 features и 9 associations. Unsafe state блокирует startup без partial
writes; manual `full-clean` не является штатным требованием.

### AC-03. Успешный Save

Editor перемещает vertex index `1`, Save возвращает canonical geometry, operation `updated` и следующий token.

### AC-04. Атомарность

При любой ошибке current snapshot, revision, event history и terminal result остаются согласованными; `DefaultStateFeature` не меняется.

### AC-05. Идемпотентность

Повтор одинаковой команды возвращает тот же результат, не увеличивает revision и не создаёт второе событие. Повтор `CommandId` с другим fingerprint возвращает `COMMAND_ID_REUSED`.

### AC-06. Конкурентное изменение

Save со старым token возвращает `DRAFT_VERSION_STALE`. UI перечитывает workspace и не отправляет изменение автоматически.

### AC-07. Проверка геометрии

Изменение endpoint, количества vertices, двух вершин, invalid/non-simple geometry или выход за AOI отклоняется отдельным documented code.

### AC-08. Durable readback

Сохранённая geometry, token, validation и baseline change set совпадают после refresh, новой HTTP session и backend restart.

### AC-09. Cancel и Revert

Cancel снимает только local draft. Revert после restart возвращает baseline, меняет operation на `unchanged` и сохраняет отдельное change-set-cleared event.

### AC-10. Полноценный UI-demo

Ручной сценарий `open -> select -> drag -> save -> refresh -> restart -> readback -> revert` проходит без прямого обращения к БД или developer tools.

## 15. Definition of Done

Sprint 2 готов к приёмке, когда одновременно выполнены все условия:

- AC-01–AC-10 подтверждены;
- backend format/lint/tests проходят;
- settings, seed specification, fixture upgrade idempotency/rollback и startup-order tests проходят;
- frontend format/lint/typecheck/tests/build проходят;
- migration проходит upgrade/downgrade/upgrade;
- DB/API smoke проходит на fresh demo database;
- restart readback подтверждён автоматической и ручной проверкой;
- исходный `DefaultStateFeature` доказуемо не изменился;
- `POSITIONAL_ACCURACY_UNVERIFIED` не представлен как verified;
- acceptance report создан в `docs/sprint_2/`;
- изменения оставлены unstaged для проверки пользователем;
- `git add`, `git commit` и `git push` не выполнялись.

## 16. Риски и допустимые fallback

| Риск | Основная защита | Допустимый fallback |
| --- | --- | --- |
| Старый volume скрывает новую fixture | Atomic validate-first fixture upgrade после seed chain | Demo startup останавливается с rollback; manual `full-clean` разрешён только для disposable fallback |
| Degree grid принимают за positional tolerance | Раздельные названия и `POSITIONAL_ACCURACY_UNVERIFIED` | Не добавлять выдуманный допуск в метрах |
| Retry создаёт повторное изменение | Global `CommandId` и сохранённый terminal result | Сериализовать Save на locked `EditVersion` |
| Revert после restart теряет baseline | Baseline приходит в workspace `changeSet` | Добавить отдельный read-only change-set endpoint, не кешировать seed в UI |
| UI interaction занимает больше времени | Один MapLibre `Marker` и одна fixture | Сократить визуальную полировку, сохранив полный UI-demo |
| Матрица не помещается в последний день | Проверки распределены по календарю | Сохранить обязательные Save/retry/stale/restart/revert, отложить только polish |

## 17. Открытые вопросы после Sprint 2

Эти вопросы не блокируют текущую реализацию:

- долгосрочный retention срок `edit_version_change_events` после закрытия `EditVersion`;
- будущая projected CRS strategy;
- правила и evidence для перехода из `POSITIONAL_ACCURACY_UNVERIFIED` в verified status;
- развитие сценария к нескольким features, topology, reconcile, review и post.
