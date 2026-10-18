# День 11 — план реализации пользовательских команд

> **Для исполнителя:** применять `superpowers:executing-plans` либо, если пользователь выберет работу с субагентами, `superpowers:subagent-driven-development`. Выполнять задачи последовательно с проверками и отметками `- [x]`. Запрет AGENTS.md на `git add`, `git commit`, `git push` имеет приоритет над инструкциями skills.

**Цель:** добавить понятные команды и состояния редактора без повторных отправок и без расширения recovery scope.

**Архитектура:** отдельная панель над картой использует существующий Pinia store. Чистая проекция определяет доступность и сообщения; store владеет local draft, identity и запросами. Карта отражает тот же draft и те же блокировки.

**Стек:** Vue 3, TypeScript, Pinia, MapLibre, Vitest, Vue Test Utils; новых dependencies нет.

**Спецификация:** [2026-10-18-day-11-user-commands-design.md](2026-10-18-day-11-user-commands-design.md), принята пользователем 2026-10-18. Исполнитель читает её вместе с этим планом.

## Общие ограничения

- Все пользовательские тексты по-русски; кнопки «Сохранить», «Отменить», «Сбросить».
- Save без подтверждения. Cancel без подтверждения, с сохранением выбора и маркера. Подтверждения выбора на карте остаются.
- Revert только показывает сообщение; нет HTTP, baseline reset или нового commandId.
- Unknown, failed readback, stale не получают ручных recovery controls. Существующие автоматические повторы не меняются.
- Клавиатура — кнопки/диалоги; responsive — компьютер и планшет.
- Backend, API, migrations, dependencies и формат sessionStorage не меняются.
- Код и документы оставлять unstaged. Не создавать agent memory или ingest ради самого завершения задачи.
- До исполнения проверить `git status --short` и локальные инструкции; сохранять чужие изменения. Если нужна изоляция, применять worktree skill на этапе исполнения, не во время подготовки плана.

## Фокус проверки

1. Двойной submit до завершения Promise: одна identity и один initial PUT; проверяется задачами 1 и 3.
2. PUT success + GET failure либо stale + GET failure: честные разные сообщения без новой mutation; задачи 2 и 3.
3. Cancel после ранее сохранённого изменения: восстановить current, а не baseline, оставить маркер; задачи 1 и 4.
4. Смена actor/workspace и поздний callback: старый результат и вспомогательные сообщения не попадают в новый контекст; задачи 1, 3 и 4.
5. Recovery после refresh без исходного snapshot: не выдумывать no-op и не откатывать карту старым replay; задачи 1 и 2.

## Файлы и порядок

Все пути ниже относительны корню репозитория. Команды npm выполняются из `apps/frontend`.

| Задача | Файлы | Назначение |
| --- | --- | --- |
| 1 | `src/stores/workOrders.ts`, `src/stores/workOrders.edit.test.ts`, `src/stores/workOrders.recovery.test.ts` | Атомарный Cancel, guards, данные для сообщения no-op/отказа |
| 2 | новые `src/domain/workspaceCommandPresentation.ts`, `.test.ts` | Чистая проекция состояний панели |
| 3 | новые `src/components/WorkspaceEditCommands.vue`, `.test.ts`; `src/components/EditorWorkOrdersView.vue`, `.test.ts` | Панель, команды, сообщения, фокус |
| 4 | `src/components/WorkspaceLineInteraction.vue`, `.test.ts`; при необходимости `src/composables/map/useWorkspaceLineInteraction.ts` | Интеграция карты и доступность существующих диалогов |
| 5 | `docs/sprint_2/2026-10-18-day-11-user-commands-implementation-report.md`, `docs/sprint_2/evidence/day-11/`, README | Полная проверка и отчёт |

Пути `src/` в таблице находятся внутри `apps/frontend/`. Не менять остальные компоненты ради общего рефакторинга.

## Задача 1. Store: команды и доказательства результата

**Интерфейсы:** существующие `saveLocalDraft(): Promise<void>`, `cancelLocalEdit(): boolean`, `createLocalDraft(workspace, featureId, vertexIndex)` сохраняются. Добавить `discardLocalChangesKeepingSelection(): boolean`: сброс обычной dirty правки к current без снятия выбора. Добавить неперсистентные поля `submittedSourceGeometry: LineStringXY | null`, `rejectedCandidateGeometry: LineStringXY | null` и getter `saveChangedCurrent: boolean | null`. Последний сравнивает canonical result с исходным current той же текущей команды; `null` означает недостаток evidence. Данные не являются вторым активным draft.

- [x] В `workOrders.edit.test.ts` добавить failing tests: `discard restores current and keeps a clean selection`, `discard refuses stale and pending`, `rejects unchanged rejected candidate`, `allows corrected candidate`, `double save starts one request`. Использовать existing fixtures и deferred HTTP. Проверки: `localDraft.featureId` и vertex сохранены, candidate равен current, dirty false; baseline не подставлен; HTTP count при Cancel равен 0; blocked Cancel возвращает false без изменения draft; второй Save до ответа не увеличивает count.
- [x] Запустить `npm test -- src/stores/workOrders.edit.test.ts --maxWorkers=2`; подтвердить падения новых проверок по нужной причине.
- [x] Реализовать новый action атомарной заменой draft через `createLocalDraft` из activeWorkspace, с actor/access/recovery/phase guards и проверкой dirty. Оставить прежний `cancelLocalEdit` для существующих сценариев снятия выбора. Сбрасывать относящиеся к отменённому candidate сообщения/доказательства отказа.
- [x] При новой отправке фиксировать копию current target geometry до PUT, привязанную к текущей command identity/generation. При обычном терминальном отказе удерживать отправленный candidate для сравнения; новый Save того же candidate блокировать, исправленный допускать. Не менять retry прежней команды. Сбрасывать неперсистентные evidence при смене контекста/actor и новом намерении; refresh recovery не получает синтетический source snapshot.
- [x] Добавить в `workOrders.recovery.test.ts` проверки `no-op compares result with submitted current`, `restored receipt has unknown change classification`, `late callback cannot set evidence for another context`. Минимальные assertions: `saveChangedCurrent` false/true/null соответственно, map current всегда из GET. Воспроизвести FAIL, затем реализовать getter и lifecycle evidence.
- [x] Запустить `npm test -- src/stores/workOrders.edit.test.ts src/stores/workOrders.recovery.test.ts src/stores/workOrders.test.ts --maxWorkers=2`; ожидается PASS. Проверить отсутствие изменения структуры recovery record и retry schedule.

## Задача 2. Единая проекция панели

**Файлы:** создать `apps/frontend/src/domain/workspaceCommandPresentation.ts` и `.test.ts`.

**Интерфейсы:** экспортировать `WorkspaceCommandPresentation` с полями `canSave`, `canCancel`, `canRevert`, `busy` типа boolean, `statusText`, `qualityText` типа string и `severity: "info" | "success" | "error"`. Экспортировать `presentWorkspaceCommands(store: WorkspaceCommandState, actorCanEdit: boolean): WorkspaceCommandPresentation`. `WorkspaceCommandState` — type-only `Pick<ReturnType<typeof useWorkOrdersStore>, "activeWorkspace" | "localDraft" | "phase" | "recoveryRecord" | "commandResult" | "saveError" | "readbackError" | "storageError" | "editBlockReason" | "saveChangedCurrent" | "rejectedCandidateGeometry">`; runtime store не создаётся.

- [x] Добавить table-driven failing tests для строк матрицы спецификации: clean/dirty × persisted changeSet, sending/retry-wait/unknown/reading-current, rejected/stale/blocked. Проверить ровно русские тексты спецификации; Revert разрешён только при persisted changeSet и отсутствии блокировки. Actor без права редактирования не получает доступных команд.
- [x] Запустить `npm test -- src/domain/workspaceCommandPresentation.test.ts --maxWorkers=2`; ожидается FAIL до реализации.
- [x] Реализовать чистую функцию. Приоритет: access/context/storage/block → известный результат и readback error → активный запрос/ожидание → stale/rejected → обычный editing/idle. Не превращать все `reading-current` в подтверждённый успех. Применять `isLocalDraftDirty` и действующую `vertexMoveBlockReason` для допустимости candidate; не копировать серверную canonicalization.
- [x] Добавить assertions для пограничных случаев: success+failed GET содержит «Правка сохранена», stale+failed GET не содержит утверждения успеха; storage failure до PUT не называется unknown; no-op только при `saveChangedCurrent === false`; восстановленная квитанция с null evidence получает нейтральный success; неизвестный код не отображается буквально; qualityText остаётся при `basicValidation=null`.
- [x] Запустить тот же файл; ожидается PASS. Сверить все строки D11-01 и D11-07–12 со спецификацией.

## Задача 3. Панель команд и включение в Editor view

**Файлы:** новые `apps/frontend/src/components/WorkspaceEditCommands.vue`, `.test.ts`; изменяемые `EditorWorkOrdersView.vue`, `.test.ts` рядом с ними.

**Интерфейсы:** компонент без props использует существующие auth/workOrders stores и `presentWorkspaceCommands`. Команды вызывают `saveLocalDraft` и `discardLocalChangesKeepingSelection`. Revert меняет только локальное пояснение панели. Этот текст сбрасывается при смене workspace/actor и новом пользовательском действии; он не заменяет основную ошибку. Заголовок панели имеет `tabindex="-1"` как цель восстановления фокуса.

- [x] Добавить failing component tests с реальным Pinia: `saves immediately and prevents duplicate activation`, `cancels without dialog and keeps selection`, `revert only explains unavailability`, `shows distinct recovery messages without recovery buttons`. Проверять HTTP count с deferred promises, отсутствие диалога Cancel, отсутствие PUT от Cancel/Revert, отсутствие retry/readback controls.
- [x] Запустить `npm test -- src/components/WorkspaceEditCommands.test.ts --maxWorkers=2`; ожидается FAIL.
- [x] Реализовать компонент с native `button type="button"`, согласованными подписями, текстами и disabled; одна status live region, отдельное пояснение качества. Во время active request показать индикатор ожидания без процентов; при readbackError `busy=false`, ограничения сохраняются. «Сбросить» имеет доступное пояснение назначения.
- [x] Добавить failing focus/context tests: explicit Cancel переводит фокус на heading при отключении кнопки; async status не крадёт фокус из другого control; старое пояснение Revert исчезает при смене actor/workspace. Реализовать фокус только в ответ на явное действие/закрытие диалога, не общим watcher каждого статуса.
- [x] В `EditorWorkOrdersView.test.ts` добавить проверку наличия панели только при active workspace и её DOM-порядка до карты. Запустить тест до изменения view; затем подключить панель перед MapView. CSS: flex-wrap для команд, min-width:0, перенос длинного текста, отсутствие absolute overlay; карта сохраняет доступную область.
- [x] Запустить `npm test -- src/components/WorkspaceEditCommands.test.ts src/components/EditorWorkOrdersView.test.ts --maxWorkers=2`; ожидается PASS. Enter/Space дополнительно проверяются в браузере, поскольку jsdom не заменяет native keyboard activation.

## Задача 4. Карта, блокировки и существующие диалоги

**Интерфейсы:** использовать тот же store; не добавлять независимый selected feature. Чистый local draft после Cancel удерживает выбор/marker, отсутствие draft после успешного Save убирает их. `available` composable уже исключает stale/recovery; сохранить этот guard.

- [x] Расширить `WorkspaceLineInteraction.test.ts`: Cancel панели после persisted edit возвращает marker к current, не baseline; после success/readback marker отсутствует; stale/unknown/readbackError запрещают click/drag/discard через карту. Использовать совместный mount панели и interaction с existing map mock и реальным store. До правок подтвердить FAIL новых нарушенных сценариев; уже проходящие regression cases не ломать искусственно.
- [x] Добавить проверки диалога: Tab/Shift+Tab удерживаются внутри, Escape сохраняет candidate, focus возвращается на доступный инициатор либо заголовок панели; фон не принимает взаимодействие при открытом modal confirmation. Список неоднозначного выбора остаётся nonmodal.
- [x] Исправить только выявленные разрывы. Для existing modal confirmation использовать native `<dialog>`/`showModal()` и `cancel` handler, сохранив текущий safe-first порядок кнопок; focus fallback на общий heading панели. В jsdom добавить локальный dialog stub лишь для API, не объявляя его доказательством реальной inertness. Проверку фона завершить в браузере.
- [x] Запустить `npm test -- src/components/WorkspaceLineInteraction.test.ts src/components/WorkspaceEditCommands.test.ts src/map/workspace-layers.test.ts src/domain/workspaceLineInteraction.test.ts --maxWorkers=2`; ожидается PASS. Не добавлять keyboard movement вершины.

## Задача 5. Итоговая проверка и отчёт

**Результат:** проверяемый UI и отчёт с фактическими результатами, без заявлений о выполнении Дня 12.

- [x] Выполнить полный `npm test -- --maxWorkers=2`; ожидаются PASS всех suites. Зафиксировать фактические числа, не копировать результаты Дня 10.
- [x] Выполнить `npm run lint`, затем `npm run build`; ожидается exit 0. Existing bundle warning отделить от ошибки. Не запускать тяжёлые проверки одновременно, учитывая прошлые import timeouts.
- [x] Выполнить `git diff --check`; ожидается exit 0 без диагностик. Проверить diff на отсутствие backend/dependency/migration изменений и нежелательных edits чужой работы.
- [x] Проверить demo в браузере: выбор → движение → Cancel без диалога → сохранённый выбор; новое движение → Save → обновлённая карта без marker; при persisted changeSet «Сбросить» только сообщает о недоступности. Прямые подтверждения карты сохраняются. Не выдавать component fixtures сетевых ошибок за реальный сбой сервера.
- [ ] Выполнить review на 1440×900, 1024×768 и 768×1024 при 100% и 200% масштабе. Проверить native Enter/Space, Tab, Escape, focus после отключения кнопки, inert background modal, прокрутку и отсутствие перекрытия карты. Сохранить снимки в `docs/sprint_2/evidence/day-11/`.
- [x] Если runtime недоступен, явно указать непроведённую browser-проверку и её причину; не объявлять D11-15 выполненным. Не удалять demo volumes ради запуска. Зафиксировать изменение demo geometry после Save: Revert UI в этом дне не реализован, автоматический сброс БД не выполнять.
- [x] Провести итоговое review по D11-01–15 и пяти пунктам фокуса проверки. Исправить найденные нарушения с соответствующей регрессией; повторять только затронутые проверки, расширяя прогон при обоснованном риске.
- [x] Создать `docs/sprint_2/2026-10-18-day-11-user-commands-implementation-report.md` с фактическими изменениями, проверками, ограничениями, состоянием demo и ссылками на evidence. Обновить README и статус плана. Изменения оставить unstaged, без Git mutation commands.

## Самопроверка плана

Покрытие: разделы спецификации 3–4 → задачи 2–3; раздел 5 → 1, 3–4; раздел 6 → 3–5; разделы 7–8 → все задачи. Review Focus распределён по tests задач 1–4. Runtime/browser evidence отделён от unit tests. Интерфейсы проекции используют поля, определённые задачей 1; формат recovery не расширяется. Реализация и проверки отражены в отчёте; отметки выше учитывают итог, а не первоначальный статус планирования.

## Передача на исполнение

Пользователь поручил реализацию; выполнено последовательно в этом чате. Код реализован, итоговое независимое review и автоматические проверки проведены. Незакрытая часть приёмки — настоящий browser zoom 200%; вместо него выполнен reflow на эквивалентных CSS viewport. Подробности проверки: [отчёт реализации](2026-10-18-day-11-user-commands-implementation-report.md).
