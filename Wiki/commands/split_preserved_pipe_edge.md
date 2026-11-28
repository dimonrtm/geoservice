---
title: "Разделить ребро при установке задвижки"
type: command
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/2026-11-27-field-information-answers.md"
tags: [domain-knowledge, utility-gis, field-evidence]
confidence: inferred
related: [DDD_Wiki/aggregates/network_edit_version, DDD_Wiki/aggregates/network_asset, Wiki/value_objects/evidence_extent]
---

# Разделить ребро при установке задвижки

## Actor

ГИС-редактор, учитывающий установленную задвижку.

## Target

Ребро в рабочей версии, новый узел и физическая труба с историей осмотров.

## Preconditions

Установлены место новой задвижки и то, что исходная физическая труба сохранилась.

## Outcome

Редактор делит прежний путь на два ребра с новым узлом и связывает оба ребра с той же трубой. Изменение связности проходит обычную проверку и публикацию. Осмотры сохраняют прежние дату, физический объект и [[Wiki/value_objects/evidence_extent|охват]]. При локализованном дефекте можно указать соответствующее новое ребро. Если известна лишь труба, результат остаётся в её общей истории. Физическая замена требует отдельного установления идентичности.

Решения условной организации через `expert_repson`. [NET-05](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-05) · [Офисная, полевая и оперативная работа с сетью](../../RAW_inputs/documents/UtilityGisEditor.md#базовые-и-продвинутые-workflows).
