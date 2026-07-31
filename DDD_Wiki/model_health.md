---
title: Model Health
type: state
status: active
created: 2026-06-24
updated: 2026-07-31
source: "docs/superpowers/specs/2026-06-24-domain-knowledge-layer-design.md; Vision_wiki/concepts/utility_gis_editing_domain.md; Code_wiki/архитектура/data_model.md; RAW_inputs/meetings/implementation_contract_for_review_and_post.md; RAW_inputs/meetings/ic_review_package_and_simulated_post.md; RAW_inputs/meetings/increment_after_open_workspace.md; RAW_inputs/meetings/persisted_edit_slice_EditVersion.md; RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md; RAW_inputs/meetings/first_save_edit_version.md; RAW_inputs/meetings/first_save_for_edit_version.md; RAW_inputs/meetings/tolerance_rules.md; RAW_inputs/meetings/demo_utility_gis.md"
tags: [domain-knowledge, ddd, health]
confidence: high
related: [DDD_Wiki/index, Wiki/_registry/conflicts, Wiki/_registry/questions]
---

# Model Health

## Current Summary

Первичная доменная модель создана вокруг core subdomain `Utility Authoritative Editing`: `WorkOrder`, `EditVersion`, рабочее пространство, проверка, review/post и audit. Discovery answers закрыли поведение first-save contract, но фактические demo metadata и fixture ещё не выбраны. Ближайшая реализация должна доказать путь workspace -> `UpdateEditVersionFeatureGeometry` -> сдвиг ровно одной внутренней вершины одной существующей line feature -> server-side canonicalization по metadata dataset -> atomic save full resulting snapshot относительно единого базового состояния работы -> command response + persisted readback -> revert к baseline. Line должна быть valid/simple и `covered by` AOI; endpoints, structure, attributes и associations заморожены. Позиционная точность для приёмки берётся из утверждённой спецификации и evidence, coordinate grid — из spatial-reference metadata dataset; это разные правила. `POSITIONAL_ACCURACY_UNVERIFIED` разрешает technical save, но блокирует review/completion/post. `DraftVersionToken` защищает весь aggregate, а `CommandId` идентифицирует одну operation на весь lifecycle `EditVersion`, включая concurrent retry и повтор terminal rejection. `EditVersionChangeSetPersisted` возникает на каждый content-changing save с непустым diff и хранит line identity + before/after + actor/time/baseline/command evidence; `EditVersionChangeSetCleared` возникает на revert; no-op/retry событий не создают. First-save readiness называется `persisted-draft-ready`: lifecycle остается `open`, topology - `not_checked`, review/post остается downstream context.

## Current Blocking Conflicts

| Conflict | Blocks | Status | Next Question |
| --- | --- | --- | --- |
| Нет активных blocking conflicts после ingest `demo_utility_gis.md` | - | clear | Найти утверждённую accuracy specification, прочитать фактические spatial metadata и выбрать eligible demo line/vertex fixture |

## Recently Resolved Conflicts

| Conflict | Resolution Source | Result |
| --- | --- | --- |
| [[Wiki/conflicts/2026-06-24-reviewer-vs-publisher]] | `RAW_inputs/meetings/implementation_contract_for_review_and_post.md`; `RAW_inputs/meetings/ic_review_package_and_simulated_post.md` | `Publisher` отделен от `Reviewer`; developer demo использует system `post-gate` для simulated technical post после computed `can_post`. |
| [[Wiki/conflicts/2026-06-24-release1-vs-release2-review-policy]] | `RAW_inputs/meetings/implementation_contract_for_review_and_post.md`; `RAW_inputs/meetings/ic_review_package_and_simulated_post.md`; `RAW_inputs/meetings/increment_after_open_workspace.md` | Review/post remains required downstream scope, но ближайший code slice сначала закрывает persisted edit change set. |
| [[Wiki/conflicts/2026-06-26-legacy-contract-vs-integrated-flow]] | `RAW_inputs/meetings/ic_review_package_and_simulated_post.md`; user chat 2026-06-26 | Новый contract отдельный и integrated; старый Release 2 artifact остается legacy/reference. |
| [[Wiki/conflicts/2026-06-27-review-post-before-edit-persistence]] | `RAW_inputs/meetings/increment_after_open_workspace.md`; `RAW_inputs/meetings/persisted_edit_slice_EditVersion.md`; `RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md` | Ближайший sprint начинается с persisted geometry diff existing line feature и edit-save-readback; `ReviewPackage`, `can_post`, simulated post, full audit, trace/subnetwork evidence, risk tiers, reviewer queue, endpoint rewiring и association mutation откладываются. |
| [[Wiki/conflicts/2026-07-25-edit-version-event-cadence]] | `RAW_inputs/meetings/first_save_edit_version.md`; `RAW_inputs/meetings/first_save_for_edit_version.md` | `EditVersionChangeSetPersisted` эмитится на каждый content-changing save с непустым diff; revert создает `EditVersionChangeSetCleared`; no-op/retry событий не создают. |

## Current Coverage

| Area | Status | Notes |
| --- | --- | --- |
| Ubiquitous Language | active | [[Wiki/glossary/utility_gis_editing]], [[Wiki/glossary/positional_accuracy_for_acceptance]], [[Wiki/glossary/coordinate_storage_precision]] и [[Wiki/glossary/base_work_state]] закрепляют язык workflow, точности и baseline. |
| Subdomains | active | Core subdomain [[DDD_Wiki/subdomains/utility_authoritative_editing]] отделен от generic map editing. |
| Bounded Contexts | active | Выделены контексты Work Order, Utility Network, Review Post, Audit и Auth. |
| Context Map | active | [[DDD_Wiki/context_map/geoservice_context_map]] описывает upstream/downstream и границу application layer. |
| Aggregates | active | `WorkOrder`, `EditVersion` и `ReviewPackage` активны в доменной модели. |
| Commands And Events | active | `OpenEditVersion` активна; first write command - `UpdateEditVersionFeatureGeometry`; события `EditVersionChangeSetPersisted` и `EditVersionChangeSetCleared` описывают save/revert, `CommandId` отделяет retry от concurrency. |
| Policies And Specifications | active | Проверка назначения, [[Wiki/policies/edit_geometry_precision_policy]], [[Wiki/policies/positional_accuracy_acceptance_policy]], persisted change set, basic draft validation, ready-for-review, post allowed, review/post и stale policies активны. |
| Sprint Planning Inputs | active | `Wiki/_registry/questions.md` содержит приоритетные вопросы для планирования маленьких спринтов. |

## Current Discovery Queue

Основные доменные развилки first save закрыты. Следующий `/discover` не должен заново спрашивать snapshot-vs-diff, one-internal-vertex guard, AOI boundary, token/idempotency semantics, event cadence, baseline naming/mapping или состав event evidence. Открыты четыре точечных implementation/model choice:

- Как называется утверждённая спецификация продукта данных, какова её версия, область действия и числовой positional tolerance?
- Какие фактические CRS, coordinate unit, `xyResolution`, `xyTolerance`, origin/domain и transformations имеет сохраняющий demo dataset?
- Какая текущая demo line имеет eligible внутреннюю shape vertex и какие before/after fixture coordinates используются? Текущий seed-контекст такого объекта не подтверждает.
- Какой records policy задаёт долгосрочный срок хранения immutable save-operation history после закрытия `EditVersion`?

Human-layer вопросы по `Reviewer`, evidence sufficiency, policy-relevant `traceResult` / `subnetworkStatus` важны после реализации persisted draft path.

## Current Sprint Planning Queue

Следующий `/plan-sprint` должен использовать 14-дневную рамку, но мыслить маленькими вертикальными increments:

- Первый спринт после открытия workspace создает end-to-end first-save slice для одной line feature и одной внутренней вершины: сначала фиксирует реальную editable fixture и spatial metadata dataset, затем добавляет единое immutable базовое состояние работы + current snapshot, AOI `CoveredBy`, server-side canonical single-vertex normalization, hard atomic guards, явный `POSITIONAL_ACCURACY_UNVERIFIED`, aggregate `DraftVersionToken`, lifecycle registry `CommandId`, before/after event evidence, response/readback proof, no-op semantics, stale recovery и revert с двумя domain events.
- Следующий спринт добавляет `submit_for_review` и `ReviewPackage v0.1` как materialized snapshot поверх persisted `edit_version_features`, с backrefs на исходные rows и editor summary/evidence.
- Следующий спринт добавляет reviewer detail view одного package, reviewer decision и computed `can_post`; simulated post, durable audit, trace/subnetwork evidence, risk tiers, reviewer queue и association mutation не должны стартовать раньше persisted change set.

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
