---
title: Review Post Safety Invariants
type: invariant
status: active
created: 2026-06-24
updated: 2026-06-24
source: "docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-domain-model-design.md; docs/release_1/2026-06-11-release-1-utility-workflow-sprints.md; Vision_wiki/decisions/release_2_conflict_explanation.md; RAW_inputs/meetings/implementation_contract_for_review_and_post.md"
tags: [domain-knowledge, ddd, invariant, review-post]
confidence: high
related: [Wiki/specifications/editor_assigned_to_work_order, Wiki/specifications/post_allowed, Wiki/policies/stale_approval_policy]
---

# Review Post Safety Invariants

## Invariants

- Только назначенный active `Editor` может открыть editor workspace.
- У `WorkOrder` есть не больше одной active `EditVersion`.
- `EditVersion.baseNetworkRevision` фиксируется при создании.
- Workspace не меняет authoritative `Default`.
- Post небезопасен, если validation, reconcile, unresolved conflicts, stale approval или separation-of-duties rules не выполнены.
- Protective failures должны сохранить edit version и предотвратить частичное изменение `Default`.
- `Reviewer` выполняет semantic approval, но не владеет technical `PostToDefault`.
- `Publisher` / demo-system action может выполнить post только после `PostAllowed`.
- `Critical` требует подтверждения профильного специалиста.

## Absolute Veto Cases

- Unresolved или unreviewed conflicts.
- Validation errors или error dirty areas в affected scope.
- Stale package или stale approval.
- Изменение `Default` после package build, требующее нового reconcile.
- Unresolved association delta.
- Trace, который недостоверен из-за dirty areas.
- Invalid/dirty subnetwork в затронутой области.
- Missing required evidence для `High`/`Critical`.
