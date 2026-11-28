---
title: "Принять исполнительную съёмку построенной части"
type: command
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/2026-11-27-field-information-answers.md"
tags: [domain-knowledge, utility-gis, field-evidence]
confidence: inferred
related: [DDD_Wiki/aggregates/network_edit_version, Wiki/specifications/surveyed_part_publishable, Wiki/commands/submit_network_changes]
---

# Принять исполнительную съёмку построенной части

## Actor

ГИС-редактор, принимающий фактические сведения от подрядчика.

## Target

Измеренная часть построенного участка в рабочей версии и относящийся к ней полевой материал.

## Preconditions

Участок опознан. Граница фактических измерений позволяет отличить снятую часть от проектного продолжения.

## Outcome

Редактор фиксирует измеренную геометрию, ссылку на съёмку и сведения о подключении. Если врезка есть только на проекте, на построенной части указывают «подключение не подтверждено». Если часть самостоятельно проходит обязательные проверки, редактор может [[Wiki/commands/submit_network_changes|передать её на утверждение]]. При невыделимой границе или топологической ошибке материал остаётся в работе. Соответствие проекту и допуск в действующую сеть имеют отдельные основания. Исполнительная съёмка может оставаться достоверной и при спорной применимости проектного изменения.

Решения условной организации через `expert_repson`. [NET-09](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-09) · [NET-10](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-10) · [NET-11](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-11) · [Офисная, полевая и оперативная работа с сетью](../../RAW_inputs/documents/UtilityGisEditor.md#базовые-и-продвинутые-workflows).
