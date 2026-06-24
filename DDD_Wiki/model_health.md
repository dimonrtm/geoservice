---
title: Model Health
type: state
status: active
created: 2026-06-24
updated: 2026-06-24
source: "docs/superpowers/specs/2026-06-24-domain-knowledge-layer-design.md; Vision_wiki/concepts/utility_gis_editing_domain.md; Code_wiki/архитектура/data_model.md; RAW_inputs/meetings/implementation_contract_for_review_and_post.md"
tags: [domain-knowledge, ddd, health]
confidence: high
related: [DDD_Wiki/index, Wiki/_registry/conflicts, Wiki/_registry/questions]
---

# Model Health

## Current Summary

Первичная доменная модель создана вокруг core subdomain `Utility Authoritative Editing`: `WorkOrder`, `EditVersion`, рабочее пространство, проверка, review/post и аудит. Review/post contract уточнен новым RAW source: `Reviewer` выполняет semantic `approve package`, `Publisher` / demo-system action владеет technical `PostToDefault`, а `ReviewPackage` становится отдельным aggregate для evidence, risk tier, blockers, stale status и audit.

## Current Blocking Conflicts

| Conflict | Blocks | Status | Next Question |
| --- | --- | --- | --- |
| Нет активных blocking conflicts после ingest `implementation_contract_for_review_and_post.md` | - | clear | Следующий вопрос - оформить implementation contract v0.1 и проверить human layer |

## Recently Resolved Conflicts

| Conflict | Resolution Source | Result |
| --- | --- | --- |
| [[Wiki/conflicts/2026-06-24-reviewer-vs-publisher]] | `RAW_inputs/meetings/implementation_contract_for_review_and_post.md` | `Publisher` отделен от `Reviewer`; ближайший срез использует demo-system action для technical post. |
| [[Wiki/conflicts/2026-06-24-release1-vs-release2-review-policy]] | `RAW_inputs/meetings/implementation_contract_for_review_and_post.md` | Must-scope ближайшего среза: `ReviewPackage`, evidence, `RiskTier`, hard blockers, stale policy и audit. |

## Current Coverage

| Area | Status | Notes |
| --- | --- | --- |
| Ubiquitous Language | active | [[Wiki/glossary/utility_gis_editing]] и реестры созданы. |
| Subdomains | active | Core subdomain [[DDD_Wiki/subdomains/utility_authoritative_editing]] отделен от generic map editing. |
| Bounded Contexts | active | Выделены контексты Work Order, Utility Network, Review Post, Audit и Auth. |
| Context Map | active | [[DDD_Wiki/context_map/geoservice_context_map]] описывает upstream/downstream и границу application layer. |
| Aggregates | active | `WorkOrder`, `EditVersion` и `ReviewPackage` активны в доменной модели. |
| Commands And Events | active | `OpenEditVersion` активна; команды review/post запланированы. |
| Policies And Specifications | active | Проверка назначения, ready-for-review, post allowed, review/post и stale policies активны. |
| Sprint Planning Inputs | active | `Wiki/_registry/questions.md` содержит первые приоритетные вопросы для планирования 14-дневного спринта. |

## Current Discovery Queue

Следующий `/discover` должен сгенерировать 150 candidate questions на основе обновленной review/post модели, открытых validation hypotheses, реализации `Code_wiki` и оставшихся human-layer вопросов, затем выбрать top 15.

## Current Sprint Planning Queue

Следующий `/plan-sprint` должен использовать 14-дневную рамку спринта и выбрать top 15 planning questions из 150 candidate questions. Самые важные стартовые вопросы:

- Должен ли следующий спринт продолжать frontend workflow для `WorkOrder`/`EditVersion` или начать укрепление модели review/post?
- Как оформить implementation contract v0.1 для review/post slice без расширения в full topology engine?
- Какие human-layer вопросы требуют real `Editor`/`Reviewer` validation: evidence sufficiency, trust wording, specialist confirmation для `Critical`?

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
