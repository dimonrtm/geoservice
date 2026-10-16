---
title: Публичный Save API и согласованный readback EditVersion
type: technical-note
status: active
created: 2026-10-12
updated: 2026-10-16
source: repository-change:2026-10-12
tags: [api, edit-version, readback, baseline, geometry]
---

# Публичный Save API и согласованный readback EditVersion

## HTTP-граница Save

`PUT /api/v1/work-orders/{work_order_id}/edit-versions/{edit_version_id}/features/{feature_id}/geometry`
передаёт raw request bytes существующему Decimal parser, затем вызывает
`EditVersionService.save_geometry`. Request содержит `commandId`,
`draftVersionToken` и полную geometry. Это XY LineString минимум с двумя
вершинами; запрет extras/duplicate keys и числовые ограничения parser сохраняются.
Ошибка формата не создаёт command registry row. Принятый parser-ом запрос может
получить durable domain rejection: две вершины вместо трёх относятся к этому случаю.

Успешный ответ возвращается после завершения Save transaction. Matching retry
сохраняет исходный payload, в том числе исторический token. Для текущего состояния
клиент повторно читает workspace. Revert использует тот же PUT с baseline geometry,
новым CommandId и текущим token; отдельного Revert endpoint нет.

`WorkOrderEditRoute` ограничивает strict mapping request/path errors двумя
операциями: geometry PUT и workspace GET. Для них ошибки имеют только
`{code,message,correlationId}`; `422 REQUEST_VALIDATION_ERROR` описан и в OpenAPI.
List/open/legacy validation этим adapter не меняется. CORS разрешает PUT только
для настроенных origins. Auth требует активного Editor; assignment проверяется
на сервере. Закрытый Save context возвращает `SAVE_CONTEXT_CLOSED`, неподходящий
workspace lifecycle — `EDIT_VERSION_STATE_CONFLICT`.

## Текущий persisted draft

В `workOrder.editVersion` workspace обязательны `draftVersionToken`,
`hasPersistedChangeSet`, `basicValidation` и `changeSet`. У чистого draft два
последних поля равны null, после Revert token не сбрасывается. Непустой changeSet
содержит `featureId`, `vertexIndex`, полную `baselineGeometry` и `operation=updated`.
Current geometry остаётся в `features`.

`workspace_aggregate.sql` одним statement читает revision, baseline root по
`EditVersion.default_state_id` и все пары current/baseline. Проверяемые пары не
ограничены AOI; видимые features и associations сохраняют прежний AOI-фильтр.
Отсутствующие baseline/AOI сохраняются как неполный context для controlled error.
Repository передаёт raw EWKB hex, а WorkspaceService декодирует геометрию после
role, assignment и lifecycle guards. Это сохраняет 404 для чужого workspace даже
при повреждении его геометрии.

Чистая `project_workspace_draft` сравнивает точные числовые значения без
canonicalization при GET. Unchanged points и двухвершинные lines допустимы.
Diff допускает одну видимую line с одной изменённой внутренней вершиной и
`operation=updated`. Отсутствующая сторона пары, несовместимый baseline,
несогласованная operation, несколько или скрытое изменение дают
`422 WORKSPACE_CONTEXT_INVALID`; автоматического repair нет.

Validation summary описывает сохранённый draft, прошедший Save, и содержит
`POSITIONAL_ACCURACY_UNVERIFIED`; GET не выполняет новую внешнюю проверку качества.
Один SQL snapshot не смешивает token и geometry при конкурентном Save и не берёт
mutation root lock. Baseline/current используют обратимый EWKB codec.

## Источники и проверяемые границы

- `apps/backend/utility_service/web_api/api/work_orders.py`
- `apps/backend/utility_service/web_api/api/work_order_edit_route.py`
- `apps/backend/utility_service/infrastructure/postgresql/sql/workspace_aggregate.sql`
- `apps/backend/utility_service/use_cases/services/workspace_service.py`
- `apps/backend/utility_service/use_cases/services/workspace_draft_projection.py`
- `apps/backend/tests/integration_tests/test_geometry_save_api_integration.py`
- `apps/backend/tests/integration_tests/test_workspace_save_concurrency.py`
- `docs/sprint_2/2026-10-12-day-8-api-readback-design.md`

Тест с новым client/app/session подтверждает независимое чтение persisted данных,
но не фактический restart процесса. Frontend Save/Revert и S2-X01 имеют отдельный scope.

## Согласование описаний

Post-ingest correction по зарегистрированному FU-2026-10-11-001 синхронизировала
[[edit_geometry_determinism]] и [[data_model]] с текущими PUT/decoding/EWKB.
Backend registry/replay и frontend recovery описаны отдельно:
[[edit_version_save_orchestration]], [[frontend_save_recovery]].

Связи: [[api_and_realtime]], [[edit_version_persistence]], [[edit_geometry_determinism]], [[data_model]].
