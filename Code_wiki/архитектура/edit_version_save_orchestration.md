---
title: Атомарный Save, replay и история EditVersion
type: technical-note
status: active
created: 2026-10-16
updated: 2026-10-16
source: repository-change:2026-10-16
tags: [edit-version, save, replay, transaction, history]
---

# Атомарный Save, replay и история EditVersion

## Граница транзакции

`EditVersionService.save_geometry` выполняет Save/Revert в одной `AsyncSession.begin()`: root lock, проверка контекста и идентичности, reservation команды, validation, запись current, revision, terminal response и change event. Repository предоставляет операции хранения; сервис определяет их порядок. Root блокируется по WorkOrder/EditVersion, command lookup глобален по `command_id`. Save не берёт WorkOrder lock после root; reopen использует WorkOrder → EditVersion.

Сервис проверяет активного Editor, текущее назначение и lifecycle `open`/`in_progress`. Guards действуют и при replay: сохранённый успешный ответ не даёт права получить результат после потери доступа. Для новой команды отсутствие версии/feature до reservation не занимает CommandId. Существующий, но чужой объект маскируется `EDIT_VERSION_NOT_FOUND`; такой отказ при доступном внутреннем context может быть сохранён в registry.

## Идентичность и повтор

`edit_version_commands` имеет глобальный PK `command_id`. До нового reservation сервис проверяет retained change history: ID с событием нельзя занять заново после удаления operational registry. `INSERT ... ON CONFLICT DO NOTHING` позволяет прочитать победившую команду; другая версия, feature, actor или fingerprint дают `COMMAND_ID_REUSED`.

Обычный `geom-v1` fingerprint зависит от неизменяемого baseline/policy и исходного token, а не от current. При недоступном baseline новая команда получает `geom-contextless-v1` и отказ контекста; сохранённый формат идентичности при повторе не меняется. Если baseline сломался после сохранения `geom-v1`, fallback на другую идентичность запрещён.

Matching terminal replay выполняется до проверки token против текущей revision: возвращается исходный успешный payload или прежний domain rejection. Поэтому replay может содержать исторические geometry/token. Текущие данные читаются отдельным workspace GET — [[edit_version_api_readback]]. `running` не является долговременным состоянием: deferred constraint trigger запрещает commit незавершённой команды.

Единственное предусмотренное возобновление terminal rejection — `retry_on_access_change=true` для `404 EDIT_VERSION_NOT_FOUND`, выставляемое при несовпадении assignee. После восстановления доступа та же identity проходит `rejected → running` и повторную domain/token validation в одной транзакции. Обычные отказы не возобновляются после исправления данных. Текущие access/lifecycle guards могут маскировать прежний результат, не переписывая его.

## Save, no-op и Revert

Новая команда проходит подготовку candidate, проверку `draftVersionToken == str(draft_revision)`, spatial/structure guards и ограниченную запись. Domain rejection сохраняется как terminal row; `WorkOrderApiError` выбрасывается только после успешного commit отказа. Ошибки инфраструктуры и исключения после начала mutation откатывают всю транзакцию и не превращаются в durable domain rejection.

При фактическом изменении revision увеличивается на 1; успешный result сохраняется в registry. `change_set_persisted` создаётся для resulting operation `updated`, `change_set_cleared` — для возврата к baseline. No-op создаёт успешный результат команды, но не меняет revision, geometry или историю. Revert — тот же Save с baseline geometry, новым CommandId и текущим token; он восстанавливает точный baseline EWKB и не удаляет прежние события. Matching retry не выполняет повторную mutation.

## Схема и история

Миграция `b7d2e9f4a6c8` добавляет `draft_revision` (BIGINT, начальное значение 1), registry и `edit_version_change_events`. Переходы и неизменность identity защищены trigger, согласованность полей result — CHECK. Operational registry связан FK с версией/feature; история хранит идентификаторы без FK на удаляемый рабочий контекст.

Change event содержит command/version/workOrder/defaultState/feature/actor, before/after geometry, base revision, соседние draft revisions и время. PK по CommandId и unique `(edit_version_id, draft_revision_after)` запрещают дубли. Insert trigger сверяет событие с успешной командой, current geometry/operation и revision под root lock. UPDATE, DELETE и TRUNCATE истории запрещены trigger. Эти ограничения не являются реализацией сроков архива/удержаний SIM-UGIS-RET-001; автоматическая очистка и архивный workflow здесь не реализованы. Downgrade схемы уничтожает registry/history и не является retention-операцией.

## Проверяемые источники

- `apps/backend/utility_service/use_cases/services/edit_version_service.py`
- `apps/backend/utility_service/use_cases/services/edit_version_save_identity.py`
- `apps/backend/utility_service/infrastructure/postgresql/repositories/edit_version_repository.py`
- `apps/backend/utility_service/infrastructure/postgresql/repositories/edit_version_commands.py`
- `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/b7d2e9f4a6c8_first_save_schema.py`
- `apps/backend/utility_service/infrastructure/postgresql/models/work_order/edit_version_command.py`
- `apps/backend/utility_service/infrastructure/postgresql/models/work_order/edit_version_change_event.py`

Сценарии зафиксированы в `test_save_geometry_atomicity.py`, `test_save_geometry_events.py`, `test_save_geometry_concurrency.py` в `apps/backend/tests/integration_tests/` и `apps/backend/utility_service/use_cases/tests/test_save_geometry_rejections.py`. В рамках ingest проверены исходники; эти suites повторно не запускались.

Связи: [[edit_version_persistence]], [[edit_geometry_determinism]], [[data_model]], [[frontend_save_recovery]].
