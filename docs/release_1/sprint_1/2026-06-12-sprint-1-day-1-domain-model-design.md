# Спринт 1, День 1: Доменная Модель

Дата: 2026-06-12
Статус: подтвержден пользователем

## Назначение

Документ определяет сущности, связи, состояния и инварианты Спринта 1 без
фиксации окончательной SQL-схемы.

Связанные артефакты:

- [Сценарий приемки](2026-06-12-sprint-1-day-1-acceptance-design.md)
- [API-контракт](2026-06-12-sprint-1-day-1-api-contract-design.md)
- [Вертикальный backlog](2026-06-12-sprint-1-day-1-vertical-backlog-design.md)

## Граница Агрегатов

```text
User(Editor)
  -> WorkOrder
       -> AOI
       -> Feeder
            -> NetworkFeature[]
            -> NetworkAssociation[]
       -> EditVersion
            -> baseRevision(Default)
```

`WorkOrder` является корнем пользовательского сценария. Он связывает
исполнителя, географическую рабочую область, логический участок сети и
изолированный контекст version.

## User И Role

`User` представляет аутентифицируемого участника workflow.

Минимальные свойства:

- стабильный `id`;
- login/email;
- отображаемое имя;
- одна workflow-роль;
- признак активности.

В Спринте 1 поддерживаются взаимоисключающие роли `Editor` и `Reviewer`.
`Editor` работает с назначенными задачами. `Reviewer` существует в RBAC и
demo seed, но reviewer workflow не реализуется.

## WorkOrder

`WorkOrder` представляет назначенную задачу по просмотру и последующему
изменению конкретного участка utility network.

Минимальные свойства:

- стабильный `id` и человекочитаемый `code`;
- русские `title` и `description`;
- `assigneeId`;
- `aoiId`;
- `feederId`;
- состояние;
- timestamps создания и обновления.

Состояния Спринта 1:

```text
Assigned -> InProgress
```

Переход выполняется при первом успешном создании `EditVersion`. Остальные
состояния полного Release 1 добавляются в следующих спринтах.

Инварианты:

- `WorkOrder` назначен ровно одному активному `Editor`;
- открыть задачу может только назначенный `Editor`;
- `WorkOrder` ссылается ровно на один `AOI` и один `Feeder`;
- у `WorkOrder` не более одной активной `EditVersion`;
- `Reviewer` не может открыть editor workspace.

## AOI

`AOI` (`Area of Interest`) — именованная географическая область задачи. Это
серверная граница доступного набора данных, а не только положение камеры.

Минимальные свойства:

- стабильный `id`;
- русские `name` и необязательное `description`;
- geometry типа `Polygon` или `MultiPolygon`;
- `SRID 4326`;
- вычисляемый extent для начального позиционирования карты.

Поведение:

- workspace возвращает только `NetworkFeature` выбранного `Feeder`, geometry
  которых пересекает `AOI`;
- пересекающая geometry возвращается целиком и не обрезается;
- `NetworkAssociation` возвращается только при наличии обоих связанных
  объектов в текущем наборе features;
- `AOI` фиксируется при назначении `WorkOrder`;
- изменение `AOI`, несколько AOI на задачу, buffer zones и spatial ACL не
  входят в Спринт 1.

Проверка доступа по `AOI` не заменяет assignment authorization. Для доступа
одновременно требуются роль `Editor` и назначение соответствующего
`WorkOrder`.

## Feeder

`Feeder` — именованный логический участок электрической сети от источника
питания к связанным узлам, линиям и устройствам. В Спринте 1 он служит
устойчивой границей demo-данных и workspace, а не моделью электрического
расчета.

Минимальные свойства:

- стабильный `id`;
- уникальный `code`;
- русские `name` и необязательное `description`;
- признак активности.

### NetworkFeature

`NetworkFeature` — пространственный объект сети, принадлежащий одному
`Feeder`.

Минимальные виды:

- `Junction` — точка соединения;
- `Line` — участок линии между узлами;
- `Device` — выключатель, трансформатор или другое оборудование.

Минимальные свойства:

- стабильный `id`;
- `feederId`;
- уникальный в пределах dataset `assetCode`;
- `featureType`;
- GeoJSON-совместимая geometry в `SRID 4326`;
- русские отображаемые атрибуты;
- authoritative object revision.

### NetworkAssociation

`NetworkAssociation` — непространственная направленная связь между двумя
`NetworkFeature`.

Минимальные виды:

- `Connectivity`;
- `Containment`;
- `Attachment`.

Минимальные свойства:

- стабильный `id`;
- `feederId`;
- `fromFeatureId`;
- `toFeatureId`;
- `associationType`;
- authoritative object revision.

Инварианты агрегата `Feeder`:

- каждый demo `NetworkFeature` принадлежит ровно одному `Feeder`;
- association не ссылается на отсутствующий feature;
- оба конца association принадлежат тому же `Feeder`, что и association;
- удаление непустого `Feeder` запрещено;
- межфидерные associations, смена принадлежности feature и вычисление
  energized topology не входят в Спринт 1.

## Default

`Default` — authoritative опубликованное состояние utility network.

Для Спринта 1 требуется стабильный идентификатор и монотонная
`currentRevision`. Workspace читает данные из `Default`, но не изменяет их.

## EditVersion

`EditVersion` — изолированный рабочий контекст одного `WorkOrder`.

Минимальные свойства:

- стабильный `id`;
- `workOrderId`;
- `ownerId`;
- `baseRevision`;
- состояние;
- timestamps создания и последнего открытия.

Состояние Спринта 1:

```text
Open
```

Инварианты:

- version принадлежит одному `WorkOrder` и назначенному `Editor`;
- `baseRevision` фиксируется при создании и не меняется;
- создание version и фиксация `baseRevision` атомарны;
- повторное открытие возвращает существующую активную version;
- уникальность активной version должна выдерживать конкурентные запросы;
- version не содержит change set до Спринта 2;
- сеть внутри workspace доступна только для чтения.

## Demo Dataset

`synthetic_utility_feeder_01` должен содержать:

- один `AOI`;
- один `Feeder`;
- junctions, lines и devices;
- валидные внутрефидерные associations;
- authoritative `Default`;
- `WO-001`, назначенный `alexey.editor`;
- demo users `alexey.editor` и `marina.reviewer`.

Seed должен быть идемпотентным и давать одинаковые стабильные codes после
повторного восстановления.
