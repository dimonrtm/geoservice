---
title: Post To Default
type: command
status: planned
created: 2026-06-24
updated: 2026-06-24
source: "Vision_wiki/concepts/utility_gis_editing_domain.md; Vision_wiki/decisions/release_2_conflict_explanation.md; Code_wiki/архитектура/data_model.md; RAW_inputs/meetings/implementation_contract_for_review_and_post.md"
tags: [domain-knowledge, command, post]
confidence: high
related: [Wiki/entities/default_state, Wiki/policies/stale_approval_policy, Wiki/specifications/post_allowed]
---

# Post To Default

## Actor

`Publisher` / version administrator в целевой модели. В ближайшем вертикальном срезе actor может быть demo-system action после semantic approval от `Reviewer`.

## Target

Authoritative `Default` / `DefaultState`.

## Preconditions

- `PostAllowed` возвращает true.
- Package семантически approved и не stale.
- `DefaultState.baseNetworkRevision` совпадает с актуальной сетью.
- Нет unresolved conflicts, dirty/error areas или missing mandatory evidence.
- Технический post gate подтверждает freshness, blockers и право публикации.

## Outcome

Одобренный change set публикуется в authoritative `Default`, создается audit record и доменное событие [[Wiki/domain_events/authoritative_post_completed]].
