---
title: Publisher
type: actor
status: active
created: 2026-06-24
updated: 2026-06-26
source: "Vision_wiki/concepts/utility_gis_editing_domain.md; Vision_wiki/decisions/release_2_conflict_explanation.md; RAW_inputs/meetings/implementation_contract_for_review_and_post.md; RAW_inputs/meetings/ic_review_package_and_simulated_post.md"
tags: [domain-knowledge, actor, conflict]
confidence: high
related: [Wiki/conflicts/2026-06-24-reviewer-vs-publisher, Wiki/commands/post_to_default, DDD_Wiki/bounded_contexts/review_post]
---

# Publisher

## Responsibility

`Publisher` - отдельная техническая роль, которая отвечает за финальную интеграцию одобренного change set в authoritative `Default`.

## Permissions

В целевой модели владеет операцией `PostToDefault` и финальной технической проверкой freshness, blockers и прав на post. В developer demo представлен system actor `post-gate`, который выполняет simulated post только после reviewer decision и computed `can_post`; это не делает `Reviewer` владельцем authoritative state.

## Boundary

`Data Owner` задает policy, risk matrix и делегирование полномочий, но не выполняет routine post. `Reviewer` принимает semantic package verdict, а `Publisher` / version administrator выполняет technical post gate.
