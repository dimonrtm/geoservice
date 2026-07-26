---
title: Command ID
type: value-object
status: planned
created: 2026-07-25
updated: 2026-07-26
source: "RAW_inputs/meetings/first_save_for_edit_version.md; RAW_inputs/meetings/tolerance_rules.md"
tags: [domain-knowledge, value-object, idempotency, edit-version]
confidence: high
related: [Wiki/entities/edit_version, Wiki/value_objects/draft_version_token, Wiki/glossary/base_work_state, Wiki/commands/update_edit_version_feature_geometry]
---

# Command ID

`CommandId` - уникальный idempotency key одного command payload. Он обязателен уже в first-save slice и не является concurrency token.

## Equality

Одинаковый `CommandId` обозначает одну и ту же команду только при идентичном смысловом payload. Fingerprint включает target feature, [[Wiki/glossary/base_work_state]], ожидаемый `DraftVersionToken`, тип операции, изменяемую вершину или точный diff и канонический resulting geometry после применения [[Wiki/glossary/coordinate_storage_precision]]. Сырые координаты могут различаться, если их канонический результат совпадает.

Повтор с тем же id и тем же fingerprint возвращает результат уже выполненной операции без новой mutation. Переиспользование id для другого fingerprint отклоняется.

## Immutability

После выдачи `CommandId` не меняется и не переносится на другое намерение.

## Retention And Scope

Idempotency record хранится на стороне системы и должен переживать reconnect, повторный вход и продолжение работы с другого устройства. Пользовательская сессия и устройство не определяют identity команды.

Повтор распознаётся, пока record не истёк и относится к тому же базовому состоянию. После изменения базового состояния или истечения опубликованного idempotency window клиент должен создать новый `CommandId`; старый запрос трактуется как новое намерение или conflict по актуальному состоянию. Точная длительность window остаётся отдельным implementation/domain-policy выбором.

## Separation From Concurrency

`DraftVersionToken` отвечает на вопрос, какую текущую версию агрегата обновляет client. `CommandId` отвечает на вопрос, не является ли request повтором уже выполненного намерения после потери response. Идемпотентный retry не создает новую mutation, не меняет token и не дублирует domain event.

Если после исходной команды feature была изменена снова, запоздалый retry не возвращает старое состояние как текущее: response подтверждает, что исходная команда уже выполнена, и показывает актуальный persisted object.

## Used By

`UpdateEditVersionFeatureGeometry` и будущие state-changing commands, для которых retry после потери response должен быть безопасным.
