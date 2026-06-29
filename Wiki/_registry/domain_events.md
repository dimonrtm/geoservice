---
title: Domain Events Registry
type: index
status: active
created: 2026-06-24
updated: 2026-06-29
source: docs/superpowers/specs/2026-06-24-domain-knowledge-layer-design.md
tags: [domain-knowledge, registry, domain-event]
confidence: n/a
related: [Wiki/index]
---

# Domain Events Registry

| Event | Source Aggregate | Reactions | Confidence | Source |
| --- | --- | --- | --- | --- |
| [[Wiki/domain_events/edit_version_opened]] | [[DDD_Wiki/aggregates/work_order]] | Workspace может загрузиться, `WorkOrder` переходит в работу | high | `Code_wiki/архитектура/api_and_realtime.md` |
| [[Wiki/domain_events/edit_version_change_set_persisted]] | [[DDD_Wiki/aggregates/edit_version]] | Readback diff и basic draft validation могут опереться на persisted geometry change set; event эмитится только для ненулевого diff | high | `RAW_inputs/meetings/persisted_edit_slice_EditVersion.md`; `RAW_inputs/meetings/persisted_edit_slice_for_edit_version.md` |
| [[Wiki/domain_events/review_package_approved]] | [[DDD_Wiki/aggregates/review_package]] | System `post-gate` может вычислить `can_post`; approval не равно technical authorization | medium | `RAW_inputs/meetings/ic_review_package_and_simulated_post.md` |
| [[Wiki/domain_events/authoritative_post_completed]] | Граница review/post | Аудит и downstream доверие обновляются | medium | `docs/release_1/2026-06-11-release-1-utility-workflow-sprints.md` |
