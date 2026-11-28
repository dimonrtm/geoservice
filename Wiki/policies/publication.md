---
title: "Условия публикации изменения сети"
type: policy
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/UtilityGisEditor.md"
tags: [domain-knowledge, utility-gis]
confidence: inferred
related: [DDD_Wiki/aggregates/network_edit_version, Wiki/specifications/change_scope_publishable, Wiki/commands/approve_network_changes, Wiki/commands/publish_network_changes, DDD_Wiki/use_cases/utility_editor_workflow]
---

# Условия публикации изменения сети

## Rule

На схеме процесса проверка правил и топологии предшествует рассмотрению и утверждению. Выявленную ошибку или конфликт исправляют, затем повторяют проверку. В официальный слой публикуют утверждённое изменение.

## Decision Outcome

Если проверка выявила ошибку соединения, изменение остаётся в работе. После успешной проверки, разрешения конфликтов и утверждения результат можно опубликовать и передать потребителям. Распределение полномочий между проверяющим, утверждающим и публикующим в источнике не установлено.

На исполнительной съёмке действие правила ограничено предъявленным объёмом. Редактор может выделить измеренную часть с установленной границей и явной пометкой о неподтверждённой врезке. Утверждение и публикация этого объёма сохраняют прежние пути через место спорной врезки. Допуск опубликованного участка к работе подтверждает эксплуатация. Это порядок условной организации. [NET-09](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-09) · [NET-10](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-10).

[UtilityGisEditor.md · Базовые и продвинутые workflows](../../RAW_inputs/documents/UtilityGisEditor.md#базовые-и-продвинутые-workflows)
