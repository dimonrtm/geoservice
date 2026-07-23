# Стабильная геометрия асинхронных кнопок

Дата: 2026-07-23
Статус: согласован и одобрен пользователем; implementation plan подготовлен
Расположение: `docs/superpowers/specs`

## Назначение

При переходе кнопки из idle в loading более длинная подпись может изменить её
ширину и сдвинуть соседние элементы. В GeoService эта проблема уже частично
решена в `UiButton`: idle- и loading-содержимое располагаются в одной
CSS-grid ячейке. Однако правило ещё не завершено как общий контракт:

- submit-кнопка `LoginScreen` использует отдельную разметку;
- `loadingLabel` имеет generic fallback;
- поведение при нехватке места не определено;
- обязательность предметной loading-подписи не закреплена;
- ручной критерий проверки геометрии не сформулирован отдельно.

Цель изменения — сделать размеры всех поддерживаемых асинхронных кнопок
стабильными между idle и loading без введения одинаковой ширины для разных
действий.

## Критерии успеха

- Каждая текстовая кнопка сохраняет width и height при переходе между idle и
  одним заранее объявленным loading-состоянием.
- Разные кнопки могут иметь разную ширину.
- Icon-only controls сохраняют фиксированный квадратный размер.
- Асинхронная кнопка всегда получает явный предметный `loadingLabel`.
- Длинная подпись не расширяет кнопку за пределы доступного контейнера и не
  переносится на новую строку.
- Полная активная подпись остаётся доступной assistive technologies.
- Повторное действие блокируется на всё время loading.
- Решение покрывает текущие активные controls и задаёт контракт для будущих.

## Границы scope

В scope входят:

- `UiButton` и `UiIconButton`;
- общие стили `ui-controls.css`;
- `Войти` в `LoginScreen`;
- существующие loading-состояния `Начать`/`Продолжить`, копирования correlation
  ID и обновления списка нарядов;
- component tests;
- ручная проверка desktop, mobile и узкого контейнера.

Не входят:

- единая фиксированная ширина всех кнопок;
- публичные размеры `sm`, `md` или `lg`;
- отдельный `UiAsyncButton`;
- резервирование места под error blocks, списки, карту или другие части экрана;
- несколько последовательно меняющихся loading-подписей одной операции;
- новый browser test runner или screenshot infrastructure;
- legacy editing toolbar `MapView` с асинхронными `Сохранить` и `Удалить`.

Legacy toolbar остаётся явным исключением: у его действий сейчас нет
pending/loading state, а добавление такого состояния расширило бы P3 с
геометрии на поведение legacy-редактора.

## Выбранный подход

Развивается существующий `UiButton`. Отдельный асинхронный компонент и
предустановленные ширины не вводятся.

Если caller передал `loadingLabel`, idle- и loading-слои создаются одновременно
до начала операции и занимают одну CSS-grid ячейку. Неактивный слой скрывается
через `visibility: hidden`: он продолжает участвовать в расчёте intrinsic size,
но исключается из accessibility tree через `aria-hidden`.

Итоговая ширина определяется как:

```text
max(idle icon + idle label, loader + loading label) + horizontal padding
```

Переключение `loading` меняет только видимость слоёв и state-атрибуты. DOM-слой
с более длинной подписью не добавляется после click, поэтому соседние элементы
не должны смещаться.

## Отклонённые подходы

### Отдельный `UiAsyncButton`

Он сделал бы границу синхронных и асинхронных controls более заметной, но
привёл бы к двум почти одинаковым компонентам и дублированию API. Для текущего
числа controls это лишняя абстракция.

### Размеры `sm`, `md`, `lg`

Предустановленные width/min-width упростили бы построение регулярной сетки, но
оставляли бы лишнее пустое пространство, требовали ручного выбора размера и
хуже работали бы с локализованными подписями. Они также не соответствуют
принятому требованию: стабильность нужна между состояниями одной кнопки, а не
между разными действиями.

### Runtime-измерение текста

Измерение обоих слоёв через JavaScript или `ResizeObserver` не требуется:
CSS-grid уже умеет резервировать максимальный intrinsic size. Runtime-измерение
добавило бы timing, дополнительное состояние и новые тестовые риски без
пользовательской пользы.

## Контракт `UiButton`

`UiButton` остаётся единственным текстовым примитивом для поддерживаемых
асинхронных действий.

Синхронная форма props:

- обязательный `icon`;
- текст через default slot;
- опциональные `variant` и `disabled`;
- `loading` и `loadingLabel` не передаются.

Асинхронная форма props:

- те же базовые props;
- обязательный boolean `loading`;
- обязательный непустой `loadingLabel`.

Две формы выражаются TypeScript union: допустимо либо отсутствие обоих loading
props, либо одновременное наличие `loading: boolean` и
`loadingLabel: string`. Это ловит статически отсутствующую подпись при
`vue-tsc`. Непустое значение дополнительно проверяется во время выполнения,
поскольку TypeScript не отличает пустую строку.

Generic fallback `Выполняется…` удаляется. При нарушении контракта component в
development выдаёт диагностическое предупреждение. Безопасное production
поведение не создаёт пустую подпись: control остаётся disabled и
`aria-busy="true"`, но сохраняет idle icon/label вместо показа безымянного
loading-слоя.

При корректном loading:

- normal icon заменяется на `LoaderCircle`;
- видимый текст заменяется на `loadingLabel`;
- button получает native `disabled`;
- button получает `aria-busy="true"`;
- повторный click блокируется браузером;
- inactive layer получает `aria-hidden="true"`.

Компонент не принимает Promise, не запускает операции и не сбрасывает loading
самостоятельно.

## Контракт `UiIconButton`

`UiIconButton` сохраняет существующую роль icon-only control:

- `label` задаёт idle accessible name;
- `tooltip` остаётся визуальным описанием действия;
- асинхронная форма также требует пару `loading` и непустой `loadingLabel`;
- generic loading fallback удаляется;
- при loading icon заменяется на `LoaderCircle`, accessible name — на
  `loadingLabel`;
- native `disabled` и `aria-busy="true"` блокируют повторное действие.

Его геометрия не зависит от длины accessible name, поскольку видимого текста
внутри button нет. При пустом или отсутствующем loading label действуют те же
диагностика и безопасное поведение: control остаётся disabled и
`aria-busy="true"`, но сохраняет idle icon и `label`.

## Геометрия и responsive behavior

Общие правила:

- desktop text button имеет block size `36 px`;
- при viewport не более `760 px` block size становится `44 px`;
- desktop icon-only control имеет размер `36 x 36 px`;
- mobile icon-only control имеет размер `44 x 44 px`;
- icon имеет размер `18 px`;
- публичный size prop не добавляется.

Текстовая кнопка имеет intrinsic inline size, рассчитанный по обоим слоям.
`UiButton` и stable-content wrapper получают ограничения, позволяющие
сжиматься внутри родителя:

- `max-inline-size: 100%`;
- `min-inline-size: 0` у grid/flex intermediates;
- label имеет `overflow: hidden`, `text-overflow: ellipsis` и
  `white-space: nowrap`.

Ellipsis является аварийным поведением для узкого контейнера, а не способом
сокращать обычные подписи. Полный активный текст остаётся в DOM и формирует
accessible name. Высота button при обрезке не меняется.

`LoginScreen` задаёт локальный `inline-size: 100%`, поэтому его submit-кнопка
занимает всю ширину формы независимо от длины idle/loading label.

Гарантия относится к переходу между idle и одним стабильным `loadingLabel`.
Caller не должен менять loading-подпись между фазами одной операции. Если
появится подтверждённый multi-phase сценарий, для него потребуется отдельный
дизайн резервирования всех допустимых состояний.

## State flow

Источник loading остаётся у caller или store:

```text
click
  -> owner устанавливает loading=true
  -> UI-примитив показывает заранее зарезервированный loading-слой
  -> owner выполняет операцию
  -> owner/store устанавливает loading=false
  -> UI-примитив возвращает idle-слой без изменения геометрии
```

Текущие потоки:

| Control | Источник состояния | Idle label | Loading label |
|---|---|---|---|
| Вход | `LoginScreen.isSubmitting` | `Войти` | `Выполняем вход…` |
| Открытие workspace | `openingWorkOrderId` / `isOpening` | `Начать` или `Продолжить` | `Открываем…` |
| Копирование correlation ID | `ActionableError.isCopying` | `Копировать код обращения` | `Копируем…` |
| Обновление списка | `workOrders.isLoading` | accessible `Обновить` | accessible `Обновление списка нарядов` |

`LoginScreen` переводит native `.submitButton` на `UiButton`, передаёт
`type="submit"`, `variant="primary"`, `isSubmitting`,
`loadingLabel="Выполняем вход…"` и Lucide icon `LogIn`. Локальный класс
сохраняет `inline-size: 100%`; shared `UiButton` становится источником высоты,
padding, цвета и остальных state styles. Компоновка формы за пределами button
не меняется.

Action-кнопки ошибок не получают фиктивный локальный loading. Они синхронно
выпускают event, после чего host переключает всю session/error/workspace-зону.
Стабилизация геометрии этой зоны не относится к кнопочному контракту.

## Ошибки и accessibility

UI-примитивы не перехватывают исключения. Локальные владельцы loading state
сбрасывают его в `finally`; store-driven controls отражают state store. После
ошибки button возвращается в idle, а существующий `ErrorPresentation`
показывает сообщение и доступное следующее действие.

Во время loading:

- button остаётся нативным `<button>`;
- `disabled` предотвращает повторную активацию мышью и клавиатурой;
- `aria-busy="true"` сообщает состояние assistive technologies;
- скрытый слой исключается через `aria-hidden`;
- decorative icons имеют `aria-hidden="true"`;
- полный активный label остаётся доступным, даже если визуально обрезан.

Изменение высоты формы из-за появления ошибки допустимо. Эта задача не
резервирует место под ещё не существующий error block.

## Testing

### `UiButton`

Component tests проверяют:

- idle/loading layers существуют одновременно до начала операции, если передан
  `loadingLabel`;
- оба слоя находятся в одном stable-content wrapper;
- переключение меняет visibility-class и `aria-hidden`, но не структуру;
- active label сохраняет полный текст в DOM;
- loading устанавливает `disabled` и `aria-busy`;
- disabled button не выпускает повторный click;
- отсутствие loading label в асинхронной форме ловится typecheck;
- пустой loading label вызывает development diagnostic;
- DOM получает классы ограничения ширины и ellipsis.

`jsdom` не используется для числового сравнения `getBoundingClientRect`,
поскольку он не выполняет реальный browser layout.

### Регрессии экранов

- `LoginScreen.test.ts` использует deferred login Promise и проверяет переход
  `Войти -> Выполняем вход… -> Войти`, блокировку повторного submit и
  восстановление idle после ошибки.
- `WorkspaceDetailsPanel.test.ts` сохраняет проверки `Начать`, `Продолжить`,
  `Открываем…`, `disabled` и `aria-busy`.
- `ActionableError.test.ts` сохраняет проверки локального copy pending state.
- `EditorWorkOrdersView.test.ts` сохраняет проверки refresh loading state.
- `UiIconButton.test.ts` подтверждает обязательную предметную loading-подпись и
  неизменный icon-only contract.

### Автоматическая проверка

В `apps/frontend` выполняются:

```powershell
npm test
npm run typecheck
npm run lint
npm run format:check
npm run build
```

### Ручная приёмка

На desktop и viewport `<=760 px` проверяются:

- одинаковые width и height до и во время loading;
- отсутствие смещения соседних controls;
- full-width login button;
- `36 x 36 px` и `44 x 44 px` у icon-only controls;
- ellipsis без переноса в искусственно узком контейнере;
- полный accessible name у визуально обрезанной подписи;
- focus ring без обрезки;
- возврат исходной геометрии после успешной операции и ошибки.

Новый Playwright, Cypress или иной browser runner не добавляется. Ручная
проверка и component screenshot допустимы как артефакты review, но не становятся
новой постоянной инфраструктурой.

## Предполагаемые файлы изменения

- `apps/frontend/src/components/ui/UiButton.vue`;
- `apps/frontend/src/components/ui/UiButton.test.ts`;
- `apps/frontend/src/components/ui/UiIconButton.vue`;
- `apps/frontend/src/components/ui/UiIconButton.test.ts`;
- `apps/frontend/src/components/ui/ui-controls.css`;
- `apps/frontend/src/components/LoginScreen.vue`;
- `apps/frontend/src/components/LoginScreen.test.ts`;

`WorkspaceDetailsPanel.test.ts`, `ActionableError.test.ts` и
`EditorWorkOrdersView.test.ts` являются обязательными regression targets, но
изменения их production-компонентов не планируются: текущие call sites уже
передают обе части loading contract.

Backend, API contracts, stores, `MapView` и domain behavior не изменяются.
