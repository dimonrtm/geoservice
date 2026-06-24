---
title: Reviewer
type: actor
status: active
created: 2026-06-24
updated: 2026-06-24
source: "Vision_wiki/concepts/utility_gis_editing_domain.md; Vision_wiki/decisions/release_2_conflict_explanation.md"
tags: [domain-knowledge, actor, review]
confidence: high
related: [Wiki/policies/reviewer_post_policy, Wiki/entities/review_decision, DDD_Wiki/bounded_contexts/review_post]
---

# Reviewer

## Responsibility

`Reviewer` проверяет review package, сетевое последствие, evidence и готовность change package к post. Для Release 2 роль означает содержательное approval change package перед публикацией.

## Permissions

- Принимает или отклоняет подготовленный package.
- Для `High` принимает финальное содержательное решение по package.
- Для `Critical` может требоваться dual control с профильным специалистом или data owner.

## Open Questions

Для Release 1 и Release 2 нужно развести, где `Reviewer` только выполняет `approve package`, а где он также выполняет или authorizes post.
