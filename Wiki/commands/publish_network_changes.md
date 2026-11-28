---
title: "Опубликовать утверждённое изменение сети"
type: command
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/UtilityGisEditor.md"
tags: [domain-knowledge, utility-gis]
confidence: inferred
related: [DDD_Wiki/aggregates/network_edit_version, Wiki/policies/publication, Wiki/domain_events/network_changes_published]
---

# Опубликовать утверждённое изменение сети

## Actor

Участник с полномочием публикации.

## Target

Утверждённый объём изменения в рабочей версии и соответствующие записи официальной сети.

## Preconditions

Проверки правил и топологии пройдены, конфликты в публикуемом изменении разрешены, утверждение относится к его составу. При отсутствии основания для публикации официальная сеть сохраняет прежнее состояние.

## Outcome

При успехе указанный объём становится частью официальной схемы. Офис, мобильные клиенты и внешние системы могут получать результат для дальнейшей работы. Передача конкретному потребителю происходит после [[Wiki/domain_events/network_changes_published|публикации]]. Общая политика оставляет открытым вопрос о действии утверждения после изменения связанных данных. [[Wiki/policies/publication|Условия публикации]].

Основание в исходной модели. [Офисная, полевая и оперативная работа с сетью](../../RAW_inputs/documents/UtilityGisEditor.md#базовые-и-продвинутые-workflows).
