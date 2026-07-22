# Icon controls активного operational flow

Дата: 2026-07-22
Статус: согласован в диалоге, ожидает review письменной спецификации
Расположение: `docs/superpowers/specs`

## Назначение

Активный frontend GeoService использует понятные, но визуально тяжёлые текстовые
controls. Наиболее заметны `Выйти`, `Обновить`, `Начать`/`Продолжить`, действия
ошибок и `Копировать код обращения`. Для operational UI они медленно
сканируются, занимают лишнее место и неодинаково показывают loading/disabled
states.

Цель изменения — ускорить распознавание действий без потери ясности:

- использовать icon-only только для очевидных вспомогательных действий;
- сохранить видимый текст у основных, session и error actions;
- дать icon-only controls доступное имя и полноценный tooltip;
- унифицировать loading, disabled, focus и responsive behavior только у
  затронутых controls;
- не менять domain flow, API, stores и существующую обработку ошибок.

## Границы scope

В scope входят:

- обе кнопки `Выйти` в `App.vue`;
- `Обновить` в заголовке списка нарядов в `EditorWorkOrdersView.vue`;
- `Начать`/`Продолжить` в `WorkspaceDetailsPanel.vue`;
- action-кнопка и `Копировать код обращения` в `ActionableError.vue`;
- два небольших UI-примитива для icon+text и icon-only controls;
- desktop-first behavior и адаптация при ширине не более `760 px`;
- component tests, visual review и accessibility checks;
- зависимость `@lucide/vue` v1. Официальный пакет переименован из
  `lucide-vue-next`, API icon-компонентов сохранён.

Не входят:

- submit-кнопка `Войти` в `LoginScreen.vue`;
- кнопки выбора и содержимое карточек нарядов;
- встроенные MapLibre controls;
- legacy toolbar `MapView.vue` с `Сохранить`/`Удалить`;
- backend, API contracts, Pinia stores и domain behavior;
- полноценная design system;
- новая screenshot infrastructure.

`ActionableError.vue` является общим компонентом. Поэтому его action-кнопка
получит icon+text и при показе ошибки на экране входа, но сама submit-кнопка
формы авторизации не изменится.

## Выбранный подход

Создаются два специализированных domain-agnostic примитива:

- `UiButton` для icon+text controls;
- `UiIconButton` для icon-only controls с обязательным tooltip.

Этот подход выбран вместо одного универсального компонента и локальной разметки
в каждом экране. Два компонента удерживают API небольшим, исключают недопустимую
icon-only кнопку без accessible name и не дублируют tooltip/loading behavior в
нескольких call sites.

Компоненты располагаются в `apps/frontend/src/components/ui/`. Общие размеры,
цветовые варианты, focus ring и state styles выносятся в небольшой общий файл
стилей в той же директории. Создание общей библиотеки компонентов за пределами
этой задачи не требуется.

## Матрица controls

| Control | Desktop | `<=760 px` | Lucide icon | Tooltip |
|---|---|---|---|---|
| Обновить список нарядов | icon-only | icon-only | `RefreshCw` | `Обновить список назначенных нарядов` |
| Выйти в top bar | icon+text | icon-only | `LogOut` | Только у mobile icon-only варианта: `Выйти из GeoService` |
| Выйти на экране ошибки сессии | icon+text | icon+text | `LogOut` | Нет |
| Начать | icon+text | icon+text | `Play` | Нет |
| Продолжить | icon+text | icon+text | `Play` | Нет |
| Повторить | icon+text | icon+text | `RotateCcw` | Нет |
| Обновить в ошибке | icon+text | icon+text | `RefreshCw` | Нет |
| Войти в ошибке | icon+text | icon+text | `LogIn` | Нет |
| Переоткрыть | icon+text | icon+text | `FolderOpen` | Нет |
| Копировать код обращения | icon+text | icon+text | `Copy` | Нет |

У `ActionableError` иконка выбирается по `ErrorActionId` через исчерпывающий
mapping:

- `retry` -> `RotateCcw`;
- `refresh` -> `RefreshCw`;
- `reopen` -> `FolderOpen`;
- `sign-in` -> `LogIn`.

Видимая подпись продолжает приходить из `ErrorPresentation.action.label` и
остаётся источником смысла. Иконка только ускоряет распознавание.

## Контракт `UiButton`

`UiButton` всегда рендерит нативный `<button>` и поддерживает:

- обязательную icon-компоненту;
- default slot с видимым текстом;
- `variant`: `primary`, `secondary` или `error`;
- `loading`, `loadingLabel` и `disabled`;
- стандартные native attrs и события кнопки.

По умолчанию используется `type="button"`, чтобы применение примитива внутри
формы не запускало submit. Явно переданный native `type` может переопределить
default. Отдельный публичный `size` prop не добавляется: текущему scope нужны
только единые размеры из раздела Responsive behavior.

Lucide icon имеет `aria-hidden="true"` и не дублирует видимую подпись для
assistive technologies. При `loading` control получает `disabled` и
`aria-busy="true"`, а обычная icon заменяется на `LoaderCircle`.

Обычное и loading-содержимое располагаются в одной CSS-grid ячейке. Неактивное
содержимое визуально скрыто и исключено из accessibility tree, но участвует в
расчёте ширины. Поэтому переходы `Начать` -> `Открываем…` и `Продолжить` ->
`Открываем…` не двигают соседние элементы.

Loading-layer создаётся только если caller передал `loadingLabel` или включил
`loading`. Синхронные logout/error actions не получают скрытый default-текст и
не расширяются без необходимости; все асинхронные controls передают
`loadingLabel` явно.

## Контракт `UiIconButton`

`UiIconButton` всегда рендерит нативный `<button>` и требует:

- `icon`;
- `label` — короткое accessible name, например `Обновить` или `Выйти`;
- `tooltip` — более полное визуальное и доступное описание;
- `variant`, `loading`, `loadingLabel` и `disabled` по тем же правилам,
  что у `UiButton`.

Wrapper нужен только для позиционирования tooltip. Native attrs и listeners
forwarded непосредственно на внутренний `<button>`, а default `type` также
равен `button`.

`label` устанавливается как `aria-label`. Tooltip имеет собственный стабильный
id, `role="tooltip"` и связывается с trigger через `aria-describedby`.
`label` и `tooltip` не должны быть дословно одинаковыми: это предотвращает
бесполезное повторение при озвучивании имени и описания.

Tooltip element постоянно присутствует в DOM; открытие меняет только его
visual visibility. Поэтому `aria-describedby` никогда не ссылается на
отсутствующий id.

Tooltip находится внутри общего wrapper trigger/tooltip и:

- появляется через `500 ms` по pointer hover;
- появляется без задержки по keyboard focus;
- остаётся видимым, пока pointer находится над trigger или tooltip;
- закрывается по `Escape`, `blur` или уходу pointer с общей области;
- не получает focus и не содержит интерактивных элементов;
- располагается ниже trigger с отступом `8 px`;
- поддерживает выравнивание `center` и `end`; top-bar logout и panel refresh,
  расположенные у правого края контейнера, используют `end`;
- ограничен шириной `min(240px, calc(100vw - 16px))` и переносит длинный текст;
- не перекрывает trigger.

Поведение соответствует WAI tooltip pattern и требованиям WCAG 2.2 к
dismissible, hoverable и persistent content:

- <https://www.w3.org/WAI/ARIA/apg/patterns/tooltip/>
- <https://www.w3.org/WAI/WCAG22/Understanding/content-on-hover-or-focus.html>

Tooltip не является единственным источником смысла. На touch UI icon-only
используется только для знакомого действия `LogOut`, а assistive technologies
получают `aria-label`.

## Responsive behavior

Desktop-first breakpoint сохраняется равным `760 px`.

Top bar рендерит два взаимоисключающих logout-представления:

- desktop `UiButton` с `LogOut` и текстом `Выйти`;
- narrow `UiIconButton` с `LogOut`, `label="Выйти"` и
  `tooltip="Выйти из GeoService"`.

CSS `display: none` гарантирует, что в accessibility tree и tab order находится
только видимый вариант. Оба представления используют один обработчик
`auth.logout()`.

Размеры controls:

- desktop icon-only — `36 x 36 px`;
- desktop icon+text — высота `36 px`;
- при ширине не более `760 px` минимальная интерактивная цель — `44 x 44 px`;
- icon — `18 px`, `stroke-width="2"`;
- focus ring не обрезается родительскими контейнерами.

## State flow

### Обновление списка нарядов

`EditorWorkOrdersView` передаёт `workOrders.isLoading` в `UiIconButton`.
Во время запроса `RefreshCw` заменяется на вращающийся `LoaderCircle`, button
disabled, `aria-busy="true"`, accessible name меняется на
`Обновление списка нарядов`. Существующий panel live region продолжает
объявлять loading/result state. Повторный запуск через control невозможен.

### Открытие workspace

`WorkspaceDetailsPanel` передаёт существующие `isOpening` и
`isOpenActionDisabled` в `UiButton`. `Play` заменяется на `LoaderCircle`, а
видимый текст — на `Открываем…`. Store уже защищает операцию через
`openingWorkOrderId`; UI дополнительно блокирует повторный click.

### Error actions

`ActionableError` не вводит локальное фиктивное loading state. После emit
существующий parent/store переводит экран в loading, session или workspace
state. Контракт emit и `ErrorActionId` не меняются.

### Копирование correlation ID

`ActionableError` получает локальный `isCopying`, который существует только на
время `navigator.clipboard.writeText`. Кнопка временно disabled и показывает
`LoaderCircle` с текстом `Копируем…` и accessible name
`Копируем код обращения`. Успех или ошибка продолжают передаваться существующим
`copyStatus` с `aria-live="polite"`; дополнительные таймеры и transient success
icon не добавляются.

### Logout

Loading state для logout не показывается. `auth.logout()` немедленно очищает
локальную сессию, поэтому authed top bar исчезает; server logout завершается в
существующем асинхронном flow. Ошибка server logout по текущему контракту не
возвращает пользователя в authed UI.

## Visual states

Изменение сохраняет текущую палитру:

- `primary` — зелёный фон и белый текст;
- `secondary` — светлый фон и нейтральная рамка;
- `error` — белый фон, красные текст и рамка;
- icon наследует `currentColor`;
- focus ring контрастный и одинаковый у обоих примитивов;
- disabled/loading state не передаётся одним цветом;
- при `prefers-reduced-motion: reduce` вращение loader отключается, а состояние
  остаётся понятным по тексту, `aria-label`, `aria-busy` и disabled state.

## Error handling

UI-примитивы не вызывают stores, API или Clipboard API и не перехватывают
domain errors. Они только отображают входные props и выпускают native button
events.

Существующие владельцы операций остаются владельцами ошибок:

- `workOrders.loadAssigned()` — загрузка списка;
- `workOrders.openSelectedWorkOrder()` и retry/reopen методы — workspace flow;
- `auth.logout()` — session flow;
- `ActionableError.copyCorrelationId()` — Clipboard API и live-status.

Если операция завершается ошибкой, loading prop возвращается в `false`, control
возвращается в обычное состояние, а существующий `ErrorPresentation` остаётся
источником сообщения и следующего действия.

## Testing

### UI-примитивы

Tests `UiButton` проверяют:

- совместный render icon и видимого текста;
- `aria-hidden` у icon;
- `disabled` и `aria-busy` при loading;
- одновременное присутствие normal/loading слоёв в общем stable-content wrapper;
- native attrs, click event и предотвращение повторного click.

`jsdom` не измеряет реальный layout, поэтому отсутствие изменения внешней
ширины проверяется ручным visual review, а не ложным числовым assertion в
component test.

Tests `UiIconButton` с fake timers проверяют:

- обязательные accessible name и tooltip contract;
- уникальный tooltip id и `aria-describedby`;
- hover-delay `500 ms` и немедленное открытие по focus;
- hoverable/persistent behavior;
- закрытие по `Escape`, `blur` и `mouseleave`;
- loading icon, accessible name и блокировку повторного click.

### Регрессии экранов

- `App.test.ts`: desktop и narrow logout вызывают `auth.logout`, имеют разные
  UI-примитивы и взаимоисключающие responsive classes.
- `EditorWorkOrdersView.test.ts`: refresh вызывает `loadAssigned`, отражает
  `workOrders.isLoading` и сохраняет существующие list states.
- `WorkspaceDetailsPanel.test.ts`: `Начать`, `Продолжить`, `Открываем…`, icon и
  disabled behavior соответствуют входным props.
- `ActionableError.test.ts`: каждый `ErrorActionId` выбирает правильную icon,
  emit не меняется, Clipboard API блокируется на время операции, а существующее
  live-status сообщение сохраняется.

Tests не должны зависеть от внутренней SVG-разметки Lucide. Проверяется выбранная
icon-компонента или стабильный control contract, а не конкретные `<path>`.

### Автоматическая проверка

В `apps/frontend` выполняются:

```powershell
npm test
npm run typecheck
npm run lint
npm run format:check
npm run build
```

### Ручная проверка

- desktop и breakpoint `760 px`;
- keyboard-only navigation: `Tab`, `Enter`/`Space`, focus ring, `Escape`;
- hoverable и persistent tooltip;
- отсутствие layout shift при loading;
- понятность icon+text controls без tooltip;
- отсутствие tooltip overflow у правой границы viewport;
- `prefers-reduced-motion`;
- smoke-проверка accessible names icon-only controls со screen reader.

## Предполагаемые файлы изменения

- `apps/frontend/package.json`;
- `apps/frontend/package-lock.json`;
- новые файлы в `apps/frontend/src/components/ui/`;
- `apps/frontend/src/App.vue` и `App.test.ts`;
- `apps/frontend/src/components/EditorWorkOrdersView.vue` и соответствующий test;
- `apps/frontend/src/components/WorkspaceDetailsPanel.vue` и соответствующий test;
- `apps/frontend/src/components/ActionableError.vue` и соответствующий test.

Точный список новых UI-файлов и порядок TDD-шагов фиксируются в отдельном
implementation plan после review этой спецификации.

## Критерии готовности

- матрица controls реализована без расширения scope;
- icon-only controls имеют понятные `aria-label` и доступные tooltips;
- основные, session и error actions сохраняют видимый текст;
- responsive logout корректно переключается на breakpoint `760 px`;
- loading не вызывает layout shift и блокирует повторные действия;
- tooltip выполняет keyboard, dismissible, hoverable и persistent contract;
- все автоматические проверки проходят;
- ручной desktop/mobile/accessibility review не выявляет overflow, потерю focus
  или непонятные icon-only actions.
