# S2-X01 — план реализации независимого восстановления

> **Для исполнителя:** обязательный навык — `superpowers:executing-plans` либо `superpowers:subagent-driven-development`, в зависимости от выбранного пользователем способа исполнения. Выполнять задачи по шагам, отмечая checkboxes. Запрет `AGENTS.md` на `git add`, `git commit`, `git push` имеет приоритет; вместо commit оставлять проверенные изменения unstaged.

**Цель:** восстановление нескольких независимых Save/Revert после потери ответа и закрытия браузера без повторной mutation, подмены current и скрытой потери local draft при управляемой навигации.

**Архитектура:** выбран вариант C. Новый `useWorkspaceRecoveryStore` единолично владеет отправленными намерениями, IndexedDB обеспечивает долговременные записи, `useWorkOrdersStore` владеет workspace/local draft/navigation. Явный bridge передаёт readback без зависимости recovery store от work orders store.

**Технологии:** существующие Vue/Pinia/TypeScript, IndexedDB, Vitest/Vue Test Utils, MapLibre, Playwright в `infra/m4`, pytest/DB runner. Backend-контракт сохраняется.

**Спецификация:** [2026-10-23-s2-x01-recovery-design.md](2026-10-23-s2-x01-recovery-design.md), принята пользователем 2026-10-23. [Анализ и ответы](2026-10-22-s2-x01-recovery-analysis.md).

Статус: выполнено и проверено 2026-10-23; итог — [отчёт](2026-10-23-s2-x01-recovery-implementation-report.md). Checkboxes включают выполненные шаги и эквивалентные проверки, уточнённые в журнале исполнения. План — единый: storage, recovery, auth и workspace образуют одну цепочку безопасности, не независимые продукты.

## Общие ограничения

- Ключ `(actorId, workOrderId, editVersionId)`; одна незавершённая команда на версию, без продуктового лимита независимых контекстов.
- PUT только после завершения транзакции записи. Retry не меняет actor/target/CommandId/token/geometry.
- Первоначальный PUT плюс до пяти повторов; восстановление/ручная серия — пять попыток с задержками `[0, 2000, 5000, 10000, 20000]` мс. Два фоновых recovery HTTP-запроса одновременно; retry-wait освобождает слот.
- Known outcome → только оставшийся GET; replay geometry не становится current. Новые mutations неизвестной версии запрещены, независимых разрешены.
- Нет persisted `OutcomePending`, новых backend endpoint/migrations, polling, offline editing, history UI, TTL cleanup, baseline repair или координации нескольких вкладок одного наряда.
- Сессия/доступ проверяются перед HTTP и применением ответа; после обнаруженной потери доступа — подтверждение каждого наряда отдельно. Чужие материалы не отображаются.
- Stale-сравнение живёт в памяти при переключении; после завершённого readback может исчезнуть при refresh. Перенос candidate не добавляется.
- Точные тексты: «Выход не отменяет отправленную команду»; «Отказаться от попытки»; «Попытка будет удалена. Затем можно заново изменить актуальную линию».
- UTF-8/LF для текста, CRLF только `.cmd`/`.bat`. Не менять календарь. Не редактировать read-only reference repository.
- Новые отчёты/evidence — в `docs/sprint_2/`; результаты прошлых дней не выдавать за новые. Никаких секретов в evidence.

## Особое внимание при review

1. Поздний 401 запроса actor A после входа B не должен разлогинить B — тест задачи 5.
2. Смена actor во время IndexedDB commit не должна привести к PUT от новой сессии — тест задачи 3.
3. Crash между импортом v1 и удалением старой записи не должен воскресить уже завершённую команду — тесты задач 2 и 8.
4. Более новый обычный GET и старый recovery GET одного контекста не должны переставить current — тест задачи 4; важен общий clock, а не два независимых счётчика.
5. Logout из B при stale-материале A должен явно разрешить потерю материала A, а исход success A с ошибкой GET не должен превратиться в unknown — тесты задач 5–6.

## Файлы и ответственность

Все пути далее относительно `C:/Repositories/geoservice`.

| Файл/группа | Изменение и ответственность |
| --- | --- |
| `apps/frontend/src/contracts/workspace-recovery.ts`, `.test.ts` | Создать: ключи, schema v2, runtime views и bridge |
| `apps/frontend/src/contracts/workspace-edit.ts` | Сохранить wire types/parsers; v1 выделить как legacy type, не менять HTTP shape |
| `apps/frontend/src/stores/workspaceRecoveryStorage.ts`, `.test.ts` | Добавить IndexedDB adapter; временные legacy exports удалить после переключения потребителей в задаче 4 |
| `apps/frontend/src/stores/workspaceRecoveryMigration.ts`, `.test.ts` | Создать: v1 import и журнал незавершённого импорта |
| `apps/frontend/src/stores/workspaceRecoveryScheduler.ts`, `.test.ts` | Создать: лимит фоновых HTTP, справедливая очередь, отмена |
| `apps/frontend/src/stores/workspaceRecovery.ts`, `.test.ts` | Создать: единственный владелец команд и execution lifecycle |
| `apps/frontend/src/stores/workspaceRetry.ts`, `workspaceSaveErrors.ts` | Переиспользовать интервалы и классификацию; новые access distinctions только с тестами |
| `apps/frontend/src/stores/workOrders.ts`, `.test.ts`, `.edit.test.ts`, `.recovery.test.ts` | Перенос владения, context maps, bridge, общий clock, Revert/navigation guards |
| `apps/frontend/src/domain/workspaceNavigation.ts`, `.test.ts` | Создать: типизированный запрос/согласие перехода |
| `apps/frontend/src/stores/auth.ts`, `.test.ts`, `apps/frontend/src/api/http.ts`, `.test.ts` | Session epoch, остановка/подтверждение, защита поздних 401 |
| `apps/frontend/src/domain/workspaceCommandPresentation.ts`, `.test.ts` | Selectors и честные сообщения |
| `apps/frontend/src/components/WorkspaceRecoveryList.vue`, `.test.ts` | Создать: список recovery текущего actor |
| `apps/frontend/src/components/WorkspaceStaleComparison.vue`, `.test.ts` | Создать: source/candidate/current и read-only preview |
| `apps/frontend/src/components/WorkspaceNavigationDialog.vue`, `.test.ts` | Создать: управляемые переходы и сохранность материала |
| `apps/frontend/src/components/WorkspaceEditCommands.vue`, `.test.ts`, `EditorWorkOrdersView.vue`, `.test.ts`, `apps/frontend/src/App.vue`, `.test.ts` | Подключение новых actions и диалогов |
| `apps/frontend/src/composables/map/useWorkspaceLineInteraction.ts`, `apps/frontend/src/components/WorkspaceLineInteraction.vue`, `.test.ts` | Изолированный preview без подмены workspace; при необходимости отдельный map helper |
| `apps/frontend/src/test/workspaceEditFixture.ts`, новый `recoveryStorageFixture.ts` | Контексты A/B/C и управляемый adapter для отказов |
| `infra/m4/recovery.spec.ts`, новые `s2-x01-storage.spec.ts`, `s2-x01-recovery.spec.ts`, `s2-x01-fixture.ts`; `playwright.config.ts`, `run.mjs`, `README.md` | Реальный browser storage, restart браузера, множество нарядов, account switching |

Не переносить весь `workOrders.ts` в новый файл механически: recovery store не владеет картой, selection, подтверждением Revert или обычным local draft.

## Контракты между задачами

Имена ниже фиксируют внутренние интерфейсы плана. Wire types `PendingGeometryCommand`, `GeometrySaveResult`, `SaveRejection`, `WorkspaceResponse`, `LineStringXY` берутся из существующих contracts.

```ts
type RecoveryKey = string; // JSON.stringify([actorId, workOrderId, editVersionId])
type RecoveryContext = { actorId: string; workOrderId: string; editVersionId: string };
type RecoverySource = { geometry: LineStringXY; vertexIndex: number } | null;
type RecoveryOutcome =
  | { kind: "unknown" }
  | { kind: "succeeded"; result: GeometrySaveResult }
  | { kind: "rejected"; error: SaveRejection; needsReadback: boolean };
type RecoveryRecordV2 = {
  schemaVersion: 2; key: RecoveryKey; revision: number;
  command: PendingGeometryCommand; source: RecoverySource;
  outcome: RecoveryOutcome; readbackRequired: boolean;
  blocks: Array<"access" | "protocol" | "identity" | "storage">;
  requiresAccessConfirmation: boolean;
};
type RecoverySession = { actorId: string; epoch: number; canEdit: boolean };
type ReadTicket = { key: RecoveryKey; sessionEpoch: number; generation: number };
type RecoveryApplyResult = "applied" | "superseded" | "blocked";
type RecoveryStartResult = "started" | "blocked";
type RecoveryCompletion = { record: RecoveryRecordV2; sessionEpoch: number };
type RecoveryStorageLoad = {
  records: RecoveryRecordV2[];
  invalid: Array<{ key: RecoveryKey | null; reason: string }>;
};
type RecoveryHost = {
  session(): RecoverySession | null;
  canAccess(context: RecoveryContext): boolean;
  reserveRead(context: RecoveryContext): ReadTicket;
  applyRead(ticket: ReadTicket, workspace: WorkspaceResponse): RecoveryApplyResult;
  complete(completion: RecoveryCompletion): void;
  interrupted(key: RecoveryKey, reason: "unknown" | "readback" | "rejected" | "access"): void;
};
```

`readbackRequired` сохраняет незавершённость согласования current; при success/stale true, при другом доказанном terminal rejection без обязательного GET false. Не сохранять false для success/stale до принятия readback и завершения cleanup: после перезапуска память current отсутствует. `blocks` — независимые причины, подтверждение доступа снимает только access. `revision` — локальный CAS записи, не `draftVersionToken` сервера. Legacy source=null разрешён явно; новые команды без source не создаются.

`RecoveryHost.canAccess` опирается на актуальный список назначений/роль, не заменяет серверную авторизацию. Невозможность загрузить список из-за сети не является доказательством отзыва назначения: auto-start ждёт проверки, unknown не удаляется. Все runtime host bindings снимаются при dispose; новый binding не создаёт вторую очередь.

## Задача 1. Контракты, validation и контекстные fixtures

**Файлы:** новые `contracts/workspace-recovery.ts`, `.test.ts`; существующие `contracts/workspace-edit.ts`, `test/workspaceEditFixture.ts`; новый `test/recoveryStorageFixture.ts`.

**Потребляет:** существующие wire parsers и fixtures.

**Предоставляет:** типы выше; `recoveryKey(context: RecoveryContext): RecoveryKey`; `parseRecoveryRecord(value: unknown, expectedActorId: string): RecoveryRecordV2`; `createRecoveryRecord(command: PendingGeometryCommand, source: Exclude<RecoverySource, null>): RecoveryRecordV2`. Последняя функция копирует и замораживает исходное намерение, revision=1, outcome=unknown, readbackRequired=true, blocks=[], requiresAccessConfirmation=false.

- [x] Добавить тесты `rejects_actor_target_and_key_mismatch`, `access_block_preserves_terminal_outcome`, `new_record_copies_source_and_command`. Assertions: чужой actor/несогласованный target бросают protocol error; known success/rejection не теряются; изменение переданных массивов после создания не меняет record.
- [x] Запустить `npm.cmd test -- --maxWorkers=2 src/contracts/workspace-recovery.test.ts` из `apps/frontend`; новые assertions должны выявлять отсутствие поведения, не ошибку окружения.
- [x] Реализовать типы/parsers; сохранить v1 decoder для миграции, не ослаблять текущие UUID/geometry/HTTP response проверки. Не выводить no-op из `operation`.
- [x] Создать независимые fixtures A/B/C с разными workOrder/editVersion/feature IDs, не менять только label при общей identity. Fixture adapter получает управляемые ошибки read/write/commit/delete и возвращает копии значений.
- [x] Повторить targeted tests и `npm.cmd run typecheck`; ожидается PASS. Проверить wire parser regression без изменений API.

## Задача 2. IndexedDB, CAS и миграция v1

**Файлы:** `stores/workspaceRecoveryStorage.ts`, `.test.ts`; новые `workspaceRecoveryMigration.ts`, `.test.ts`; storage fixture задачи 1; новый `infra/m4/s2-x01-storage.spec.ts`, изменение `infra/m4/playwright.config.ts` для `*.spec.ts`.

**Потребляет:** `RecoveryRecordV2`, key/parser задачи 1.

**Предоставляет:** `RecoveryStorage` с `list(actorId: string): Promise<RecoveryStorageLoad>`, `insert(record: RecoveryRecordV2): Promise<void>`, `replace(record: RecoveryRecordV2, expectedRevision: number): Promise<void>`, `remove(key: RecoveryKey, commandId: string, expectedRevision: number): Promise<void>`, `importLegacy(record: RecoveryRecordV2, legacyPayload: string): Promise<"imported" | "already-imported">`, `acknowledgeLegacyRemoval(actorId: string, commandId: string): Promise<void>`; `createRecoveryStorage(): RecoveryStorage`; `migrateLegacyRecovery(actorId: string, storage: RecoveryStorage): Promise<void>`. Import атомарно изменяет record и receipt внутри adapter; migration module не изображает transaction последовательными insert. Ошибки операций типизированы: unavailable, invalid, conflict; identity несовпадение никогда не ведёт к overwrite. List отделяет валидные записи от повреждённых: определимый key блокируется отдельно, null key запрещает mutations actor. Сырые повреждённые записи не удаляются и не попадают в UI.

- [x] Добавить behavioral tests `commit_failure_is_not_write_success`, `cas_rejects_old_revision_and_command`, `independent_records_survive_mutation`, `migration_is_idempotent_after_cleanup_failure`. Assert: promise записи не завершается на request success до transaction complete; A не затирает B; старый revision не обновляет block; повтор импорта не восстанавливает удалённую завершённую команду.
- [x] Запустить `npm.cmd test -- --maxWorkers=2 src/stores/workspaceRecoveryStorage.test.ts src/stores/workspaceRecoveryMigration.test.ts`; проверить RED.
- [x] Реализовать object stores `recoveries` (keyPath key, actor index) и `legacyImports` (actor + commandId, проверяемый исходный payload). `insert` запрещает занятый context; replace/remove выполняют read/check/write в одной readwrite transaction. Promise resolve только на complete; abort/error — reject.
- [x] До задачи 4 сохранить существующие synchronous v1 exports для ещё не перенесённого workOrders/auth, но не запускать новый store в production flow. Новые tests используют async adapter отдельно. Перенос не должен временно активировать два отправителя или ломать текущую сборку.
- [x] Реализовать перенос: проверить v1; атомарно сохранить v2 + import receipt; удалить v1; завершить receipt cleanup. Если v1 removal не удался, receipt не удаляется и не даёт повторно импортировать запись после её завершения. Не импортировать чужие записи автоматически. Legacy block/result сохраняются, source=null. Конфликтующие данные остаются для разбора.
- [x] В браузерном storage spec проверить настоящий IndexedDB transaction abort, два ключа, compare-and-swap и legacy receipt. В отдельной странице изолированного Vite dev origin загрузить adapter через dynamic import `/src/stores/workspaceRecoveryStorage.ts`; сценарий управляется из Playwright evaluate и не требует production debug endpoint/UI. Для этих storage tests допустима подготовка записей; это не end-to-end lost-response evidence. Добавить `corrupt_A_does_not_disable_valid_B` и проверку неидентифицируемого повреждения.
- [x] В `infra/m4/run.mjs` передать `...process.argv.slice(2)` после `"test"` при запуске Playwright CLI; test describe назвать `storage`. Повторить Vitest и выполнить из `infra/m4` `npm.cmd test -- --grep storage`; ожидается PASS на реальном Chromium. Существующие два M4 сценария остаются включёнными в полном запуске без фильтра.

## Задача 3. Recovery store и справедливая очередь

**Файлы:** новые `stores/workspaceRecovery.ts`, `.test.ts`, `workspaceRecoveryScheduler.ts`, `.test.ts`; существующие `workspaceRetry.ts`, `workspaceSaveErrors.ts`, соответствующие tests.

**Потребляет:** storage и contracts задач 1–2; `saveFeatureGeometry`, `fetchWorkspace`, existing parsers/classifier.

**Предоставляет:** `useWorkspaceRecoveryStore` actions: `bindHost(host: RecoveryHost): () => void`, `initializeActor(actorId: string): Promise<void>`, `submit(command: PendingGeometryCommand, source: Exclude<RecoverySource, null>): Promise<RecoveryStartResult>`, `retry(key: RecoveryKey): Promise<void>`, `retryRead(key: RecoveryKey): Promise<void>`, `suspend(key: RecoveryKey): Promise<void>`, `suspendActor(actorId: string): Promise<void>`, `resumeAfterAccess(key: RecoveryKey, commandId: string, sessionEpoch: number): Promise<void>`, `stopRuntime(): void`. `submit` возвращает started после commit/запуска; завершение приходит через host.complete, а не обещание навигации. Read-only selector `getRecord(key): RecoveryRecordV2 | null` и runtime phase по key.

**Scheduler:** `createRecoveryScheduler(limit: number)` предоставляет `run<T>(key: RecoveryKey, signal: AbortSignal, request: () => Promise<T>): Promise<T>`; FIFO среди готовых запросов, не допускает двух активных requests одного key. `AUTO_RETRY_DELAYS_MS` используется вне занятого HTTP slot.

- [x] Добавить тесты `unknown_A_does_not_block_B_C`, `two_recovery_requests_and_wait_releases_slot`, `series_is_single_flight`, `known_outcome_uses_get_only`; assertions: activeRecoveryHttp≤2, третья готовая команда получает слот, 5 попыток восстановления, неизменный payload, 0 PUT при known result.
- [x] Добавить `actor_switch_during_commit_prevents_put`, `old_completion_cannot_remove_new_record`, `access_block_keeps_success_and_rejection`, `readback_rejection_keeps_record`. Два submit до первого await дают только один insert/PUT; stale-generation ответ не завершает контекст.
- [x] Запустить `npm.cmd test -- --maxWorkers=2 src/stores/workspaceRecovery.test.ts src/stores/workspaceRecoveryScheduler.test.ts`; проверить RED.
- [x] Реализовать runtime controllers/generations вне persisted state. Забрать старые retry/send/readback алгоритмы, сохранив классификатор и точные интервалы. Проверять host session до persist, после persist, перед request и обработкой ответа. `interrupted` вызывается при первом unknown/error, чтобы отменить pending navigation до позднего успеха.
- [x] Реализовать known result → GET → host.applyRead → cleanup CAS → host.complete. `blocked` оставляет record; `superseded` не объявляет completion: повторное чтение допускается через безопасную очередь после завершения более нового GET, без tight loop. Terminal rejection без GET передаётся complete после cleanup. В памяти completion содержит нужные source/candidate для UI.
- [x] Реализовать access suspension как runtime stop немедленно, затем durable blocks без потери outcome. Resume снимает только access после actor/epoch/command checks. Storage/protocol/identity block не снимаются. Инициализация не обходит ошибку migration/list.
- [x] Повторить тесты, `workspaceRetry.test.ts`, `workspaceSaveErrors.test.ts`, typecheck; ожидается PASS. Покрытие X01-01/03/06/12/15 и review focus 2.

## Задача 4. Подключение workspace, общая актуальность чтений и Revert

**Файлы:** `stores/workOrders.ts`, `.test.ts`, `.edit.test.ts`, `.recovery.test.ts`; `domain/workspaceCommandPresentation.ts`, `.test.ts` для совместимости selectors; fixtures.

**Потребляет:** store/host задачи 3.

**Предоставляет:** `attachRecoveryHost(): () => void`, `reserveWorkspaceRead(context: RecoveryContext): ReadTicket`, `applyWorkspaceRead(ticket: ReadTicket, workspace: WorkspaceResponse): RecoveryApplyResult`; `staleComparisons: Record<RecoveryKey, { source: RecoverySource; candidate: LineStringXY; commandId: string }>`; `discardRejectedAttempt(): boolean` и существующие Save/Revert public actions сохраняют пользовательский смысл. Workspace snapshots хранятся по key; `workspace/activeWorkspace` — представление выбранного, не второй независимый current.

- [x] Добавить `background_A_never_replaces_selected_B`, `ordinary_newer_get_wins_over_recovery_get`, `stale_material_survives_A_B_A`, `revert_still_uses_baseline_after_extraction`. В одном тесте разрешить более новый обычный GET раньше recovery GET и проверить неизменность current/selection/marker B.
- [x] Запустить `npm.cmd test -- --maxWorkers=2 src/stores/workOrders.test.ts src/stores/workOrders.edit.test.ts src/stores/workOrders.recovery.test.ts`; новые тесты RED, старые блокировки переключения при unknown пометить как заменённые новым требованием, не удалять guards-тесты без эквивалента.
- [x] Подключить host один раз на lifecycle приложения; reserveRead един для всех GET соответствующего context. `applyRead` проверяет sessionEpoch/generation/context до изменения snapshots. Возврат к stale A перечитывает current; недоступный GET не разрешает новое редактирование.
- [x] Перевести Save/Revert на recovery.submit с source и неизменным command. Удалить старое mutable владение recovery и таймерами из workOrders; presentation selectors читают новый store. Не сохранять два пути отправки.
- [x] Переключить оставшиеся synchronous storage callsites на recovery actions; до расширения auth в задаче 5 существующий `suspendWorkspaceRecoveryForAccessLoss` становится только делегирующим адаптером без собственного state. Удалить старые exports прямого write/read/remove v1 из production flow; v1 parser остаётся только в migration. Поиск `rg` должен подтвердить отсутствие старого отправителя и mutable `recoveryRecord` в workOrders.
- [x] В host.complete перенести rejection material в нужный context; success очищает локальную попытку/selection только своего контекста. Двухэтапный Revert и confirmation identity/token guards сохранить. Cleanup failure не открывает новые mutations.
- [x] Повторить targeted tests и typecheck. Покрытие X01-04/07/08/09/16 и review focus 4. Проверить, что существующие тесты подтверждённого no-op всё ещё используют submitted source конкретной команды.

## Задача 5. Auth lifecycle, scope доступа и поздние 401

**Файлы:** `stores/auth.ts`, `.test.ts`, `api/http.ts`, `.test.ts`, `stores/workspaceRecovery.ts`, `.test.ts`, `stores/workOrders.ts`, `.recovery.test.ts`.

**Потребляет:** recovery.suspendActor/suspend/resumeAfterAccess и host.session.

**Предоставляет:** monotonic `auth.sessionEpoch: number`; `prepareLogout(): Promise<boolean>` в workOrders для durable suspension после решения навигации; существующий `auth.logout(): Promise<void>` остаётся низкоуровневым завершением сессии, UI использует navigation task 6. `auth.handleUnauthorizedResponse` принимает только ошибку запроса текущей identity/epoch. HTTP request metadata хранит actorId/epoch отправки, не bearer token.

- [x] Добавить `late_401_of_A_does_not_logout_B`, `context_403_stops_only_A`, `global_session_loss_stops_all_actor_records`, `relogin_requires_each_confirmation`, `known_success_survives_access_loss`. Assert: B session unchanged; PUT A blocked; B/C продолжаются; по known success после согласия выполняется GET, не PUT.
- [x] Добавить `logout_waits_for_suspend_commit`, `forced_logout_does_not_wait_for_storage_failure`: добровольный маршрут не обещает сохранность до durable stop, принудительный закрывает доступ немедленно; запись с исходной identity не удаляется.
- [x] Запустить `npm.cmd test -- --maxWorkers=2 src/stores/auth.test.ts src/api/http.test.ts src/stores/workspaceRecovery.test.ts`; проверить RED.
- [x] Добавить sessionEpoch на logout/actor change/forced session loss, без инвалидации обычного token refresh того же actor. Request interceptor фиксирует epoch/actor; response 401 handler сверяет их до вызова auth. Старый runtime callback не воздействует на новую сессию.
- [x] Разделить контекстные ошибки назначения/закрытия версии и глобальную потерю auth/роли. `loadAssigned` успешно исключивший A останавливает A, network failure списка не объявляется отзывом доступа. Повторный login того же actor сохраняет durable confirmation flags каждого наряда.
- [x] Повторить targeted tests и typecheck. Покрытие X01-05/06/12, review focus 1/5. Если невозможно сохранить access stop при недоступном storage, фиксировать ограничение явно; не заявлять гарантированное recovery после потери browser storage.

## Задача 6. Управляемая навигация и dialog context

**Файлы:** новые `domain/workspaceNavigation.ts`, `.test.ts`, `components/WorkspaceNavigationDialog.vue`, `.test.ts`; `stores/workOrders.ts`, `.recovery.test.ts`; `App.vue`, `.test.ts`; `EditorWorkOrdersView.vue`, `.test.ts`.

**Потребляет:** host.interrupted/complete, prepareLogout и command guards.

**Предоставляет:** `NavigationTarget = {kind: "work-order"; workOrderId: string} | {kind: "logout"}`; `NavigationChoice = "save" | "discard" | "leave" | "stay"`; `requestNavigation(target: NavigationTarget): string | null`, `resolveNavigation(id: string, choice: NavigationChoice): Promise<void>`, `cancelNavigation(id: string): void`. Контекст содержит actor/epoch/source key/target, фазу и связанный CommandId после Save. ID одноразовый; отсутствие диалога при clean даёт немедленный допустимый переход.

- [x] Добавить `save_and_leave_success_uses_original_target`, `unknown_or_get_error_cancels_navigation_forever`, `rejection_cancels_navigation`, `double_confirmation_sends_once`, `logout_resolves_stale_material_of_other_workorders`. Assertions: late success не вызывает переход/logout, discard без HTTP, stay сохраняет draft, stale A перечислен при выходе из B.
- [x] Запустить `npm.cmd test -- --maxWorkers=2 src/domain/workspaceNavigation.test.ts src/components/WorkspaceNavigationDialog.test.ts src/stores/workOrders.recovery.test.ts`; проверить RED.
- [x] Реализовать одноразовый navigation context и связь с исходным CommandId. При dirty только явный discard удаляет draft; при отправленной команде новый Save не предлагается. `interrupted` окончательно удаляет отложенную навигацию. Переход A→B не останавливает recovery A; logout выполняет prepareLogout и низкоуровневый auth.logout.
- [x] Подключить кнопки выбора наряда/выхода к requestNavigation. Не перехватывать forced unauthorized через добровольный диалог. Не добавлять beforeunload. Точные строки взять из спецификации; reuse focus/Escape patterns существующего Revert dialog.
- [x] Повторить targeted tests, `App.test.ts`, `EditorWorkOrdersView.test.ts`; ожидается PASS. Покрытие X01-10/16, review focus 5.

## Задача 7. Recovery list, stale comparison, preview и сообщения

**Файлы:** новые `WorkspaceRecoveryList.vue`, `.test.ts`, `WorkspaceStaleComparison.vue`, `.test.ts`; existing `WorkspaceEditCommands.vue`, `.test.ts`, `EditorWorkOrdersView.vue`, `workspaceCommandPresentation.ts`, `.test.ts`, `WorkspaceLineInteraction.vue`, `.test.ts`, `useWorkspaceLineInteraction.ts`.

**Потребляет:** recovery records/runtime views, staleComparisons/current snapshots и actions задач 3–6.

**Предоставляет:** recovery list без HTTP/таймеров; `comparisonPreview: { key: RecoveryKey; kind: "source" | "candidate" | "current"; geometry: LineStringXY } | null` как transient presentation state. Preview — отдельный map source/layer; workspace geometry не изменяется.

- [x] Добавить `list_contains_only_current_actor`, `known_success_read_error_is_not_unknown`, `legacy_missing_source_is_explicit`, `preview_does_not_modify_current_or_allow_drag`, `closing_comparison_keeps_material`, `discard_clears_only_its_attempt`, `historical_revert_does_not_claim_current_baseline`. Assert: source=null не подменяется baseline; no-op при недостатке данных не заявлен; protocol/storage не разблокируются кнопкой доступа.
- [x] Запустить targeted tests для новых компонентов, `WorkspaceEditCommands.test.ts`, `WorkspaceLineInteraction.test.ts`, `workspaceCommandPresentation.test.ts`; проверить RED.
- [x] Реализовать список, per-context actions и отдельное confirmation после доступа с текущими actor/epoch/CommandId. Состояния фона не открывают modal и не перемещают focus. Хранить consent вне persistent storage.
- [x] Реализовать таблицу XY и read-only preview source/candidate/current. При смене context/доступа preview снимается; при новом GET current preview обновляется без изменения source/candidate. «Отказаться от попытки» вызывает явное действие, закрытие панели не удаляет материал.
- [x] Обновить сообщения о no-op, исторической квитанции, непроверенных positional/topology, baseline/history. Ручной разбор показывает доступные identifiers/error/correlationId без токенов и без недоказанного диагноза. Не добавлять отправку обращения.
- [x] Повторить tests и typecheck. Проверить keyboard/focus на уровне компонентов. Покрытие X01-07/08/09/13/16.

## Задача 8. Настоящий browser restart и сквозные A/B/C/account сценарии

**Файлы:** новые `infra/m4/s2-x01-recovery.spec.ts`, `s2-x01-fixture.ts`; existing `recovery.spec.ts`, `playwright.config.ts`, `run.mjs`, `README.md`; при необходимости общие M4 helpers выделить из existing spec без изменения семантики Дня 12.

**Потребляет:** готовое поведение задач 1–7; существующий isolated Compose/DB snapshot/route.fetch→abort механизм.

**Предоставляет:** reproducible `npm.cmd test` из `infra/m4`; evidence в `docs/sprint_2/evidence/s2-x01/`, run ID/time, sanitized request identity/payload, counters, browser restart markers.

- [x] Создать отдельный persistent Chromium profile в тестовом временном каталоге. Тест закрывает context/browser process и повторно запускает `launchPersistentContext` с тем же userDataDir/origin. Не подменять это export/import storageState, reload или ручным recovery record. Удалять только проверенный собственный абсолютный temp path после завершения.
- [x] Подготовить до измерения независимые наряды A/B/C и второго actor в изолированной БД через test fixture, не production seed changes. Каждый имеет независимые editVersion/feature IDs; зафиксировать baseline/revision. SQL/admin действия тестового fixture разрешены только в изолированном M4 окружении, не внутри измеряемой цепочки ради подделки результата.
- [x] Добавить тесты `save_survives_browser_restart`, `revert_survives_browser_restart`, `independent_A_B_C`, `relogin_each_context`, `old_replay_keeps_new_current`. Настоящий commit скрывать от страницы, блокировать последующие PUT до контрольной точки. Проверять first commit → replay без прироста revision/events/commands, current через GET, baseline неизменен.
- [x] Для relogin сравнивать actor, не значение access token; вход B не показывает и не повторяет A. После возврата A проверять ноль PUT до каждого отдельного согласия. Access reset тестировать реальным отказом API тестовой БД, не только вызовом store.
- [x] Для позднего replay одной версии использовать существующий HTTP-контракт из тестового драйвера, потому что UI запрещает второй Save при unknown первого. Отделить этот сценарий от A/B/C разных нарядов; не обходить UI guard и не выдавать такую подделку за пользовательский сценарий. Проверить и UI current, и счётчики.
- [x] Запустить `npm.cmd test` в `infra/m4`; ожидаются новые сценарии и два прежних M4 PASS, retries=0. Настоящий frontend/browser результат не заменять unit mocks. Исправления делать по конкретным failures, не ослаблять counters/identity assertions.
- [x] Обновить README M4: новые границы, запуск, изоляция, evidence; не сохранять traces/tokens. Покрытие X01-01–06/11–14.

## Задача 9. Полная приёмка и документация результата

**Файлы:** создать `docs/sprint_2/2026-10-23-s2-x01-recovery-implementation-report.md` при фактическом выполнении (если дата другая — использовать её в имени и ссылках); обновить карточку S2-X01/README/этот план только по фактическому результату. Product code — только исправления выявленных failures с regression test.

**Потребляет:** готовые задачи 1–8, матрица X01-01–16.

**Предоставляет:** отчёт с командами, exit codes, evidence и оставшимися ограничениями; unstaged diff для пользователя.

- [x] Из `apps/frontend` выполнить `npm.cmd test -- --maxWorkers=2`, `npm.cmd run typecheck`, `npm.cmd run lint`, `npm.cmd run format:check`, `npm.cmd run build`. Ожидается exit 0; предупреждения описать, не скрывать. При sandbox-specific EPERM использовать предусмотренную эскалацию, не считать её failure продукта.
- [x] Выполнить `infra/db-tests.cmd`: существующие HTTP replay/atomicity/no-op/zero-segment/access suites должны пройти. Backend не менять без подтверждённого регрессионным тестом дефекта; границы API/схемы сохраняются.
- [x] Провести ручной проход UI в изолированном demo: A/B/C, compare preview, две стадии Revert, dirty/save-and-leave/unknown/GET error, добровольный logout. Проверить Tab/Shift+Tab/Escape/возврат фокуса и viewport 1440×900, 1024×768, 768×1024; reflow 720×450, 512×384, 384×512. Viewport reflow не называть настоящим zoom 200%.
- [x] Выполнить независимое итоговое code review выбранным способом исполнения; исправить подтверждённые findings и повторить только затронутые проверки, затем необходимые итоговые gates.
- [x] Создать отчёт по трём шагам карточки и X01-01–16. Для каждого указать конкретный тест/evidence и факт выполнения; тестовый fixture не выдавать за реальные данные организации. Только после всех обязательных checks отметить S2-X01 выполненной; календарные дни не менять.
- [x] Проверить `git diff --check`, UTF-8/LF всех новых/изменённых текстовых файлов, включая untracked. Сверить `git status --short`, не staging/commit/push.
- [x] Оценить новое долговременное техническое знание: при наличии изменения архитектуры recovery применить `/ingest repository-change` к Code_wiki отдельным docs-only проходом по соответствующему skill; это не pre-commit gate и не повод повторять текущую спецификацию в agent memory. Если knowledge node уже достаточна, объяснить отсутствие ingest. Не менять Wiki/DDD_Wiki автоматически ради task completion.

## Покрытие спецификации и самопроверка плана

| Раздел спецификации | Задачи |
| --- | --- |
| 1–3: цель, границы и C | Общие ограничения, 4, 9 |
| 4: владельцы и bridge/current | 1, 3, 4 |
| 5: IndexedDB, v1, ошибки | 1–3, 8 |
| 6: queue/retry/access | 3, 5, 8 |
| 7: UI/navigation/stale/Revert/quality | 4, 6, 7, 9 |
| 8: приёмка и counters | Tests каждой задачи, 8–9 |
| 9–10: файлы и переход к реализации | Карта файлов, интерфейсы, handoff |

Порядок исполнения последовательный: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9. Перекрывающиеся правки stores не выполнять независимыми writers одновременно. При делегировании следующая задача получает интерфейсы уже проверенной предыдущей, а не свою версию contracts.

Самопроверка: все X01-сценарии связаны с задачами; пять review risks получили тесты; имена contracts/actions согласованы; чистые implementation details оставлены исполнителю. Этот абзац фиксировал самопроверку до реализации. Фактические изменения и прогоны приведены в отчёте.

## Передача к исполнению (историческое решение)

Пользователь проверяет этот план и выбирает способ: последовательное исполнение основным агентом с итоговым независимым review либо исполнение задач отдельными агентами с review каждой задачи. Для этого плана рекомендовано последовательное исполнение основным агентом: задачи тесно связаны интерфейсами auth/recovery/workspace; единый контекст уменьшает риск несовместимых переносов. Начать только после review плана и выбора способа.


## Итоговые уточнения исполнения

Все девять задач завершены. Пользователь выбрал последовательное исполнение, итоговое независимое review проведено. Контракты дополнились причинами interruption `blocked`/`session`, необходимыми для отмены навигации и глобального access reset; wire API не менялся.

- Native IndexedDB adapter выделен в `workspaceRecoveryIndexedDb.ts`; legacy utilities оставлены для миграции и старых tests, production v1 не пишет.
- Вместо `WorkspaceStaleComparison` используется `WorkspaceComparisonPanel`; вместо самописного storage fixture — `fake-indexeddb` и `recoveryIntegration.ts`. Поведение новых UI компонентов покрыто store/domain/map suites и реальным M4, без дублирующих component-only suites.
- Проверка transaction abort после request success добавлена отдельно; она подтверждает commit boundary, дополнительно к CAS abort в Chromium.
- Ручной UI-проход заменён воспроизводимым Playwright-проходом и визуальным просмотром screenshots агентом. Отдельная ручная сессия человека и настоящий zoom 200% не заявляются.
- Persistent profiles оставлены в игнорируемом `infra/m4/test-results/`; автоматическое рекурсивное удаление профиля не требуется для продукта и не выполнялось. Изолированные Docker-проекты очищены runner.
- Git staging/commit/push, merge и cleanup текущего checkout не выполняются по правилам репозитория. Все отклонения и их стоимость — в [журнале](2026-10-23-s2-x01-execution-ledger.md).
