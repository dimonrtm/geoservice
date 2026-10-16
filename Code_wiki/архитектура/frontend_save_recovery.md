---
title: Frontend Save и восстановление намерения редактора
type: technical-note
status: active
created: 2026-10-16
updated: 2026-10-16
source: repository-change:2026-10-16
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

После первоначального network/timeout/5xx сбоя store допускает 5 дополнительных попыток с паузами 0/2/5/10/20 секунд. Restore неизвестного исхода выполняет 5 попыток всего; manual retry делает одну. Во всех случаях сохраняются CommandId, token, target и geometry. `AbortController`, поколения запросов и проверка текущего actor/workspace/command останавливают устаревшие callbacks.

Success сначала сохраняется в recovery как квитанция, затем выполняется workspace GET. Только GET заменяет current/token/changeSet. Ошибка GET удерживает подтверждённый результат и требует повторного чтения, а не нового PUT. Историческая квитанция replay не перезаписывает более свежий current. Recovery удаляется только после необходимого readback и успешного удаления записи storage.

`DRAFT_VERSION_STALE` сохраняет локальную попытку для сравнения, читает current и не делает automatic reapply. Известный domain rejection завершает recovery, оставляя возможность исправить local draft. `REQUEST_VALIDATION_ERROR` считается подтверждённым отказом лишь до неизвестного исхода; после unknown это protocol block. Неизвестный/некорректный ответ, `COMMAND_ID_REUSED` и access/lifecycle ошибки разделены как protocol/identity/access block.

## Доступ и навигация

Store запрещает смену workspace при local draft, незавершённом recovery, readback или blocked-состоянии. Потеря назначения, auth reset/logout и смена actor останавливают retry, инвалидируют поколения и сохраняют blocked recovery. Повторный вход не разрешает автоматическое продолжение; требуется явное подтверждение. Даже при ошибке storage запись не считается безопасно очищенной.

## Граница реализации и S2-X01

На `6c4b6ba` реализованы contracts/API/store, локальное редактирование и recovery-механика. `openSelectedWorkOrder` и `restoreOpenedWorkspace` вызывают `restorePendingSave` после загрузки workspace, поэтому recovery включён в существующий путь восстановления косвенно через store. Отсутствие прямого component-вызова не доказывает отсутствие refresh flow. В компонентах/composables нет вызовов `saveLocalDraft`, `beginLocalEdit` или `retryPendingSave`; пользовательские controls и сквозная приёмка остаются отдельным scope. Отдельного store action для Revert к baseline также нет. Уточнение проверено по исходникам после ingest research 2026-10-16 в рамках зарегистрированного FU-2026-10-11-001.

Для S2-X01 доступны backend terminal replay и current GET, pending identity, ограниченный retry, stale без reapply, storage/access guards. Остаются UI wiring, явное подтверждение продолжения после возврата доступа, диалоги навигации/выхода, Revert с разрешением local draft, пользовательские сообщения и сквозная приёмка. Более поздние правила условной организации об evaluator, restart и архиве не считаются реализованными. Календарь и статус S2-X01 этим ingest не изменены.

## Источники

- `apps/frontend/src/contracts/workspace-edit.ts`
- `apps/frontend/src/api/workOrders.ts`
- `apps/frontend/src/domain/workspaceDraft.ts`
- `apps/frontend/src/stores/workOrders.ts`
- `apps/frontend/src/stores/workspaceRecoveryStorage.ts`
- `apps/frontend/src/stores/workspaceSaveErrors.ts`
- `apps/frontend/src/stores/workspaceRetry.ts`
- `apps/frontend/src/stores/auth.ts`
- `docs/sprint_2/2026-10-15-day-9-frontend-state-implementation-report.md`
- `docs/sprint_2/2026-10-12-s2-x01-save-recovery-followup.md`

Проверки поведения описаны в `apps/frontend/src/stores/workOrders.recovery.test.ts`, `workOrders.edit.test.ts`, `workspaceRecoveryStorage.test.ts` и `apps/frontend/src/contracts/workspace-edit.test.ts`; ingest не является повторным тестовым прогоном.

Связи: [[frontend]], [[edit_version_api_readback]], [[edit_version_save_orchestration]].
