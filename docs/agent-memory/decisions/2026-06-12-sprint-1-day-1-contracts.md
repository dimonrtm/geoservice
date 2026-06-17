# Контракты Дня 1 Спринта 1

Date: 2026-06-12
Type: decision
Tags: sprint-1, acceptance, domain-model, api, backlog, localization
Related files:

- `docs/release_1/sprint_1/README.md`
- `docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-acceptance-design.md`
- `docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-domain-model-design.md`
- `docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-api-contract-design.md`
- `docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-vertical-backlog-design.md`

## Summary

День 1 нового Спринта 1 завершает контрактную подготовку без production-кода.
Результат разделен на четыре источника истины: acceptance-сценарий, доменную
модель, API-контракт и вертикальный backlog. Все документы Спринта 1 собраны в
`docs/release_1/sprint_1`; старые generic-планы сохранены в
`docs/release_1/sprint_1/legacy-generic-plan`.

## Context

Acceptance охватывает путь
`Login -> My Work Orders -> Create/Open EditVersion -> Edit Workspace` и
защитные проверки чужого `WorkOrder`, неверной роли, дублирования активной
version и поврежденного доменного контекста. Editing, validation, reconcile,
review и post не входят в Спринт 1.

`AOI` является серверной границей набора данных workspace, а не только рамкой
карты. `Feeder` является агрегатом demo-сети: объединяет принадлежащие ему
`NetworkFeature` и внутрефидерные `NetworkAssociation`.

## Actions

- 2026-06-12: Зафиксированы AC-01..AC-07 и read-only workspace.
- 2026-06-12: Зафиксированы сущности, связи, состояния и инварианты без
  окончательной SQL-схемы.
- 2026-06-12: Зафиксированы endpoints, DTO и ошибки `401/403/404/409/422`.
- 2026-06-12: Зафиксирован вертикальный backlog S1-01..S1-10 без почасовых
  оценок.
- 2026-06-12: Принято правило: весь пользовательский текст и все сообщения,
  формируемые приложением для logs, пишутся на русском языке; API paths, JSON
  keys, error `code`, типы и идентификаторы остаются на английском.
- 2026-06-12: Документы Спринта 1 перенесены в `docs/release_1/sprint_1`, исторический
  generic scope отделен в подпапку `legacy-generic-plan`.

## Verification

Проверена согласованность AC, доменных состояний, endpoints и HTTP/error codes.
В актуальных документах отсутствуют `TBD`, `TODO` и неявные расширения scope.
Старые ссылки на прежние расположения файлов не найдены.

## Retrieval Hints

Спринт 1 День 1, acceptance AC-01 AC-07, AOI серверная граница, Feeder агрегат,
EditVersion idempotent open, API contract, вертикальный backlog, русские логи,
docs/release_1/sprint_1
