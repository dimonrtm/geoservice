---
title: Post To Default
type: command
status: planned
created: 2026-06-24
updated: 2026-06-26
source: "Vision_wiki/concepts/utility_gis_editing_domain.md; Vision_wiki/decisions/release_2_conflict_explanation.md; Code_wiki/архитектура/data_model.md; RAW_inputs/meetings/implementation_contract_for_review_and_post.md; RAW_inputs/meetings/ic_review_package_and_simulated_post.md"
tags: [domain-knowledge, command, post]
confidence: high
related: [Wiki/entities/default_state, Wiki/policies/stale_approval_policy, Wiki/specifications/post_allowed]
---

# Post To Default

## Actor

`Publisher` / version administrator в целевой модели. В developer demo actor представлен system `post-gate`, который выполняет simulated post после semantic approval от `Reviewer` и successful computed `can_post`.

## Target

Authoritative `Default` / `DefaultState`.

## Preconditions

- Computed `PostAllowed` / `can_post` возвращает true.
- Package семантически approved и не stale.
- `DefaultState.baseNetworkRevision` совпадает с актуальной сетью.
- Нет unresolved conflicts, dirty/error areas или missing mandatory evidence.
- Технический post gate подтверждает freshness, blockers и право публикации.

## Outcome

В developer demo сохраняется simulated post outcome и audit record. В целевой модели одобренный change set публикуется в authoritative `Default` и создает доменное событие [[Wiki/domain_events/authoritative_post_completed]].
