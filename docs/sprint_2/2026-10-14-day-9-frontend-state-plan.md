# День 9 — план реализации frontend contracts и state

> **Для исполняющего агента:** использовать `superpowers:executing-plans` либо `superpowers:subagent-driven-development` после выбора пользователем способа исполнения. Выполнять задачи последовательно с проверками. Правило репозитория запрещает `git add`, `git commit`, `git push`; шагов commit в этом плане нет.

**Цель:** реализовать проверяемый через API/store цикл локальной правки линии, Save, неизменного retry и refresh recovery.

**Архитектура:** `workOrders` — единственный владелец current/draft/pending/result. Contracts/guards, sessionStorage и retry schedule вынесены в небольшие модули; после success актуальное состояние получается через workspace GET.

**Стек:** существующие TypeScript, Vue, Pinia, Axios, Vitest/jsdom. Новые dependencies не добавляются.

**Спецификация:** [2026-10-14-day-9-frontend-state-design.md](2026-10-14-day-9-frontend-state-design.md), принята пользователем 2026-10-14.

**Статус:** исполнение разрешено пользователем 2026-10-15, inline. Задачи 1–6 выполнены; задача 7 — итоговая проверка и review — в работе.

## Общие ограничения

- До работы прочитать AGENTS.md, memory protocol и спецификацию. Использовать подходящий существующий checkout; новые worktree нужны только при обоснованной необходимости изоляции на этапе исполнения.
- Изменять frontend и документацию результата, не backend/API/migrations. Legacy Polygon flow не переносить в utility store.
- Opaque token, неизменяемые commandId/payload при retry, одна линия/внутренняя вершина, server canonicalization и baseline из backend.
- Перед первым PUT обязательна успешная запись recovery record. Unknown, sending, readback и storage/access/protocol block запрещают новые mutations.
- После initial Save — до 5 дополнительных PUT, после refresh — до 5 PUT; задержки `0, 2000, 5000, 10000, 20000` ms после предыдущей неудачи. Ручной retry — один PUT. HTTP timeout остаётся 30000 ms.
- Сначала failing test с ожидаемой причиной, затем минимальная реализация, затем passing targeted suite. Не считать случайную ошибку окружения доказательством RED.
- UI controls/drag/Revert action, relogin resume, multi-workspace queue и browser/backend restart остаются последующим задачам. Guards и state reasons входят сейчас.
- Не запускать repository-change ingest по факту завершения плана; отдельно оценить наличие нового durable технического знания, ещё не сохранённого в документах.

## Фокус review

1. GET, начавшийся до PUT, завершается после post-success GET — старый snapshot не откатывает current; тест задачи 5.
2. Страница закрыта после storage write, но до отправки — восстановление использует прежнее намерение; тест задачи 5.
3. Записать success в storage не удалось — результат известен в памяти, но новая команда не перезаписывает record; тест задачи 4.
4. 401 interceptor сбрасывает store раньше catch PUT — stale callback не возобновляет отправку от другого actor; тест задачи 6.
5. На retry приходит REQUEST_VALIDATION_ERROR либо access error — это не доказательство отсутствия прежнего commit; тест задачи 4.

## Карта файлов и зависимости

Все пути далее относительно `apps/frontend/`, если не указано иное.
Все команды npm в задачах выполняются с рабочим каталогом `apps/frontend`; не менять существующий package manager/lockfile.

| Файл | Ответственность |
| --- | --- |
| `src/contracts/work-orders.ts` | Расширенный workspace contract |
| `src/contracts/workspace-edit.ts` | Типы request/result/local draft/recovery и runtime guards |
| `src/api/workOrders.ts` | Один geometry PUT, проверка PUT/GET response |
| `src/domain/workspaceDraft.ts` | Чистые операции локальной правки |
| `src/stores/workspaceRecoveryStorage.ts` | Versioned record, явные storage errors |
| `src/stores/workspaceRetry.ts` | Ограниченное расписание и отменяемое ожидание |
| `src/stores/workOrders.ts` | Единственный владелец state, orchestration и guards |
| `src/stores/auth.ts` | Остановка recovery при identity/access transition |

Задачи 1 → 2 → 3 → 4 → 5 → 6 → 7 выполняются последовательно: storage/retry/state не разрабатываются как независимые владельцы одного состояния. Для каждого нового модуля создаётся соседний `.test.ts`.

## Задача 1. Контракты и один запрос API

**Создать:** `src/contracts/workspace-edit.ts`, `src/contracts/workspace-edit.test.ts`, `src/api/workOrders.test.ts`.

**Изменить:** `src/contracts/work-orders.ts`, `src/api/workOrders.ts`; workspace fixtures в `src/stores/workOrders.test.ts`, `src/map/workspace-layers.test.ts`, `src/components/MapView.test.ts`, `src/components/EditorWorkOrdersView.test.ts`, `src/components/WorkspaceDetailsPanel.test.ts`.

**Интерфейсы:** экспортировать `LineStringXY`, `BasicValidation`, `WorkspaceChangeSet`, `GeometrySaveRequest`, `GeometrySaveResult`, `SaveTarget={workOrderId,editVersionId,featureId}`, `ProtocolError`. `saveFeatureGeometry(target: SaveTarget, request: GeometrySaveRequest): Promise<GeometrySaveResult>`; `parseGeometrySaveResult(value: unknown, target: SaveTarget, commandId: string): GeometrySaveResult`; `parseWorkspaceResponse(value: unknown, workOrderId: string, editVersionId: string): WorkspaceResponse`. Парсеры возвращают проверенное значение либо бросают ProtocolError. `fetchWorkspace` использует второй parser; list/open contracts сохраняются.

- [x] Добавить failing tests `sends_exact_geometry_request_once`, `preserves_opaque_token`, `rejects_mismatched_command_or_feature`, `rejects_inconsistent_workspace_summary`. Пример ключевых assertions:

```ts
expect(http.put).toHaveBeenCalledTimes(1);
expect(http.put).toHaveBeenCalledWith(
  `/api/v1/work-orders/${target.workOrderId}/edit-versions/${target.editVersionId}/features/${target.featureId}/geometry`,
  request,
);
expect(() => parseGeometrySaveResult(wrongIdResult, target, request.commandId))
  .toThrow(ProtocolError);
```

- [x] Выполнить `npm test -- src/contracts/workspace-edit.test.ts src/api/workOrders.test.ts`; подтвердить отсутствие нужной реализации как причину FAIL.
- [x] Реализовать типы и guards по разделу 3 спецификации: XY finite numbers/ranges, UUID commandId, opaque nonempty token, обязательные nullable поля, соответствие target. Workspace сохраняет Point/Polygon и другие существующие geometry types. Проверять все новые contract fields, а не использовать `as` вместо runtime validation.
- [x] Добавить PUT client; не изменять общий Axios timeout/interceptors. Обновить перечисленные fixtures обязательными полями; для payload, проходящих UUID guard, использовать реальные UUID в тестах.
- [x] Повторить targeted tests и `npm run typecheck`; ожидается PASS/exit 0. Проверить отсутствие новых fields в OpenEditVersionResponse.

## Задача 2. Local draft и Cancel

**Создать:** `src/domain/workspaceDraft.ts`, `src/domain/workspaceDraft.test.ts`, `src/stores/workOrders.edit.test.ts`.
**Изменить:** `src/contracts/workspace-edit.ts`, `src/stores/workOrders.ts`.

**Интерфейсы:** `WorkspaceLocalDraft={featureId,vertexIndex,sourceGeometry,sourceToken,candidateGeometry}`; `createLocalDraft(workspace: WorkspaceResponse, featureId: string, vertexIndex: number): WorkspaceLocalDraft`; `updateLocalVertex(draft: WorkspaceLocalDraft, xy: [number,number]): WorkspaceLocalDraft`; `isLocalDraftDirty(draft: WorkspaceLocalDraft): boolean`. Непригодная feature/index/форма бросает `DraftInputError` с code. Store actions: `beginLocalEdit(featureId: string, vertexIndex: number): boolean`, `moveLocalVertex(xy: [number,number]): boolean`, `cancelLocalEdit(): boolean`; отказ возвращает false и устанавливает причину в `editBlockReason`. Добавить localDraft, commandResult и phase; исходное состояние без редактирования `idle`.

- [x] Написать failing tests `does_not_mutate_current`, `cancel_does_not_call_api`, `dirty_is_relative_to_current`, `rejects_endpoint_or_other_changed_feature`. Проверить независимые копии coordinates и отсутствие HTTP после Cancel.
- [x] Запустить `npm test -- src/domain/workspaceDraft.test.ts src/stores/workOrders.edit.test.ts`; зафиксировать ожидаемый FAIL.
- [x] Реализовать чистые функции и store actions. Если changeSet непустой, использовать его featureId/vertexIndex; чистая версия допускает подходящую внутреннюю вершину выбранной existing LineString. Не округлять координаты, не добавлять spatial engine.
- [x] Проверить изменение только выбранной вершины, неизменность source/current и отсутствие `seed` координат. Повторить targeted tests до PASS.

## Задача 3. Recovery record и расписание

**Создать:** `src/stores/workspaceRecoveryStorage.ts`, `src/stores/workspaceRecoveryStorage.test.ts`, `src/stores/workspaceRetry.ts`, `src/stores/workspaceRetry.test.ts`.
**Изменить:** `src/contracts/workspace-edit.ts`.

**Интерфейсы storage:** `PendingGeometryCommand={actorId,target:SaveTarget,request:GeometrySaveRequest}`. `WorkspaceRecoveryRecord` имеет `schemaVersion:1`, `command:PendingGeometryCommand` и discriminated `state`: `unknown`, `succeeded`, `rejected`, `blocked`. Succeeded содержит проверенный GeometrySaveResult; rejected — status/code/message/correlationId и признак необходимости readback; blocked — причину `access|protocol|identity` и последний известный результат при наличии. Тип причины не подменяет факт terminal result.

`readRecoveryRecord(actorId: string): RecoveryReadResult` с вариантами `empty|record|invalid|unavailable`; `writeRecoveryRecord(record: WorkspaceRecoveryRecord): boolean`; `removeRecoveryRecord(actorId: string, commandId: string): boolean`; `true` означает успех, `false` — отказ операции. Ключ `geoservice:workspace-recovery:v1:<actorId>`. Один активный record на actor в данной вкладке; чтение чужого actor не выполняется. Remove сверяет identity, не удаляя новую команду.

**Интерфейсы retry:** `AUTO_RETRY_DELAYS_MS=[0,2000,5000,10000,20000]`; `waitForRetry(delayMs: number, signal: AbortSignal): Promise<boolean>` возвращает false при отмене. Helper не вызывает API, не владеет Pinia state; store отменяет ожидание через AbortController.

- [x] Написать failing storage tests на roundtrip всех фаз, unavailable storage, malformed JSON/неподдерживаемую версию, actor mismatch и невозможность удалить другой commandId. Assert: `writeRecoveryRecord(record).ok === false` при setItem exception; invalid record не исчезает.
- [x] Написать fake-timer tests для точных задержек и отмены; assert список равен `[0,2000,5000,10000,20000]`, отменённое ожидание возвращает false и не оставляет активного таймера.
- [x] Выполнить `npm test -- src/stores/workspaceRecoveryStorage.test.ts src/stores/workspaceRetry.test.ts`; подтвердить FAIL.
- [x] Реализовать codec с проверками задачи 1 и явными результатами ошибок; не сохранять credentials, не подавлять ошибки как успешную запись. Реализовать отменяемый wait без интервалов/polling.
- [x] Повторить targeted tests до PASS. Проверить, что record сохраняет исходный token/geometry независимо от нового workspace.

## Задача 4. Save orchestration, результат и ошибки

**Изменить:** `src/stores/workOrders.ts`, `src/stores/workOrders.edit.test.ts`, `src/contracts/workspace-edit.ts`.
**Создать:** `src/stores/workspaceSaveErrors.ts`, `src/stores/workspaceSaveErrors.test.ts`.

**Интерфейсы:** `classifySaveFailure(error: unknown, hadUnknownOutcome: boolean): SaveFailureDisposition` с категориями `retryableUnknown|domainRejected|stale|blocked`; blocked сохраняет конкретную причину и не означает rollback. Store: `saveLocalDraft(): Promise<void>`, `retryPendingSave(): Promise<void>`, `refreshCurrentWorkspace(): Promise<void>`. State: `pendingCommand`, `commandResult`, `phase`, `editBlockReason`, `saveError`, `readbackError`, `storageError`. Phase различает `idle|editing|sending|retry-wait|unknown|reading-current|rejected|stale|blocked`. Async runtime generation/AbortController не персистятся; для Pinia instances использовать отдельный runtime на экземпляр, не общий global timer.

- [x] Добавить failing tests `storage_write_precedes_put`, `storage_failure_sends_nothing`, `success_reads_workspace`, `readback_failure_does_not_retry_put`, `success_storage_failure_blocks_next_save`, `retry_format_or_access_error_does_not_prove_old_failure`.
- [x] Проверить assertions: при setItem failure PUT count 0; после success + GET failure commandResult содержит success, новый Save запрещён; повтор refreshCurrentWorkspace увеличивает GET count, не PUT count.
- [x] Выполнить `npm test -- src/stores/workOrders.edit.test.ts src/stores/workspaceSaveErrors.test.ts`; подтвердить FAIL.
- [x] Реализовать создание `crypto.randomUUID()` и независимого request snapshot, обязательный storage write, отправку, runtime result guard, сохранение success phase, readback и cleanup. На success current заменяется только валидным GET; receipt не патчит карту.
- [x] Реализовать error dispositions по разделу 8 спецификации. Для REQUEST_VALIDATION_ERROR учитывать hadUnknownOutcome; stale удерживает candidate и делает GET без reapply; access/reused/protocol блокируют новую mutation. Обычный terminal rejection не запускается заново автоматически.
- [x] Реализовать retry cleanup/readback при storage failures без нового PUT. Успех в памяти не превращается в unknown из-за storage exception; новая команда не перезаписывает старый record.
- [x] Повторить targeted tests до PASS; дополнительно проверить no-op и equality token без числового сравнения.

## Задача 5. Автоматические серии и восстановление после refresh

**Изменить:** `src/stores/workOrders.ts`, `src/stores/workOrders.edit.test.ts`.
**Создать:** `src/stores/workOrders.recovery.test.ts`.

**Интерфейсы:** `restorePendingSave(): Promise<void>` вызывается из существующего успешного workspace restore flow; не создаёт новую EditVersion. Использует интерфейсы задач 1/3/4. `retryPendingSave` всегда одиночный. Общий внутренний исполнитель получает явный режим `initial|restore|manual`, а не вычисляет лимит из количества errors.

- [x] Добавить failing fake-timer tests `initial_has_five_additional_attempts`, `restore_has_five_total_attempts`, `manual_retry_is_single`, `terminal_response_stops_schedule`. Assert при сплошных timeout: 6 PUT вместе с initial, 5 при restore, 1 при manual; каждый request body идентичен.
- [x] Добавить deferred tests `refresh_before_first_put_uses_stored_intent`, `confirmed_success_refresh_uses_get_only`, `old_get_cannot_overwrite_post_save_readback`, `old_replay_receipt_does_not_replace_new_current`. Проверить commandResult A и workspace B отдельно.
- [x] Выполнить `npm test -- src/stores/workOrders.recovery.test.ts`; подтвердить ожидаемый FAIL.
- [x] Подключить schedule к retryableUnknown: ждать окончания запроса, затем delay; проверять generation/actor/target до и после каждого await. Исчерпание оставляет unknown, отмена останавливает серию без очистки identity.
- [x] Подключить recovery после auth/list/workspace restore: confirmed success/rejection не вызывает PUT, unknown запускает restore-series, blocked/invalid не возобновляется автоматически. Свежий token не меняет pending request.
- [x] Инвалидировать старые workspace reads при начале Save/readback и использовать существующие sequence guards совместно с поколением mutation. GET до Save не может выиграть гонку с новым snapshot.
- [x] Повторить targeted tests задач 4–5 до PASS. Не использовать реальный sleep для проверок 30-секундных timeout.

## Задача 6. Auth/reset и безопасные переходы

**Изменить:** `src/stores/workOrders.ts`, `src/stores/auth.ts`, `src/stores/auth.test.ts`, `src/stores/workOrders.test.ts`, `src/stores/workOrders.recovery.test.ts`.
**Проверить без расширения UI scope:** `src/api/http.test.ts`, `src/components/EditorWorkOrdersView.test.ts`.

**Интерфейсы:** `suspendWorkspaceRecoveryForAccessLoss(): void` вызывается до очистки actor при runtime 401/logout/user change и initial auth failure с возможным recovery. Останавливает runtime, удерживает record, помечает access block когда actor известен. `canLeaveWorkspace` getter; существующие select/clear/reopen действия не выполняют destructive reset при localDraft/pending/readback и выставляют editBlockReason. Auth reset остаётся принудительным и скрывает private state.

- [x] Написать failing tests `interceptor_reset_before_save_catch_keeps_record`, `new_actor_never_receives_old_payload`, `stale_timer_cannot_use_new_auth`, `dirty_navigation_is_blocked`, `cancel_allows_navigation`, `assignment_loss_hides_workspace_but_keeps_pending`.
- [x] Assert отсутствие PUT после reset и смены пользователя даже после всех timers; чужая geometry не появляется в store; unknown record не удаляется; list reload не очищает intent в обход guard.
- [x] Выполнить `npm test -- src/stores/auth.test.ts src/stores/workOrders.test.ts src/stores/workOrders.recovery.test.ts src/api/http.test.ts`; подтвердить FAIL на новом поведении.
- [x] Разделить forced auth/access clearing и пользовательский navigation reset. Сначала остановить отправку/таймеры и попытаться записать access block, затем скрыть private state. Storage failure сохраняет block в памяти; не выдавать очистку за безопасное продолжение. При недоступности storage на restore отправки нет.
- [x] Сохранить initial successful auth restore для того же actor как обычный refresh path; обнаруженная потеря доступа не превращается в auto resume. Не реализовывать UI relogin resume или выбор save/discard/stay.
- [x] Проверить все clear/open/reopen/list/restore paths. Повторный выбор того же workspace без очистки допустим; неизменённые list/open flows работают по-прежнему.
- [x] Повторить targeted tests до PASS, включая `src/components/EditorWorkOrdersView.test.ts` для существующей точки входа restore.

## Задача 7. Полная проверка и отчёт

**Создать при исполнении:** `docs/sprint_2/2026-10-15-day-9-frontend-state-implementation-report.md`.
**Обновить при исполнении:** `docs/sprint_2/README.md`, статусы плана после фактического прохождения шагов.

- [x] Сопоставить D9-01..D9-16 со suites задач 1–6; в отчёте указать test names для каждой строки, без объявления UI/restart завершёнными.
- [x] Из `apps/frontend` выполнить по отдельности `npm test`, `npm run typecheck`, `npm run lint`, `npm run build`. Каждый должен завершиться exit 0; failures расследовать, не маскировать изменением assertions.
- [x] Проверить изменённые frontend файлы проектным Prettier, используя конкретные paths, и выполнить `git diff --check` из корня. Не форматировать весь репозиторий ради этой задачи.
- [x] Провести review state transitions, retries, actor isolation и матрицы приёмки в выбранном пользователем режиме исполнения. Исправления повторно проверять затронутыми suites; полный набор повторять при изменениях, которые обосновывают регрессию.
- [x] Сохранить фактические команды/результаты, известные ограничения и границы следующего этапа в отчёте. Не создавать completion memory и не запускать ingest автоматически.
- [x] Оставить все изменения unstaged для пользователя. Сообщить перечень результатов и ограничений, без git add/commit/push.

## Самопроверка плана

Покрытие спецификации: contracts — задача 1; роли данных/local draft — задача 2; recovery record — задача 3; Save/canonical/error transitions — задача 4; retries/refresh/races — задача 5; access/navigation — задача 6; полная матрица и регрессия — задача 7. Пять review risks имеют владельцев и тесты. Интерфейсы задач согласованы; новые helper types определяются в указанных модулях, state не дублируется между stores. Фактические проверки выполнены: 30 suites, 216 tests, typecheck, lint и build PASS. См. отчёт реализации.

## Передача на исполнение

Пользователь разрешил реализацию 15 октября 2026 года. Выполнено inline исполнение через executing-plans и итоговое независимое review с одним проходом исправлений. Все семь задач завершены; изменения оставлены unstaged. Итоги: [отчёт реализации](2026-10-15-day-9-frontend-state-implementation-report.md).
