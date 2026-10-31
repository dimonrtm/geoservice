# FE-02 — план реализации ошибки первоначального запуска карты

> **Для исполнителя:** применять `superpowers:executing-plans` при самостоятельном выполнении либо `superpowers:subagent-driven-development`, если пользователь выберет выполнение субагентами. Шаги отмечать через checkbox. Не выполнять `git add`, `git commit` и `git push`: запрет AGENTS.md имеет приоритет над skills.

**Цель:** показать ошибку первоначального запуска карты во всех режимах и скрывать команды до готовности карты.

**Архитектура:** состояние запуска принадлежит `MapView`; родитель получает событие готовности и управляет видимостью панели workspace. Pinia и серверные контракты не меняются.

**Стек:** существующие Vue 3, TypeScript, Pinia, MapLibre, Vitest и Vue Test Utils; без новых зависимостей.

**Дизайн:** [принятый дизайн FE-02](2026-10-31-fe-02-map-initialization-design.md). Также прочитать [анализ с ответами пользователя](2026-10-31-fe-02-map-initialization-analysis.md).

## Общие ограничения

- Точные тексты: «Не удалось запустить карту» и «Обновите страницу с помощью кнопки обновления в браузере.»; отдельный `role="alert"` на месте карты.
- Нет retry-кнопки, автоматического retry или reload. Все режимы: `workspace`, `empty`, `editing`.
- До готовности скрыты legacy toolbar и вся `WorkspaceEditCommands`, включая действия восстановления.
- Скрытие не сбрасывает draft/recovery, не запускает mutation и не меняет права. После готовности сохраняются существующие ограничения команд.
- FE-03, FE-04, load timeout/cancel, OSM tile errors и потеря работающего WebGL вне задачи. Не менять `useMapInstance` ради общего исправления lifecycle.
- Обычные текстовые файлы записывать UTF-8 с LF. Документация — по-русски. Изменения оставлять unstaged.

## Файлы и ответственность

| Файл | Изменение |
| --- | --- |
| `apps/frontend/src/components/MapView.vue` | Состояние запуска, сообщение, видимость legacy toolbar, событие готовности |
| `apps/frontend/src/components/MapView.test.ts` | Ошибка/ожидание/готовность, разделение ошибок, поздний результат |
| `apps/frontend/src/components/EditorWorkOrdersView.vue` | Локальная готовность и условие отображения панели |
| `apps/frontend/src/components/EditorWorkOrdersView.test.ts` | Управляемый mock готовности, видимость панели и сохранность store |
| `docs/sprint_2/fe-02/` | Браузерные evidence и ограничения проверки |
| `docs/sprint_2/2026-10-31-fe-02-map-initialization-implementation-report.md` | Краткий итог реализации и фактически выполненных проверок |

Новые production-модули не нужны. Список нарядов, `WorkspaceComparisonPanel` и самостоятельный список восстановления не переделываются: принятый дизайн ограничивает скрытие панели `WorkspaceEditCommands` и legacy toolbar.

## Особое внимание при проверке

1. `createMap()` возвращает `null`: не показывать готовность; в живом компоненте показать ошибку запуска (задача 1).
2. Компонент удалён, затем Promise resolved/rejected: не публиковать готовность и не продолжать настройку удалённой карты (задача 1).
3. Переход empty → workspace после готовой пустой карты: новый экземпляр начинает с false (задача 2).
4. Legacy renderer создан, но загрузка данных отклонена: не выдавать её за отказ запуска renderer (задача 1).
5. Повторный workspace readback при том же экземпляре карты: не прятать команды навсегда и не сбрасывать recovery (задача 2).

## Задача 1 — состояние запуска и сообщение в MapView

**Интерфейс:** событие `readyChange: [ready: boolean]`; локальное `startupState: Ref<'loading' | 'ready' | 'error'>`. Существующее `workspaceFitted` сохраняется. `mapReady` можно вычислять из состояния, сохранив текущие потребители. `setReady(ready: boolean): void` централизует публикацию готовности; `disposed: boolean` запрещает позднее продолжение после unmount.

- [x] Добавить parameterized test `shows startup error in every map mode` для rejected `createMap`. Использовать существующие fixture/mocks. Проверять:

  ```ts
  expect(wrapper.findAll('[role="alert"]')).toHaveLength(1);
  expect(wrapper.get('[role="alert"]').text()).toContain('Не удалось запустить карту');
  expect(wrapper.get('[role="alert"]').text()).toContain('Обновите страницу с помощью кнопки обновления в браузере.');
  expect(wrapper.get('[role="alert"]').find('button').exists()).toBe(false);
  expect(wrapper.find('.toolbar').exists()).toBe(false);
  expect(wrapper.emitted('readyChange')?.some(([ready]) => ready === true)).not.toBe(true);
  ```

- [x] Добавить `hides commands until startup completes`: deferred Promise; до resolve toolbar и interaction отсутствуют, после успешной подготовки editing toolbar доступен; в workspace ready публикуется после `setWorkspaceData`. Добавить `shows startup error for null map` и `shows error when initial workspace rendering throws` с тем же alert и без true-события.
- [x] Добавить `ignores startup completion after unmount` для resolve/reject: после удаления нет новых ready-событий, `ensureWorkspaceLayers`, загрузки legacy-данных и привязки interaction. Reset mock implementations между тестами, включая throwing mocks.
- [x] Запустить из `apps/frontend`: `npm.cmd run test -- src/components/MapView.test.ts --maxWorkers=2`. Убедиться, что новые assertions падают из-за отсутствующего поведения, а не ошибки fixture/tooling.
- [x] Реализовать состояние и событие в `MapView.vue`. При mount публиковать false, после каждого await перед побочными действиями проверять `disposed`. При unmount сначала отметить disposed и опубликовать false, затем существующий teardown. Не добавлять timeout/cancel Promise в composable.
- [x] Разделить обработку запуска и legacy-загрузки. Rejected/null `createMap` и исключение первичной workspace-отрисовки переводят в error. Empty становится ready после `createMap`. Editing становится ready после существующей настройки; штатный `loadLayersResult.status === 'empty'` завершается без startup alert и сохраняет «Слоев нет». Отказ legacy-загрузки оставляет команды скрытыми и сообщает «Не удалось загрузить данные карты» через существующий badge, без startup alert. Добавить тест `does not classify legacy data failure as map startup failure`:

  ```ts
  expect(wrapper.find('[role="alert"]').exists()).toBe(false);
  expect(wrapper.get('.badge').text()).toContain('Не удалось загрузить данные карты');
  expect(wrapper.find('.toolbar').exists()).toBe(false);
  ```

- [x] Добавить разметку и CSS сообщения по макету: отдельный alert над контейнером карты, без автофокуса; скрыть legacy badge/realtime badge при startup error. Toolbar виден только в editing при ready. Существующие workspace interaction и успешное отсутствие badge сохранить. Watcher FE-03 не переписывать.
- [x] Повторить команду тестов задачи и получить PASS, затем `npm.cmd run typecheck` — exit 0. Оставить изменения unstaged.

## Задача 2 — видимость панели workspace

**Интерфейс:** потребляет `readyChange(ready: boolean)` задачи 1. `EditorWorkOrdersView` хранит `workspaceMapReady = ref(false)` и принимает событие только от workspace-ветки `MapView`; empty-ветка не разрешает панель. Обработчик `onWorkspaceMapReadyChange(ready: boolean): void` обновляет ref.

- [x] Расширить mock `MapView` в `EditorWorkOrdersView.test.ts`: объявить `readyChange`, не эмитить true автоматически. В существующем тесте расположения команд сначала проверить отсутствие панели после открытия workspace, затем явно вызвать `$emit('readyChange', true)` и проверить прежнее расположение.
- [x] Добавить `shows workspace commands only after map readiness`: activeWorkspace без ready → панели нет; true → есть; false → нет. Проверять `wrapper.find('[data-test="workspace-edit-commands"]').exists()` соответственно false/true/false, а не только CSS или disabled.
- [x] Добавить `does not inherit readiness from empty or removed map`: готовая empty-ветка не разрешает панель; workspace готов → закрытие → новый workspace до ready без панели. Добавить `keeps readiness on current workspace readback`: заменить payload того же активного workspace при сохранении экземпляра, панель остаётся видимой.
- [x] Добавить `hiding commands preserves recovery and does not send mutations`: с реалистичным recovery fixture сохранить snapshot relevant store state, скрыть панель и проверить равенство snapshot и отсутствие вызовов Save/Revert/retry. Использовать существующие store fixtures; не придумывать обходящие типы synthetic поля. Проверить существующие ограничения доступности после true.
- [x] Запустить `npm.cmd run test -- src/components/EditorWorkOrdersView.test.ts --maxWorkers=2` и зафиксировать ожидаемый RED новых сценариев.
- [x] Реализовать условие `activeWorkspace && workspaceMapReady` для всей `WorkspaceEditCommands`. Подписать workspace-карту на событие, сбрасывать ref синхронно при исчезновении activeWorkspace; сохранить уведомление false при unmount карты из задачи 1. Не remount карту на каждый readback и не менять store. Не связывать видимость самой карты с её готовностью.
- [x] Запустить оба изменённых тестовых файла вместе и typecheck; ожидаются PASS и exit 0. Проверить diff на случайные изменения recovery и FE-03.

## Задача 3 — итоговая проверка и evidence

- [x] Из `apps/frontend` выполнить `npm.cmd run test -- --maxWorkers=2`, `npm.cmd run typecheck` и `npm.cmd exec prettier -- --check src/components/MapView.vue src/components/MapView.test.ts src/components/EditorWorkOrdersView.vue src/components/EditorWorkOrdersView.test.ts`. Ожидание — все тесты PASS и exit 0. Исправить относящиеся к изменению failures; сторонние проблемы отделить по воспроизведению.
- [x] В отдельном браузерном тестовом контексте до загрузки приложения запретить создание WebGL-контекста, открыть workspace и проверить сообщение, отсутствие панели и доступность списка нарядов. Сохранить точный способ инъекции и скриншот; не менять production-код или глобальные настройки браузера. Если инструменты недоступны, явно зафиксировать непроведённую проверку.
- [x] Убрать тестовое ограничение и вручную обновить страницу. Проверить успешную карту, появление команд и их прежние ограничения. Проверить alert при ширине 390px и масштабе 200%, отсутствие перекрытий и горизонтальной потери текста. DOM role не объявлять полноценной проверкой screen reader.
- [x] Выполнить `git diff --check`, проверить LF у всех изменённых/новых текстовых файлов. Проверить `git diff` и `git status --short`; ничего не stage/commit/push.
- [x] Записать короткий implementation report: результат, реальные команды/выходы, браузерные evidence и оставшиеся ограничения. Сверить все строки приёмки дизайна с проверками. Agent memory не дублировать; repository-change ingest запускать только при действительно новом долговечном техническом знании, которого нет в существующей документации.

## Самопроверка плана

Каждая строка приёмки дизайна покрыта задачами 1–3. Событие готовности имеет одинаковое имя и тип у производителя и потребителя. Успешная empty-карта не открывает workspace-команды; late completion закрыт на стороне удалённого производителя. Отличены renderer error и legacy data error. Реальная browser/WebGL проверка отделена от unit mocks. Запрет Git-операций сохранён; шагов коммита нет.

План выполнен в текущем чате по поручению пользователя. Результаты и ограничения: [отчёт](2026-10-31-fe-02-map-initialization-implementation-report.md), [журнал](fe-02/execution-ledger.md). Browser toolbar zoom и screen reader не проверены; для 200% выполнена проверка reflow уменьшенным viewport.
