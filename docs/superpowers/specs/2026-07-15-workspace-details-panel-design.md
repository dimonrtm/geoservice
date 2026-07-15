# Workspace Details Panel

Дата: 2026-07-15
Статус: утверждён пользователем для written spec
Расположение: `docs/superpowers/specs`

## Назначение

Заменить длинную строку метаданных поверх workspace-карты на устойчивую
панель контекста над картой. Панель должна поддерживать два последовательных
состояния рабочего сценария:

1. preview выбранного, но ещё не открытого наряда с primary action;
2. details успешно открытого workspace с AOI, состоянием версии и счётчиками.

Изменение должно улучшить сканируемость, доступность и поведение на узких
экранах без изменения backend endpoints или response contracts.

## Текущий Контекст

`EditorWorkOrdersView` использует split-view: список нарядов слева и `MapView`
справа. В `workspace` mode `MapView` формирует одну абсолютную строку `.badge`
из следующих значений:

- `WorkOrder.code`;
- `EditVersion.status`;
- `baseNetworkRevision`;
- количество features;
- количество associations.

Строка перекрывает карту, плохо переносится и не создаёт устойчивой зоны для
контекста и действий. До открытия workspace выбранный наряд представлен только
левой карточкой и action внутри неё.

Текущий `AssignedWorkOrdersResponse` содержит code, title, description и status.
AOI и edit version доступны только после успешной загрузки `WorkspaceResponse`.
Поэтому preview намеренно строится из существующего summary и не запрашивает
дополнительные данные.

## Выбранный Подход

Добавить отдельный презентационный компонент:

```text
apps/frontend/src/components/WorkspaceDetailsPanel.vue
```

Компонент размещается в `EditorWorkOrdersView` над `MapView`:

```text
workspacePane
├── WorkspaceDetailsPanel
└── MapView
```

`WorkspaceDetailsPanel` не импортирует store и API. Он получает выбранный
`WorkOrderSummary`, активный `WorkspaceResponse`, loading/error state через props
и эмитит событие `open`. `EditorWorkOrdersView` остаётся orchestration boundary:
связывает панель со store, запускает открытие и управляет focus после успеха.

Размещение панели прямо в `EditorWorkOrdersView` отклонено, потому что смешивает
список, workflow состояния, details markup и карту в одном растущем компоненте.
Размещение панели внутри `MapView` отклонено, потому что связывает общий map
component с workflow нарядов и усложняет `empty`/`editing` modes.

## Состояния Панели

### Нет Выбора

Если `selectedWorkOrder` отсутствует, `WorkspaceDetailsPanel` не монтируется.
Правая область продолжает показывать существующий `MapView mode="empty"`.

### Preview

Если наряд выбран, но `activeWorkspace` для него отсутствует, панель показывает:

- code;
- title;
- локализованный status наряда;
- description, если оно заполнено;
- primary action `Начать` или `Продолжить`.

AOI, revision, version и counts до открытия не показываются, потому что их нет в
текущем summary contract. Новый endpoint, дополнительный request на selection и
расширение списка нарядов не добавляются.

### Workspace Details

Если выбранный наряд соответствует `activeWorkspace`, панель показывает header
с code, title и локализованным status наряда. Description после открытия
скрывается. Ниже располагается семантический список метаданных:

| Поле | Источник |
|---|---|
| Область работ | `workOrder.scope.aoi.name` |
| Версия | локализованный `workOrder.editVersion.status` |
| Базовая ревизия | `workOrder.editVersion.baseNetworkRevision` |
| Объекты | `workOrder.editVersion.features.features.length` |
| Связи | `workOrder.editVersion.associations.length` |

`editVersion.id`, `workOrder.id`, AOI extent, raw API statuses и другие
технические identifiers не выводятся. Read-only badge и поясняющий текст также
не добавляются.

## Локализация

Панель отображает пользовательские значения и не показывает raw enum strings:

| API value | UI label |
|---|---|
| `assigned` | `Назначен` |
| `in_progress` | `В работе` |
| `open` | `Открыта` |

API values, TypeScript identifiers и contracts не переименовываются.

## Компонентный Контракт

`WorkspaceDetailsPanel` получает следующий контракт:

```ts
type WorkspaceDetailsPanelProps = {
  workOrder: WorkOrderSummary;
  workspace: WorkspaceResponse | null;
  isOpening: boolean;
  isOpenActionDisabled: boolean;
  errorMessage: string | null;
};
```

`isOpening` относится только к переданному `workOrder` и управляет label
`Открываем…` и `aria-busy`. `isOpenActionDisabled` блокирует action, пока любой
open workflow ещё выполняется.

Компонент эмитит событие `open` без payload и без обращения к store. Через
`defineExpose` он предоставляет единственный метод `focusHeading(): void`,
который вызывает родитель после успешного пользовательского открытия. Store и
API responsibility внутрь презентационного компонента не переносятся.

## Store State

Вместо единственного изменяемого boolean как источника loading context store
хранит:

```text
openingWorkOrderId: string | null
```

Общий признак `isOpeningWorkspace` остаётся публичным derived getter со
значением `openingWorkOrderId !== null`. Loading label `Открываем…` показывается
только если `openingWorkOrderId` совпадает с выбранным нарядом. Пока open workflow
другого наряда ещё выполняется, action нового выбранного наряда остаётся
заблокированным, но не получает ошибочную подпись `Открываем…`.

`openingWorkOrderId` устанавливается перед `POST /edit-versions` и очищается в
защищённом `finally` только для актуальной request sequence. Существующие guards
по request sequence и `selectedWorkOrderId` сохраняются: устаревший response не
может заменить текущий selected/opened workspace.

Ошибки продолжают храниться по `workOrderId`. Панель получает только ошибку
текущего выбранного наряда.

## Data Flow

### Выбор Наряда

```text
work-order card click
    -> store.selectWorkOrder(workOrderId)
    -> selectedWorkOrder changes
    -> WorkspaceDetailsPanel renders preview
    -> MapView remains in empty mode
```

Если до выбора уже был открыт другой workspace, данные остаются в store, но
`activeWorkspace` возвращает `null`, пока selection не совпадает с
`openedWorkOrderId`. Поэтому panel и map всегда описывают один и тот же наряд.
Повторный выбор сохранённого открытого наряда снова показывает его details и
карту без повторного API-вызова.

### Открытие Workspace

```text
WorkspaceDetailsPanel emits open
    -> EditorWorkOrdersView captures selected workOrderId
    -> store.openSelectedWorkOrder()
    -> POST openEditVersion
    -> update selected WorkOrder status
    -> GET workspace
    -> save opened workspace
    -> panel switches preview -> details
    -> MapView switches empty -> workspace
    -> fitBounds to AOI
    -> focus details heading
```

Primary action удаляется из левой карточки. Левая область отвечает за выбор,
правая панель — за контекст, запуск и результат открытия.

## Loading И Error Handling

Во время открытия инициировавшая кнопка:

- получает текст `Открываем…`;
- блокируется;
- не запускает повторный request;
- отмечает секцию через `aria-busy="true"`.

Панель сохраняет стабильную базовую структуру, чтобы loading text не вызывал
заметный layout shift.

Ошибка `POST` или `GET workspace` отображается рядом с primary action в preview
panel и получает `role="alert"`. Action снова становится доступным после
завершения request. Повторное нажатие повторяет существующую полную цепочку.
Если `POST` уже успел перевести наряд в `in_progress`, label становится
`Продолжить`.

Error message больше не дублируется внутри левой work-order card.

## Focus И Accessibility

Панель использует следующую семантику:

- `<section aria-labelledby="workspace-details-title">`;
- `<h2 id="workspace-details-title" tabindex="-1">`;
- `<dl>` с парами `<dt>/<dd>` для workspace metadata;
- `aria-busy` во время открытия;
- `role="alert"` для ошибки;
- видимые focus styles для интерактивных controls.

После успешного открытия, инициированного пользователем, `EditorWorkOrdersView`
ждёт обновления DOM и переводит focus на заголовок панели. Перед focus родитель
проверяет, что активный workspace всё ещё соответствует captured work order id.
Скрытая `aria-live="polite"` область сообщает:

```text
Рабочее пространство WO-001 загружено
```

Автоматическое восстановление workspace при mount не использует пользовательский
open handler, не переводит focus и не перехватывает клавиатурную навигацию.

Статус всегда передаётся текстом; цвет не является единственным различием.

## MapView

В `workspace` mode общий `.badge` не рендерится, а `renderWorkspace()` больше не
формирует длинную строку метаданных. AOI, features, `fitWorkspaceToAoi()` и событие
`workspaceFitted` сохраняют текущее поведение.

Короткий map status badge остаётся в `empty` и `editing` modes. Realtime badge в
`editing` mode не меняется. Полная переработка map statuses не входит в scope.

## Responsive Layout

Правая область `EditorWorkOrdersView` становится flex-column:

- panel имеет высоту по содержимому и нижнюю границу;
- `MapView` получает оставшееся пространство через `flex: 1 1 auto` и
  `min-height: 0`;
- panel не перекрывает canvas и map controls.

На desktop header и metadata используют доступную горизонтальную ширину. Название
AOI получает больше места, чем числовые показатели.

На ширине до текущего breakpoint `760px` существующая композиция «список сверху,
рабочая область снизу» сохраняется. Внутри панели metadata переходят в две
колонки, поле AOI занимает всю ширину, а карта сохраняет минимальную полезную
высоту. Панель всегда раскрыта и не вводит дополнительный collapse state.

Длинные title и AOI переносятся и не создают горизонтальный scroll. Preview
description после открытия исчезает, ограничивая высоту details state.

## Testing

### WorkspaceDetailsPanel

Component tests проверяют:

- preview с code, title, status, optional description и правильным action;
- labels `Назначен`, `В работе` и `Открыта`;
- emit `open`;
- loading label, disabled action и `aria-busy`;
- error с `role="alert"`;
- details с AOI, revision и точными counts;
- отсутствие UUID, raw statuses и description в details.

### EditorWorkOrdersView

Component/integration tests проверяют:

- выбор карточки показывает preview над empty map;
- primary action и open error отсутствуют в левой карточке;
- action панели запускает существующий store workflow;
- success переключает preview на details и показывает workspace map;
- error остаётся в preview panel и допускает retry;
- explicit open переводит focus на заголовок после успеха;
- restore при mount не переводит focus;
- смена selection не применяет stale response и не показывает `Открываем…` для
  неверного наряда;
- повторный выбор сохранённого opened work order возвращает details и map.

### Store

Store tests проверяют:

- lifecycle `openingWorkOrderId` на success и error;
- derived global busy state;
- очистку loading state только актуальным request;
- существующую защиту от stale response;
- сохранение и восстановление workspace в session storage.

### MapView

Component tests проверяют:

- workspace layers и fit behavior не изменились;
- длинный workspace badge и его metadata text отсутствуют;
- badges в `empty` и `editing` modes сохраняются.

### Ручная Проверка

Проверяются desktop и ширина до `760px`, длинные title/AOI, полезная высота карты,
клавиатурный сценарий, focus после открытия и screen-reader announcement.

## Критерии Готовности

Изменение готово, когда пользователь может:

1. выбрать наряд и увидеть понятный preview над картой;
2. запустить `Начать`/`Продолжить` из preview panel;
3. получить loading или actionable error в той же контекстной зоне;
4. после успеха увидеть AOI, version status, base revision и counts;
5. продолжить клавиатурную навигацию с заголовка загруженной панели;
6. использовать карту без длинной строки workspace metadata поверх canvas.

## Out Of Scope

- изменение backend endpoints, DTO или response JSON;
- загрузка AOI до открытия workspace;
- отдельный preview endpoint;
- отображение technical ids или AOI extent;
- read-only badge или поясняющий текст;
- workspace editing, validation, reconcile, review или post actions;
- collapse/expand панели;
- переработка `empty`/`editing` map statuses и realtime badge;
- отложенный mount MapLibre, code splitting и build budget;
- notification/toast infrastructure;
- визуальная отрисовка associations на карте.

## Последствия

Workflow получает устойчивое разделение обязанностей: левая область выбирает
наряд, details panel объясняет и запускает текущую операцию, `MapView` отвечает
только за карту. Backend contract остаётся прежним, поэтому риск сосредоточен во
frontend layout, state presentation и accessibility.

Отдельный panel component создаёт подходящую границу для будущих workflow
метаданных, но текущий scope намеренно не резервирует controls для validation,
reconcile или editing.

## Проверка Spec

Spec описывает одно ограниченное frontend-изменение и не требует нового backend
contract. Preview и details используют разные доступные источники данных без
скрытой дополнительной загрузки. Loading state однозначно привязан к
`openingWorkOrderId`, а focus выполняется только после explicit user action.
Плейсхолдеров, незаполненных решений и альтернативных трактовок component
boundary в документе нет.
