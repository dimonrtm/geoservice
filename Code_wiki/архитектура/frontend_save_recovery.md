---
title: Frontend Save и восстановление намерения редактора
type: technical-note
status: active
created: 2026-10-16
updated: 2026-10-23
source: repository-change:2026-10-23
tags: [frontend, pinia, save, recovery, readback, indexeddb]
---

# Frontend Save и восстановление намерения редактора

## Владение и границы

`useWorkspaceRecoveryStore` владеет отправленными намерениями, outcome, retry и долговременным хранением. Ключ — JSON `(actorId, workOrderId, editVersionId)`, одна незавершённая команда на версию. Неизвестный исход A не запрещает Save независимой версии B. Recovery не импортирует workOrders: явный `RecoveryHost` предоставляет session/access/readback/completion callbacks.

`useWorkOrdersStore` владеет current snapshots, локальным draft, selection, навигацией и временным stale-сравнением. Обычный draft не хранится как отправленная команда. `recoveryRecord` — вычисляемое совместимое представление выбранного контекста, а не второй владелец состояния.

Backend остаётся транзакционным: [[edit_version_save_orchestration]]. Клиентский unknown описывает осведомлённость, persisted `OutcomePending` отсутствует.

## Запись до отправки

IndexedDB `geoservice-workspace-recovery`, версия 1, содержит stores `recoveries` и `legacyImports`. Schema записи recovery — 2. Frozen command содержит actor/target/CommandId/source token/candidate, source evidence хранится отдельно. Outcome unknown/succeeded/rejected независим от blocks access/protocol/identity/storage. Подтверждение доступа снимает только access.

Первый PUT разрешён после transaction complete, а не request success. Replace/delete сверяют revision и identity в одной транзакции; старый callback не удаляет другую команду. Ошибки хранения блокируют небезопасную mutation, известный результат удерживается. Повреждённый определимый key изолируется; неопределимая запись блокирует actor. Сырые данные не удаляются автоматически.

Миграция v1 из actor-scoped sessionStorage атомарно копирует record и receipt, затем удаляет v1. Receipt не позволяет воскресить уже завершённую команду после crash между copy и cleanup. Legacy source=null показывается честно. Auth tokens в recovery не сохраняются. Нормальное закрытие браузера поддержано в том же профиле/origin; уничтожение storage, private-mode guarantees, offline drafts и координация вкладок не входят в контракт.

## Повторы и current

Первоначальный PUT допускает пять дополнительных повторов с задержками 0/2/5/10/20 секунд. Restore/manual retry — пять попыток всего. FIFO scheduler допускает не более двух recovery HTTP одновременно; retry-wait освобождает слот, один key имеет один активный run. Polling отсутствует. Перед фактическим выполнением в очереди заново проверяются actor, epoch и доступ.

Known success сохраняется до GET; ошибка GET не превращает результат в unknown и не запускает новый PUT. Только workspace GET обновляет current/token/changeSet; replay-result исторический. Обычные и recovery GET используют общий generation по key и session epoch. Намерение открыть workspace живёт отдельно от transient spinner: новый recovery GET может закончиться после superseded ordinary GET, и workspace всё равно откроется. Ошибка устаревшего ordinary GET не закрывает более свежий принятый workspace.

Recovery удаляется после принятого необходимого readback и успешного storage cleanup. `DRAFT_VERSION_STALE` удерживает source/candidate до GET, затем материал сравнения остаётся в памяти при переключениях. После завершённого readback refresh может его потерять; автоматического reapply нет.

## Доступ и навигация

Auth `sessionEpoch` ограждает callbacks и поздние 401/403 от новой сессии. Потеря роли/идентичности останавливает все recovery actor; потеря назначения — конкретный наряд. Неудача загрузки списка из-за сети не доказывает отзыв назначений. Suspend учитывает ещё не загруженные records и незавершённые записи. После обнаруженной потери доступа/login/logout каждый контекст требует отдельного согласия с текущими epoch и CommandId. Обычное восстановление действующей сессии запускает доступные recovery автоматически.

Управляемая навигация с dirty предлагает сохранить/отказаться/остаться. Save-and-leave связан с исходными target/command/epoch: только success и GET без промежуточного сбоя выполняют переход. Unknown, отказ, ошибка GET, storage/protocol/identity/access отменяют переход окончательно; поздний success не вызывает logout. При отправленной команде текст: «Выход не отменяет отправленную команду». Logout отдельно предупреждает о потере временных stale-материалов всех нарядов.

## Revert, сравнение и сообщения

Revert сохраняет две стадии согласия: удалить dirty draft, затем подтвердить baseline reset. Отмена второй стадии не возвращает draft. Команда получает UUID только после согласия и использует общий pipeline persist → PUT → result → GET → cleanup. Неизвестный Revert повторяется с прежней identity без нового диалога.

`WorkspaceComparisonPanel` показывает XY source/candidate/current. Map preview — отдельный read-only overlay, canonical workspace не заменяется; drag при stale запрещён. «Отказаться от попытки» удаляет только выбранный материал. Закрытие preview его не удаляет. Разрушение MapLibre выполняет владелец карты; дочерний teardown не создаёт заново overlay на уже уничтоженной карте.

No-op требует source evidence, не выводится из `operation`. При недостатке доказательств восстановленная квитанция сообщает «Прежняя операция выполнена». Позиционная точность и топология остаются непроверенными; Revert не стирает историю. Диалоги удерживают Tab/Shift+Tab внутри enabled actions, Escape отменяет, фокус возвращается к инициатору.

## Проверяемые источники

- `apps/frontend/src/contracts/workspace-recovery.ts`
- `apps/frontend/src/stores/workspaceRecovery.ts`, `workspaceRecoveryIndexedDb.ts`, `workspaceRecoveryMigration.ts`, `workspaceRecoveryScheduler.ts`
- `apps/frontend/src/stores/workOrders.ts`, `auth.ts`, `apps/frontend/src/api/http.ts`
- `apps/frontend/src/components/WorkspaceRecoveryList.vue`, `WorkspaceNavigationDialog.vue`, `WorkspaceComparisonPanel.vue`, `WorkspaceEditCommands.vue`
- `apps/frontend/src/domain/workspaceCommandPresentation.ts`, `dialogFocus.ts`
- `apps/frontend/src/composables/map/useWorkspaceLineInteraction.ts`
- `infra/m4/README.md`, `s2-x01-recovery.spec.ts`, `s2-x01-storage.spec.ts`
- `docs/sprint_2/2026-10-23-s2-x01-recovery-design.md`

Техническая актуализация относится к FU-2026-10-11-001; его доменный остаток metadata/fixture не закрыт. Приёмочные результаты хранятся в отчёте S2-X01, а не в этой архитектурной ноде.
