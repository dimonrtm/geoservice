---
title: Command ID
type: value-object
status: planned
created: 2026-07-25
updated: 2026-07-31
source: "RAW_inputs/meetings/first_save_for_edit_version.md; RAW_inputs/meetings/tolerance_rules.md; RAW_inputs/meetings/demo_utility_gis.md"
tags: [domain-knowledge, value-object, idempotency, edit-version]
confidence: high
related: [Wiki/entities/edit_version, Wiki/value_objects/draft_version_token, Wiki/glossary/base_work_state, Wiki/commands/update_edit_version_feature_geometry, DDD_Wiki/state_machines/edit_version_save_request]
---

# Command ID

`CommandId` - глобально уникальный idempotency key одного command payload. Он обязателен уже в first-save slice и не является concurrency token. Внешнее имя `saveId` из source является API alias того же понятия, а не отдельным value object.

## Equality

Одинаковый `CommandId` обозначает одну и ту же команду только при идентичном смысловом payload. Fingerprint включает tenant/project scope, `WorkOrder`, `EditVersion`, target feature, [[Wiki/glossary/base_work_state]], ожидаемый `DraftVersionToken`, тип операции, изменяемую вершину или точный diff, канонический resulting geometry после применения [[Wiki/glossary/coordinate_storage_precision]] и structure hash. Сырые координаты могут различаться, если их канонический результат совпадает.

Повтор с тем же id и тем же fingerprint возвращает тот же operation state/result без новой mutation. Переиспользование id для другого fingerprint отклоняется. Одновременные одинаковые запросы образуют одну operation: повтор в состоянии `running` получает ссылку на тот же pending outcome, а не запускает вторую mutation.

## Immutability

После выдачи `CommandId` не меняется и не переносится на другое намерение.

## Retention And Scope

Операционный idempotency record хранится на стороне системы весь lifecycle соответствующей `EditVersion` и должен переживать reconnect, повторный вход и продолжение работы с другого устройства. Пользовательская сессия и устройство не определяют identity команды.

После `post`, close, cancel, перевода версии в read-only или administrative archive старый request отклоняется как закрытый save context и не трактуется как новое намерение. Изменённый payload всегда требует нового `CommandId`.

Операционный registry отделён от append-only history save operations. Registry живёт не меньше lifecycle `EditVersion`; immutable history хранится по records policy `WorkOrder`/authoritative data. Точный долгосрочный срок хранения history остаётся открытым policy-вопросом.

Domain rejection резервирует `CommandId`: одинаковый retry возвращает то же отклонение, а исправленный request получает новый id. Если request не был принят или распознан системой, id не резервируется; при неизвестном исходе после начала commit id считается зарезервированным до установления результата.

## Separation From Concurrency

`DraftVersionToken` отвечает на вопрос, какую текущую версию агрегата обновляет client. `CommandId` отвечает на вопрос, не является ли request повтором уже выполненного намерения после потери response. Идемпотентный retry не создает новую mutation, не меняет token и не дублирует domain event.

Если после исходной команды feature была изменена снова, запоздалый retry не применяет старую mutation повторно: response подтверждает результат исходной operation и отдельно показывает актуальный persisted object.

## Used By

`UpdateEditVersionFeatureGeometry` и будущие state-changing commands, для которых retry после потери response должен быть безопасным.
