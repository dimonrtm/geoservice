---
title: Reviewer
type: actor
status: active
created: 2026-06-24
updated: 2026-06-24
source: "Vision_wiki/concepts/utility_gis_editing_domain.md; Vision_wiki/decisions/release_2_conflict_explanation.md; RAW_inputs/meetings/implementation_contract_for_review_and_post.md"
tags: [domain-knowledge, actor, review]
confidence: high
related: [Wiki/policies/reviewer_post_policy, Wiki/entities/review_decision, DDD_Wiki/bounded_contexts/review_post]
---

# Reviewer

## Responsibility

`Reviewer` проверяет review package, сетевое последствие, evidence и готовность change package к post. В целевой operating model роль выполняет семантическое `approve package`, но не владеет технической операцией `PostToDefault`.

## Permissions

- Принимает или отклоняет подготовленный package.
- Для `High` принимает финальное содержательное решение по package.
- Для `Critical` не принимает решение единолично: требуется подтверждение профильного специалиста.

## Boundary

В ближайшем вертикальном срезе `Reviewer` семантически разрешает package, а фактический post выполняет demo-system action. В целевой модели технический post переходит к [[Wiki/actors/publisher]] / version administrator.
