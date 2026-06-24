---
title: Model Health
type: state
status: active
created: 2026-06-24
updated: 2026-06-24
source: "docs/superpowers/specs/2026-06-24-domain-knowledge-layer-design.md; Vision_wiki/concepts/utility_gis_editing_domain.md; Code_wiki/архитектура/data_model.md"
tags: [domain-knowledge, ddd, health]
confidence: high
related: [DDD_Wiki/index, Wiki/_registry/conflicts, Wiki/_registry/questions]
---

# Model Health

## Current Summary

Первичная доменная модель создана вокруг core subdomain `Utility Authoritative Editing`: `WorkOrder`, `EditVersion`, рабочее пространство, проверка, публикация и аудит. Модель опирается на текущий дизайн релиза и спринта, решения из `Vision_wiki` и модель данных/API из `Code_wiki`.

## Current Blocking Conflicts

| Conflict | Blocks | Status | Next Question |
| --- | --- | --- | --- |
| [[Wiki/conflicts/2026-06-24-reviewer-vs-publisher]] | Ролевая модель финальной публикации | active | Является ли `Publisher` отдельной ролью? |
| [[Wiki/conflicts/2026-06-24-release1-vs-release2-review-policy]] | Границы ближайшего спринта и state machine проверки/публикации | active | Какие правила Release 2 про устаревание и блокеры входят в ближайшие 14 дней? |

## Current Coverage

| Area | Status | Notes |
| --- | --- | --- |
| Ubiquitous Language | active | [[Wiki/glossary/utility_gis_editing]] и реестры созданы. |
| Subdomains | active | Core subdomain [[DDD_Wiki/subdomains/utility_authoritative_editing]] отделен от generic map editing. |
| Bounded Contexts | active | Выделены контексты Work Order, Utility Network, Review Post, Audit и Auth. |
| Context Map | active | [[DDD_Wiki/context_map/geoservice_context_map]] описывает upstream/downstream и границу application layer. |
| Aggregates | active | `WorkOrder` и `EditVersion` активны; `ReviewPackage` запланирован. |
| Commands And Events | active | `OpenEditVersion` активна; команды review/post запланированы. |
| Policies And Specifications | active | Проверка назначения активна; политики review/post/stale запланированы. |
| Sprint Planning Inputs | active | `Wiki/_registry/questions.md` содержит первые приоритетные вопросы для планирования 14-дневного спринта. |

## Current Discovery Queue

Следующий `/discover` должен сгенерировать 150 candidate questions на основе этой модели, двух активных конфликтов, запланированной модели review/post и пробелов реализации в `Code_wiki`, затем выбрать top 15.

## Current Sprint Planning Queue

Следующий `/plan-sprint` должен использовать 14-дневную рамку спринта и выбрать top 15 planning questions из 150 candidate questions. Самые важные стартовые вопросы:

- Должен ли следующий спринт продолжать frontend workflow для `WorkOrder`/`EditVersion` или начать укрепление модели review/post?
- Какие правила Release 2 про устаревание и блокеры обязательны сейчас, а какие остаются planned?
- Кто владеет финальным `PostToDefault`: Reviewer, Publisher или data owner?

## Superseded Draft Summary

Первичный каркас доменной модели создан. Содержательная инициализация выполняется отдельным проходом по существующим raw, Vision_wiki, Code_wiki и sprint/release документам.

## Blocking Conflicts

| Conflict | Blocks | Status | Next Question |
| --- | --- | --- | --- |
| Нет зафиксированных конфликтов в новом слое | Полнота модели пока не оценена | draft | Выполнить первичную инициализацию доменной модели |

## Coverage

| Area | Status | Notes |
| --- | --- | --- |
| Ubiquitous Language | draft | Требуется извлечение из текущих источников |
| Subdomains | draft | Требуется классификация core/supporting/generic |
| Bounded Contexts | draft | Требуется привязка к текущей модели данных и коду |
| Aggregates | draft | Требуется проверка инвариантов |
| Commands And Events | draft | Требуется связать команды, события и политики |
| Sprint Planning Inputs | draft | Требуется список вопросов для 14-дневного спринта |

## Discovery Queue

Следующий `/discover` должен сгенерировать 150 candidate questions по пробелам модели и выбрать top 15 для пользователя.
