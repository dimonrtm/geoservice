---
title: "Внести подтверждённый стык труб"
type: command
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/2026-11-27-field-information-answers.md"
tags: [domain-knowledge, utility-gis, field-evidence]
confidence: inferred
related: [DDD_Wiki/aggregates/network_edit_version, Wiki/specifications/pipe_joint_evidenced, Wiki/entities/network_association]
---

# Внести подтверждённый стык труб

## Actor

ГИС-редактор, проверяющий изменение связности.

## Target

Рабочая версия и две трубы в месте предполагаемого соединения.

## Preconditions

Исполнительная схема или полевой материал однозначно указывают соединительную деталь и оба присоединения. Правило топологической допустимости проверяют для этих элементов.

## Outcome

Редактор создаёт общий узел и связывает с ним обе трубы. Изменённую связность предъявляют к проверке и публикации. При одном лишь пересечении линий редактор отмечает спорное место и оставляет прежние пути. Проверенное прохождение без стыка позволяет снять пометку. Если исполнительная съёмка участка поступила раньше подтверждения врезки, добавление установленного стыка становится отдельной правкой. [[Wiki/specifications/pipe_joint_evidenced|Условие для общего узла]].

Решения условной организации через `expert_repson`. [NET-04](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-04) · [NET-09](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-09) · [Офисная, полевая и оперативная работа с сетью](../../RAW_inputs/documents/UtilityGisEditor.md#базовые-и-продвинутые-workflows).
