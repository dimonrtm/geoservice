---
title: Persona-Кандидаты Authoritative GIS Editing
type: entity
status: draft
created: 2026-06-02
updated: 2026-06-02
source: "user answers to /discover --phase Ф2, 2026-06-02; RAW_inputs/documents/Ф2.md"
tags: [persona, discovery, phase-f2, authoritative-editing, research]
---

# Persona-Кандидаты Authoritative GIS Editing

## Статус

Первый проход `/discover --phase Ф2` выбрал два модельных persona-кандидата. Второй проход определил `Utility GIS editor` как primary research-persona. Оба сценария остаются research-гипотезами, а не описанием подтвержденных реальных пользователей.

## Utility GIS Editor

- Статус: primary research-persona; подробнее в [[utility_gis_editor]].
- Контекст: эксплуатация инженерной сети.
- Рабочая задача: отражать изменения сетевых объектов и поддерживать authoritative network layer в корректном состоянии.
- Боль-гипотеза: параллельные правки могут привести к конфликтам authoritative state, неверным trace-результатам, повторной проверке и снижению доверия к сетевому слою.
- Текущий обходной путь из research: named versions, reconcile/post, Conflicts view, reviewer workflow и разделение задач по work order или зонам ответственности.
- Desired outcome: изменения опубликованы после контролируемого разрешения конфликтов и проверки топологии.

## Кадастровый Инженер

- Статус: deferred research-сценарий; пользователь считает его более сложным для реализации.
- Контекст: изменения участков, split/merge и lineage.
- Рабочая задача: корректно провести кадастровое изменение и сохранить юридически значимую историю границ.
- Боль-гипотеза: параллельные правки могут привести к конфликтующей lineage, спорному статусу участков, задержке публикации и ручному аудиту.
- Текущий обходной путь из research: branch versioning, правило "одна версия - одно кадастровое дело", editor tracking, reconcile/post и reviewer перед публикацией.
- Desired outcome: участки и lineage консистентны, версия опубликована, record можно передавать дальше.

## Общее

- Общий класс риска: silent overwrite или неконтролируемое слияние недопустимы.
- Общая модель collaborative editing: изолированные версии и контролируемая публикация authoritative state.
- Scope Release 1 не меняется автоматически: связь с demo и MVP определяется на Ф4.

## Неясно

- Проверить модельные боли `Utility GIS editor` на synthetic pilot и, если возможно, на реальном рабочем контексте.

## Связи

- [[../../chats/2026-06-02-phase-f2-users-and-pain]]
- [[utility_gis_editor]]
- [[../../concepts/jtbd]]
- [[../../concepts/collaborative_editing_models]]
- [[../../solution/USM]]
- [[../../decisions/followups/index]]
