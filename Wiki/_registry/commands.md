---
title: Commands Registry
type: index
status: active
created: 2026-06-24
updated: 2026-06-27
source: docs/superpowers/specs/2026-06-24-domain-knowledge-layer-design.md
tags: [domain-knowledge, registry, command]
confidence: n/a
related: [Wiki/index]
---

# Commands Registry

| Command | Actor | Target | Outcome | Confidence | Source |
| --- | --- | --- | --- | --- | --- |
| [[Wiki/commands/open_edit_version]] | [[Wiki/actors/editor]] | [[Wiki/entities/work_order]] | [[Wiki/domain_events/edit_version_opened]] | high | `Code_wiki/архитектура/api_and_realtime.md` |
| [[Wiki/commands/update_edit_version_feature]] | [[Wiki/actors/editor]] | [[Wiki/entities/edit_version]] | [[Wiki/domain_events/edit_version_feature_updated]]; persisted `operation=updated` и readback diff | high | `RAW_inputs/meetings/increment_after_open_workspace.md` |
| [[Wiki/commands/submit_for_review]] | [[Wiki/actors/editor]] | [[Wiki/entities/edit_version]] | `ReviewPackage` snapshot поверх persisted change set | medium | `RAW_inputs/meetings/ic_review_package_and_simulated_post.md`; `RAW_inputs/meetings/increment_after_open_workspace.md` |
| [[Wiki/commands/approve_review_package]] | [[Wiki/actors/reviewer]] | [[Wiki/entities/review_decision]] | [[Wiki/domain_events/review_package_approved]]; system `post-gate` может вычислить `can_post` | medium | `RAW_inputs/meetings/ic_review_package_and_simulated_post.md` |
| [[Wiki/commands/post_to_default]] | [[Wiki/actors/publisher]] / system `post-gate` | [[Wiki/entities/default_state]] | Simulated post outcome в v0.1; future [[Wiki/domain_events/authoritative_post_completed]] | high | `RAW_inputs/meetings/ic_review_package_and_simulated_post.md` |
