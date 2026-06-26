---
title: Legacy Contract Vs Integrated Flow
type: conflict
status: resolved
created: 2026-06-26
updated: 2026-06-26
source: "RAW_inputs/meetings/ic_review_package_and_simulated_post.md; user chat 2026-06-26"
tags: [domain-knowledge, conflict, review-post, implementation-contract]
confidence: high
related: [DDD_Wiki/bounded_contexts/review_post, DDD_Wiki/use_cases/utility_editor_workflow, Wiki/specifications/post_allowed]
---

# Legacy Contract Vs Integrated Flow

## Contradiction

Существующий artifact `docs/release_2/geometry_association_conflict/2026-06-23-implementation-contract-v0.1.md` описывает standalone consequence package вокруг `geometry/association conflict`. Новый источник и ответ пользователя уточняют, что следующий implementation contract должен быть отдельным от legacy artifact и встроенным в уже существующий `WorkOrder` / `EditVersion` flow.

## Blocks

Планирование маленьких спринтов для review/post slice и выбор source of truth для новой реализации.

## Evidence

- Legacy artifact фокусируется на Release 2 `geometry/association conflict` и standalone developer demo package.
- `RAW_inputs/meetings/ic_review_package_and_simulated_post.md` рекомендует полный путь `submit_for_review -> reviewer decision -> computed can_post -> simulated post -> durable audit`.
- Ответ пользователя в чате 2026-06-26: нужен отдельный контракт; старый contract считать legacy; не мыслить релизами, а маленькими спринтами.

## Resolution Question

Должен ли новый review/post contract обновлять legacy Release 2 artifact или быть отдельным контрактом, встроенным в текущий workflow?

## Resolution

Новый review/post implementation contract должен быть отдельным artifact. Старый Release 2 contract остается legacy/reference для сценария `geometry/association conflict`, но не определяет текущую реализацию. Планирование должно идти маленькими спринтами через уже существующий flow: `WorkOrder` -> `EditVersion` -> validation/reconcile -> `ReviewPackage` -> reviewer decision -> computed `can_post` -> simulated post -> durable audit.
