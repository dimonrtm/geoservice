---
title: "Подтверждённый стык внесён в рабочую версию"
type: domain-event
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/2026-11-27-field-information-answers.md"
tags: [domain-knowledge, utility-gis, field-evidence]
confidence: inferred
related: [DDD_Wiki/aggregates/network_edit_version, Wiki/commands/record_pipe_joint, Wiki/specifications/pipe_joint_evidenced]
---

# Подтверждённый стык внесён в рабочую версию

## Source Aggregate

[[DDD_Wiki/aggregates/network_edit_version|Рабочая версия сети]], в которой редактор учёл оба присоединения.

## Happened In The Past

Редактор связал две установленные трубы общим узлом на основании исполнительной схемы или полевого материала, который опознаёт соединительную деталь и оба присоединения. В рабочей версии появился конкретный переход, который теперь можно проверить вместе со смежными рёбрами.

## Downstream Reactions

Потребитель официальной сети увидит новый путь после проверки, утверждения и публикации. Если бригада подтвердила прохождение труб без стыка, редактор может закрыть вопрос о месте пересечения без создания общего узла.

Решения условной организации через `expert_repson`. [NET-04](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-04) · [NET-09](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-09) · [Офисная, полевая и оперативная работа с сетью](../../RAW_inputs/documents/UtilityGisEditor.md#базовые-и-продвинутые-workflows).
