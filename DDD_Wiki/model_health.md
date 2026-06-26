---
title: Model Health
type: state
status: active
created: 2026-06-24
updated: 2026-06-26
source: "docs/superpowers/specs/2026-06-24-domain-knowledge-layer-design.md; Vision_wiki/concepts/utility_gis_editing_domain.md; Code_wiki/архитектура/data_model.md; RAW_inputs/meetings/implementation_contract_for_review_and_post.md; RAW_inputs/meetings/ic_review_package_and_simulated_post.md"
tags: [domain-knowledge, ddd, health]
confidence: high
related: [DDD_Wiki/index, Wiki/_registry/conflicts, Wiki/_registry/questions]
---

# Model Health

## Current Summary

Первичная доменная модель создана вокруг core subdomain `Utility Authoritative Editing`: `WorkOrder`, `EditVersion`, рабочее пространство, проверка, review/post и audit. Текущий review/post contract должен быть отдельным integrated artifact, встроенным в существующий `WorkOrder` / `EditVersion` flow: `submit_for_review -> reviewer decision -> computed can_post -> simulated post -> durable audit`. Legacy standalone Release 2 contract остается reference для прежнего `geometry/association conflict` framing и не является source of truth для ближайшей реализации.

## Current Blocking Conflicts

| Conflict | Blocks | Status | Next Question |
| --- | --- | --- | --- |
| Нет активных blocking conflicts после ingest `ic_review_package_and_simulated_post.md` | - | clear | Следующий вопрос - оформить отдельный integrated review/post implementation contract и разложить его на маленькие спринты |

## Recently Resolved Conflicts

| Conflict | Resolution Source | Result |
| --- | --- | --- |
| [[Wiki/conflicts/2026-06-24-reviewer-vs-publisher]] | `RAW_inputs/meetings/implementation_contract_for_review_and_post.md`; `RAW_inputs/meetings/ic_review_package_and_simulated_post.md` | `Publisher` отделен от `Reviewer`; developer demo использует system `post-gate` для simulated technical post после computed `can_post`. |
| [[Wiki/conflicts/2026-06-24-release1-vs-release2-review-policy]] | `RAW_inputs/meetings/implementation_contract_for_review_and_post.md`; `RAW_inputs/meetings/ic_review_package_and_simulated_post.md` | Must-scope ближайшего slice: `ReviewPackage`, evidence, `RiskTier`, absolute veto, stale policy, computed `can_post`, simulated post и audit. |
| [[Wiki/conflicts/2026-06-26-legacy-contract-vs-integrated-flow]] | `RAW_inputs/meetings/ic_review_package_and_simulated_post.md`; user chat 2026-06-26 | Новый contract отдельный и integrated; старый Release 2 artifact остается legacy/reference. |

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
| Sprint Planning Inputs | active | `Wiki/_registry/questions.md` содержит приоритетные вопросы для планирования маленьких спринтов. |

## Current Discovery Queue

Следующий `/discover` должен сфокусироваться на оставшихся human-layer вопросах и sprint-slicing: wording/trust для `Reviewer`, evidence sufficiency, policy-relevant `traceResult` / `subnetworkStatus`, и границы developer demo без production topology engine.

## Current Sprint Planning Queue

Следующий `/plan-sprint` должен использовать 14-дневную рамку, но мыслить маленькими вертикальными increments:

- Первый спринт создает `submit_for_review` и `ReviewPackage` без full topology engine.
- Следующий спринт добавляет reviewer decision и computed `can_post` с negative fixture `DefaultChangedAfterReconcile`.
- Следующий спринт закрывает simulated post, durable audit и zero false-safe gate.

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
