---
title: Commands Registry
type: index
status: active
created: 2026-06-24
updated: 2026-06-24
source: docs/superpowers/specs/2026-06-24-domain-knowledge-layer-design.md
tags: [domain-knowledge, registry, command]
confidence: n/a
related: [Wiki/index]
---

# Commands Registry

| Command | Actor | Target | Outcome | Confidence | Source |
| --- | --- | --- | --- | --- | --- |
| [[Wiki/commands/open_edit_version]] | [[Wiki/actors/editor]] | [[Wiki/entities/work_order]] | [[Wiki/domain_events/edit_version_opened]] | high | `Code_wiki/архитектура/api_and_realtime.md` |
| [[Wiki/commands/submit_for_review]] | [[Wiki/actors/editor]] | [[Wiki/entities/edit_version]] | Запланированный review package | medium | `Vision_wiki/concepts/utility_gis_editing_domain.md` |
| [[Wiki/commands/approve_review_package]] | [[Wiki/actors/reviewer]] | [[Wiki/entities/review_decision]] | [[Wiki/domain_events/review_package_approved]] | medium | `Vision_wiki/decisions/release_2_conflict_explanation.md` |
| [[Wiki/commands/post_to_default]] | [[Wiki/actors/publisher]] / demo-system action | [[Wiki/entities/default_state]] | [[Wiki/domain_events/authoritative_post_completed]] | high | `RAW_inputs/meetings/implementation_contract_for_review_and_post.md` |
