---
title: Reviewer
type: actor
status: active
created: 2026-06-24
updated: 2026-06-26
source: "Vision_wiki/concepts/utility_gis_editing_domain.md; Vision_wiki/decisions/release_2_conflict_explanation.md; RAW_inputs/meetings/implementation_contract_for_review_and_post.md; RAW_inputs/meetings/ic_review_package_and_simulated_post.md"
tags: [domain-knowledge, actor, review]
confidence: high
related: [Wiki/policies/reviewer_post_policy, Wiki/entities/review_decision, DDD_Wiki/bounded_contexts/review_post]
---

# Reviewer

## Responsibility

`Reviewer` проверяет review package, сетевое последствие, evidence и готовность change package к post. В целевой operating model роль выполняет семантическое `approve package`, но не владеет технической операцией `PostToDefault`.

## Permissions

- Принимает одно из четырех human decisions: `approve package`, `return for changes`, `request evidence`, `escalate`.
- Для `High` принимает финальное содержательное решение по package, если evidence complete и absolute veto отсутствуют.
- Для `Critical` в developer demo завершает workflow через `escalate` как terminal non-goal.

## Boundary

В ближайшем integrated slice `Reviewer` семантически разрешает package, а computed `can_post` и simulated post выполняет system `post-gate`. В целевой модели технический post переходит к [[Wiki/actors/publisher]] / version administrator.
