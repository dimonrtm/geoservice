---
title: Command ID
type: value-object
status: planned
created: 2026-07-25
updated: 2026-07-25
source: RAW_inputs/meetings/first_save_for_edit_version.md
tags: [domain-knowledge, value-object, idempotency, edit-version]
confidence: high
related: [Wiki/entities/edit_version, Wiki/value_objects/draft_version_token, Wiki/commands/update_edit_version_feature_geometry]
---

# Command ID

`CommandId` - уникальный idempotency key одного command payload. Он обязателен уже в first-save slice и не является concurrency token.

## Equality

Одинаковый `CommandId` обозначает одну и ту же команду только при идентичном payload. Повтор с тем же id и тем же payload возвращает сохраненный результат уже выполненной операции. Переиспользование id для другого payload отклоняется.

## Immutability

После выдачи `CommandId` не меняется и не переносится на другое намерение.

## Separation From Concurrency

`DraftVersionToken` отвечает на вопрос, какую текущую версию агрегата обновляет client. `CommandId` отвечает на вопрос, не является ли request повтором уже выполненного намерения после потери response. Идемпотентный retry не создает новую mutation, не меняет token и не дублирует domain event.

## Used By

`UpdateEditVersionFeatureGeometry` и будущие state-changing commands, для которых retry после потери response должен быть безопасным.
