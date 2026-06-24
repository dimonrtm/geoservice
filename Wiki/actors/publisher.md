---
title: Publisher
type: actor
status: needs-review
created: 2026-06-24
updated: 2026-06-24
source: "Vision_wiki/concepts/utility_gis_editing_domain.md; Vision_wiki/decisions/release_2_conflict_explanation.md"
tags: [domain-knowledge, actor, conflict]
confidence: medium
related: [Wiki/conflicts/2026-06-24-reviewer-vs-publisher, Wiki/commands/post_to_default, DDD_Wiki/bounded_contexts/review_post]
---

# Publisher

## Responsibility

`Publisher` отвечает за финальную публикацию одобренного change set в authoritative `Default`.

## Permissions

В полной модели может быть отдельной организационной ролью. В упрощенном Release 1 ответственность может временно нести `Reviewer`.

## Open Questions

Нужно подтвердить, является ли `Publisher` отдельной ролью, ответственностью data owner или технической операцией внутри reviewer/post workflow.
