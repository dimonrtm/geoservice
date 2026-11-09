---
title: Сверка model_health с реализацией
type: verification-report
status: active
created: 2026-11-09
updated: 2026-11-09
source: текущий код apps/backend/utility_service и apps/frontend/src; Code_wiki; отчёты Sprint 2
tags: [model-health, code-reconciliation, first-save, recovery]
---

# Сверка model_health с реализацией

## Результат и границы

Сверка 09.11.2026 выполнена по рабочему дереву при HEAD b2b4296, включая незакоммиченные изменения. Код не изменялся. First-save, публичные Save/Revert/readback и S2-X01 recovery присутствуют в реализации; ставить их заново в очередь как отсутствующие неправильно. ReviewPackage и дальнейшая публикация остаются моделью. Метка stale у model_health снята после обновления активной очереди; это актуальность документа, не полнота продукта.

Новые проверки: 105 frontend-тестов в 10 файлах. Backend/PostGIS, M4 и фактическая БД в этом проходе повторно не запускались. Их прежние протоколы имеют собственную дату/область; чтение кода не выдаётся за текущую сквозную приёмку.

## Матрица кода и модели

| Область | Фактическое состояние | Проверяемое основание |
| --- | --- | --- |
| WorkOrder / открытие версии | assigned → in_progress; повторное открытие возвращает существующую open EditVersion. Closed/cancelled lifecycle отсутствует в модели хранения | [WorkOrderStatus](../../apps/backend/utility_service/infrastructure/postgresql/models/work_order/work_order.py), [EditVersionService](../../apps/backend/utility_service/use_cases/services/edit_version_service.py) |
| Baseline и policy | При открытии создаётся рабочая версия по DefaultState; Save читает закреплённый baseline и persisted policy, а не заменяет их current | [service](../../apps/backend/utility_service/use_cases/services/edit_version_service.py), [repository](../../apps/backend/utility_service/infrastructure/postgresql/repositories/edit_version_repository.py), [[Code_wiki/архитектура/edit_geometry_fixture_metadata]] |
| Атомарный Save | session.begin, root lock, identity/reservation, guards/token, spatial validation, запись current/revision/result/event; domain rejection после commit результата | [service](../../apps/backend/utility_service/use_cases/services/edit_version_service.py), [[Code_wiki/архитектура/edit_version_save_orchestration]] |
| Пространственные ограничения | XY/SRID 4326, valid/simple, отсутствие нулевых сегментов, полное покрытие AOI; одна изменённая feature и одна внутренняя вершина | [spatial SQL](../../apps/backend/utility_service/infrastructure/postgresql/sql/edit_geometry_spatial.sql), [structure](../../apps/backend/utility_service/domain_services/edit_geometry/structure.py), [repository](../../apps/backend/utility_service/infrastructure/postgresql/repositories/edit_version_repository.py) |
| Idempotency / события | CommandId проверяется по registry/history; matching terminal replay не повторяет запись; no-op без revision/event; изменение и возврат к baseline дают разные события | [service](../../apps/backend/utility_service/use_cases/services/edit_version_service.py), [registry/history migration](../../apps/backend/utility_service/infrastructure/postgresql/alembic/versions/b7d2e9f4a6c8_first_save_schema.py) |
| Публичный API | Список/открытие наряда, GET карты/ChangeSet/baseline и PUT geometry существуют. Revert использует тот же PUT с baseline, новым CommandId и текущим token | [routes](../../apps/backend/utility_service/web_api/api/work_orders.py), [[Code_wiki/архитектура/edit_version_api_readback]] |
| UI правки | Выбор линии, drag, local draft, Save, двухэтапный Revert, dirty navigation и сравнение source/candidate/current присутствуют | [map interaction](../../apps/frontend/src/composables/map/useWorkspaceLineInteraction.ts), [commands UI](../../apps/frontend/src/components/WorkspaceEditCommands.vue), [commands store](../../apps/frontend/src/stores/editVersionCommands.ts) |
| Ограничение UI | Только линия ровно с тремя вершинами, изменяется index 1. Backend-правило одной внутренней вершины шире. Это граница текущего упражнения, не поддержка произвольной линии в UI | [line guards](../../apps/frontend/src/domain/workspaceLineInteraction.ts), [map interaction](../../apps/frontend/src/composables/map/useWorkspaceLineInteraction.ts) |
| Recovery | Запись в IndexedDB до отправки; ключ actor/WorkOrder/EditVersion, отдельные receipt/current, retry/readback и независимые контексты | [recovery](../../apps/frontend/src/stores/workspaceRecovery.ts), [IndexedDB](../../apps/frontend/src/stores/workspaceRecoveryIndexedDb.ts), [editor session](../../apps/frontend/src/stores/editorSession.ts) |
| Возврат доступа | Остановка затронутых контекстов, requiresAccessConfirmation; resumeAfterAccess проверяет actor, commandId, epoch и доступ. Возврат доступа не означает автоматического продолжения | [recovery](../../apps/frontend/src/stores/workspaceRecovery.ts), [[Code_wiki/архитектура/browser_auth_sessions]] |
| Позиционная пригодность | Успешный изменяющий Save возвращает POSITIONAL_ACCURACY_UNVERIFIED; evaluator и автоматический переход VERIFIED не найдены | [response builder](../../apps/backend/utility_service/use_cases/schemas/edit_version/geometry_save_out.py) |
| Review/post/withdrawal/correction | Нет реализованных package model, endpoint submit/reviewer/post gate и publisher workflow. Нет closed WorkOrder для post-correction. Сохранённые команды Save не являются публикационным audit | routes + модели WorkOrder; поиск ReviewPackage/submit_for_review/can_post/simulated_post/withdrawn в production source |
| Retention и restart | История Save защищена от UPDATE/DELETE/TRUNCATE; это не workflow архива/удержаний SIM-UGIS-RET-001. Recovery прежней команды не является новым edit-контекстом на исправленном baseline | migration + recovery; [[Code_wiki/архитектура/edit_version_save_orchestration]], [[Code_wiki/архитектура/frontend_save_recovery]] |

Поиск отсутствующих символов использован вместе с просмотром routes, lifecycle и текущих services, а не как самостоятельное доказательство отсутствия любого возможного поведения. Качество/топология/trace, приёмка, новая корректирующая работа и публикация остаются отдельными обязательствами модели.

## Проверки этого прохода

Из apps/frontend запущен Vitest с --maxWorkers=2:

- Первый прогон: workspaceRecovery, workspaceRecoveryIndexedDb, workOrders.recovery, workOrders.multicontext, WorkspaceEditCommands, useEditVersionEditor — 66/66, 6 suites. В фильтре также был прежний отсутствующий workOrders.edit.test.ts; он не засчитан. Актуальный edit.test.ts проверен вторым прогоном.
- Второй прогон: edit, editVersionDraft, editorNavigation, workspaceLineInteraction — 39/39, 4 suites.

Первый запуск остановился до тестов на spawn EPERM esbuild; те же проверки выполнены после разрешённой эскалации. Это ограничение sandbox, не failure приложения. Успех тестов относится к указанным suites; полный frontend suite/build, backend DB suite и M4 заново не запускались.

[Отчёт S2-X01 от 23.10](../sprint_2/2026-10-23-s2-x01-recovery-implementation-report.md) содержит прежние результаты DB/M4 и браузерного восстановления. [Протокол metadata/fixture от 08.11](2026-11-08-demo-dataset-runtime-check.md) подтверждает только указанный локальный экземпляр revision 49, 19 объектов/9 связей и техническую пригодность L-003. Ни один не доказывает позиционную точность на местности.

## Последствия для очереди

FU-2026-10-11-001 закрывается как выполненная сверка документации: технический ingest уже есть в Code_wiki, metadata/fixture сверены прежним протоколом, активная модельная очередь теперь сопоставлена с кодом. Новый repository-change ingest не нужен: нового устойчивого технического знания сверх существующих технических нод не обнаружено.

FU-2026-10-13-004 остаётся open: evaluator/evidence, отдельный restart на исправленном основании, архив/удержания, остальные организационные правила и новые publication exceptions не реализованы этим проходом. FU-2026-07-25-001 не закрывается целиком: выполнение first-save не доказывает positional acceptance и downstream completion. Отсутствие реализации не переоткрывает отвеченные доменные вопросы.

Техническая очередь: не повторять first-save/S2-X01; определить реализуемый путь evidence/positional readiness до успешного submit, затем materialized package, reviewer decision/computed gate и simulated post с аудитом. Withdraw/correction учитываются в соответствующем будущем slice, не добавляются автоматически в текущий Save. При новом планировании приоритет/сроки и 14-дневный объём определяются отдельно.
