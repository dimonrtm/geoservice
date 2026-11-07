---
title: Публичный Save API и согласованный readback EditVersion
type: technical-note
status: active
created: 2026-10-12
updated: 2026-11-04
source: repository-change:2026-11-04
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
клиент повторно читает карту версии и ChangeSet. Revert использует тот же PUT с baseline geometry,
новым CommandId и текущим token; отдельного Revert endpoint нет.

`WorkOrderEditRoute` ограничивает strict mapping request/path errors операциями сохранения геометрии и чтения версии. Для них ошибки имеют только
`{code,message,correlationId}`; `422 REQUEST_VALIDATION_ERROR` описан и в OpenAPI.
List/open/legacy validation этим adapter не меняется. CORS разрешает PUT только
для настроенных origins. Auth требует активного Editor; assignment проверяется
на сервере. Закрытый Save context возвращает `SAVE_CONTEXT_CLOSED`, неподходящий
workspace lifecycle — `EDIT_VERSION_STATE_CONFLICT`.

## Текущий persisted draft

Карта, ChangeSet и исходная линия читаются отдельно. GET ресурса версии возвращает наряд, AOI, видимые объекты и связи с двумя видимыми концами. Токен и геометрия принадлежат одному снимку схемы `work_order`. Карта доступна при сбое чтения baseline.

GET `/change-set` возвращает токен проверенной ревизии, признак сохранённого изменения, basicValidation и nullable changeSet. Сервис получает рабочие объекты всей версии и исходные объекты закреплённого снимка через разные репозитории. Сравнение геометрии определяет индекс внутренней вершины. Проверка обнаруживает также изменение за пределами AOI. Некорректный или отсутствующий снимок приводит к ошибке чтения. Успешный пустой ChangeSet означает отсутствие сохранённых изменений.

GET `/features/{feature_id}/baseline` возвращает исходную геометрию одной доступной линии из снимка `EditVersion.default_state_id`. Save также читает исходную линию через репозиторий `utility_network` и выполняет проверку в транзакции изменения рабочей версии.

После расхождения токенов клиент автоматически повторяет чтение карты и ChangeSet. Исходная геометрия запрашивается при выборе линии или автоматически по фиче из непустого ChangeSet. При временной ошибке зависимого чтения экран остаётся в режиме просмотра. После первоначального запроса выполняются до четырёх повторов с паузами 2, 5, 10 и 20 секунд. Кнопка «Повторить» возобновляет соответствующее чтение.

## Источники

- `apps/backend/utility_service/web_api/api/work_orders.py`
- `apps/backend/tests/integration_tests/test_workspace_save_concurrency.py`
- `apps/frontend/src/composables/useEditVersionEditor.ts`

Связи: [[edit_version_save_orchestration]], [[frontend_save_recovery]], [[api_and_realtime]], [[edit_version_persistence]].
