---
title: "Передать проверенный объём на утверждение"
type: command
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/2026-11-27-field-information-answers.md"
tags: [domain-knowledge, utility-gis, field-evidence]
confidence: inferred
related: [DDD_Wiki/aggregates/network_edit_version, Wiki/specifications/surveyed_part_publishable, Wiki/commands/approve_network_changes]
---

# Передать проверенный объём на утверждение

## Actor

ГИС-редактор, подготовивший изменения.

## Target

Определённый состав правок рабочей версии. Для исполнительной съёмки допустима самостоятельно проверяемая часть с установленной границей.

## Preconditions

Перед передачей редактор сопоставляет изменения с актуальной сетью, исправляет конфликты в предъявляемом объёме и проверяет правила и топологию. Неустранённая ошибка в этом объёме возвращает правку на доработку. Проектную врезку без подтверждения оставляют за пределами предъявляемых соединений.

## Outcome

Утверждающему доступны состав правки, основание и результаты проверки. Официальная сеть продолжает показывать последнюю публикацию.

Решения условной организации через `expert_repson`. [NET-09](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-09) · [Офисная, полевая и оперативная работа с сетью](../../RAW_inputs/documents/UtilityGisEditor.md#базовые-и-продвинутые-workflows).
