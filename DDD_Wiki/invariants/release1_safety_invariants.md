---
title: Release 1 Safety Invariants
type: invariant
status: active
created: 2026-06-24
updated: 2026-06-24
source: "docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-domain-model-design.md; docs/release_1/2026-06-11-release-1-utility-workflow-sprints.md; Vision_wiki/decisions/release_2_conflict_explanation.md"
tags: [domain-knowledge, ddd, invariant, release-1]
confidence: high
related: [Wiki/specifications/editor_assigned_to_work_order, Wiki/specifications/post_allowed, Wiki/policies/stale_approval_policy]
---

# Release 1 Safety Invariants

## Invariants

- Только назначенный active `Editor` может открыть editor workspace.
- У `WorkOrder` есть не больше одной active `EditVersion`.
- `EditVersion.baseNetworkRevision` фиксируется при создании.
- Workspace не меняет authoritative `Default`.
- Post небезопасен, если validation, reconcile, unresolved conflicts, stale approval или separation-of-duties rules не выполнены.
- Protective failures должны сохранить edit version и предотвратить частичное изменение `Default`.

## Risk

Release 2 добавляет более строгую stale/blocker semantics, которая может выходить за текущий scope реализации Release 1.
