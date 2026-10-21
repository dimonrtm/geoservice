---
title: Frontend Save и восстановление намерения редактора
type: technical-note
status: active
created: 2026-10-16
updated: 2026-10-21
source: repository-change:2026-10-21
tags: [frontend, pinia, save, recovery, readback]
---

# Frontend Save и восстановление намерения редактора

## Разделение данных

Единственный `useWorkOrdersStore` разделяет workspace/current, `localDraft`, `recoveryRecord`/`pendingCommand` и `commandResult`. Локальный draft содержит копии source/candidate geometry и source token. Двигается одна внутренняя вершина; при persisted changeSet выбирается та же feature/vertex. Local dirty определяется относительно source current без клиентской canonicalization. Cancel очищает local draft без HTTP; он не отменяет уже отправленную команду.

`saveFeatureGeometry` делает один PUT без скрытых retry. Runtime guards из `contracts/workspace-edit.ts` проверяют command/feature identity успешного ответа, согласованность operation/changeSet/validation; workspace guard также проверяет пару workOrder/editVersion и единственную изменённую внутреннюю вершину относительно baseline. Это проверка контракта, не геодезическая или PostGIS validation.

## Намерение до отправки

Save создаёт один UUID и замораживает target/request вместе с coordinate arrays. До первого PUT обязательна запись `WorkspaceRecoveryRecord` в `sessionStorage` под `geoservice:workspace-recovery:v1:<actorId>`. Запись содержит schemaVersion, actor, target, исходный token и geometry; состояния — `unknown`, `succeeded`, `rejected`, `blocked`. Другую pending command нельзя перезаписать; malformed/недоступное storage блокирует отправку. Recovery не хранит auth token и не обещает восстановления после уничтожения sessionStorage или закрытия сессии вкладки.

`unknown` относится к осведомлённости клиента. Backend сохраняет атомарный terminal result, см. [[edit_version_save_orchestration]]. Нельзя создавать новый CommandId, пока исход прежнего намерения не разрешён.

## Повторы и current readback

После первоначального network/timeout/5xx сбоя store допускает 5 дополнительных попыток с паузами 0/2/5/10/20 секунд. Restore неизвестного исхода и каждый ручной retry выполняют новую серию из 5 попыток всего. Одновременные запуски серии запрещены; общего lifetime budget нет. Во всех случаях сохраняются CommandId, token, target и geometry. `AbortController`, поколения запросов и проверка текущего actor/workspace/command останавливают устаревшие callbacks.

Success сначала сохраняется в recovery как квитанция, затем выполняется workspace GET. Только GET заменяет current/token/changeSet. Ошибка GET удерживает подтверждённый результат и требует повторного чтения, а не нового PUT. Ручное чтение выполняет ровно один GET; recoveryReadSeq исключает параллельные чтения. Storage/role/blocked guards проверяются в action, поэтому прямой вызов не обходит блокировку интерфейса. Историческая квитанция replay не перезаписывает более свежий current. Recovery удаляется только после необходимого readback и успешного удаления записи storage.

`DRAFT_VERSION_STALE` сохраняет отвергнутую локальную попытку, читает current и не делает automatic reapply. После успешного GET/cleanup действие `discardRejectedAttempt` явно очищает попытку без HTTP; новую правку начинают из current. Сравнение и перенос candidate не реализованы. После завершённого stale readback refresh может потерять отвергнутый draft — граница Дня 9 сохраняется. Известный domain rejection завершает recovery, оставляя возможность исправить local draft. `REQUEST_VALIDATION_ERROR` считается подтверждённым отказом лишь до неизвестного исхода; после unknown это protocol block. Неизвестный/некорректный ответ, `COMMAND_ID_REUSED` и access/lifecycle ошибки разделены как protocol/identity/access block.

## Доступ и навигация

Store запрещает смену workspace при local draft, незавершённом recovery, readback или blocked-состоянии. Потеря назначения, auth reset/logout и смена actor останавливают retry, инвалидируют поколения и сохраняют blocked recovery. Повторный вход не разрешает автоматическое продолжение; требуется явное подтверждение. Даже при ошибке storage запись не считается безопасно очищенной.

## Подтверждение Revert и общий pipeline

Панель `WorkspaceEditCommands` подключает Save/Cancel, ручной retry/readback, отказ от stale и Revert. `beginRevert` создаёт временный контекст actor/workOrder/editVersion/feature/token. При dirty сначала предлагается продолжить редактирование либо окончательно отказаться от draft; затем требуется отдельное согласие на baseline. Отмена второго решения не возвращает draft.

Store блокирует редактирование и другие команды при подтверждении. Синхронный watcher инвалидирует согласие при смене identity/token/доступа; `confirmRevert` повторно проверяет контекст и storage. Target и geometry берутся из change set, поэтому выбор линии не обязателен. UUID команды создаётся только после согласия. Приватный `submitGeometryCommand` обслуживает и Save, и Revert: persist → PUT → terminal result → GET → cleanup. Повторы неизвестного Revert не спрашивают согласия заново; новая попытка после stale получает новое согласие и ID.

Панель использует native dialog с безопасным начальным фокусом, Tab/Shift+Tab, Escape и возвратом фокуса. Карта учитывает `workspaceInteractionLocked`; после успешного readback выбор снят, marker отсутствует. Recovery schema не расширена ради подписи операции; `operation=unchanged` не определяет Revert или no-op.

## Граница реализации и S2-X01

Recovery включён через `openSelectedWorkOrder`/`restoreOpenedWorkspace` → `restorePendingSave`. Пользовательские команды подключены; прежнее описание отсутствующих controls отражало срез 2026-10-16. Актуализация технической части относится к существующему FU-2026-10-11-001, но не закрывает его доменный остаток.

S2-X01 сохраняет явное продолжение после обнаруженной потери доступа, переход на другой наряд при незавершённом recovery и расширенное сравнение/перенос попытки. Evaluator, архив и организационные правила не объявляются реализованными.

## Сквозная проверка recovery

`infra/m4` — отдельный пакет Playwright Test и уникальный disposable Compose-проект с API, frontend и `m4_test`. Инициализация schema/seed предшествует сценариям; API entrypoint запускает только uvicorn, поэтому restart не восстанавливает данные через seed. БД сохраняется между commit и replay.

Browser-context route выполняет настоящий PUT через `route.fetch()`, подтверждает commit отдельным SQL-чтением и скрывает ответ через `route.abort()`. Повторы блокируются до restart и новой навигации той же вкладки. Recovery record создаётся приложением; тест не записывает storage вручную. При refresh access token обновляется, поэтому неизменность actor проверяется по JWT subject и owner версии; исходные CommandId/draftVersionToken/geometry проверяются отдельно.

Save и Revert сравнивают три снимка БД: до команды, после первого commit и после replay. Первая содержательная команда добавляет одну revision/событие/запись команды, replay — ноль. Baseline проверяется независимо, после replay требуется отдельный GET. Результаты и ограничения — в отчёте Дня 12; обычный refresh и unit tests эту проверку не заменяют. Runbook: `infra/m4/README.md`.

## Источники

- `apps/frontend/src/contracts/workspace-edit.ts`
- `apps/frontend/src/api/workOrders.ts`
- `apps/frontend/src/domain/workspaceDraft.ts`
- `apps/frontend/src/stores/workOrders.ts`
- `apps/frontend/src/stores/workspaceRecoveryStorage.ts`
- `apps/frontend/src/stores/workspaceSaveErrors.ts`
- `apps/frontend/src/stores/workspaceRetry.ts`
- `apps/frontend/src/stores/auth.ts`
- `apps/frontend/src/components/WorkspaceEditCommands.vue`
- `apps/frontend/src/domain/workspaceCommandPresentation.ts`
- `apps/frontend/src/composables/map/useWorkspaceLineInteraction.ts`
- `docs/sprint_2/2026-10-20-day-12-recovery-design.md`
- `infra/m4/recovery.spec.ts`
- `infra/m4/run.mjs`
- `infra/m4/compose.yml`
- `docs/sprint_2/2026-10-15-day-9-frontend-state-implementation-report.md`
- `docs/sprint_2/2026-10-12-s2-x01-save-recovery-followup.md`

Проверки поведения описаны в `apps/frontend/src/stores/workOrders.recovery.test.ts`, `workOrders.edit.test.ts`, `workspaceRecoveryStorage.test.ts` и `apps/frontend/src/contracts/workspace-edit.test.ts`; ingest не является повторным тестовым прогоном.

Связи: [[frontend]], [[edit_version_api_readback]], [[edit_version_save_orchestration]].
