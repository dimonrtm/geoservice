---
title: Authoritative Utility Workflow
type: concept
status: active
created: 2026-06-24
updated: 2026-06-24
source: "Vision_wiki/decisions/release_1_utility_workflow.md; Vision_wiki/concepts/utility_gis_editing_domain.md"
tags: [domain-knowledge, concept, workflow]
confidence: high
related: [Wiki/glossary/utility_gis_editing, DDD_Wiki/use_cases/utility_editor_workflow]
---

# Authoritative Utility Workflow

Authoritative utility workflow - полный пользовательский путь, в котором изменения сети проходят через `WorkOrder`, изолированную edit version, validation, reconcile, conflict resolution, review, post и audit.

## Why It Matters

Этот concept отделяет продуктовый сценарий Release 1 от generic GIS CRUD: пользовательская ценность возникает в безопасном post в authoritative `Default`, а не в факте сохранения геометрии.

## Related Nodes

[[DDD_Wiki/use_cases/utility_editor_workflow]], [[DDD_Wiki/invariants/release1_safety_invariants]], [[Wiki/conflicts/2026-06-24-release1-vs-release2-review-policy]].
