---
title: Increment After Open Workspace
type: chat-summary
status: active
created: 2026-06-27
updated: 2026-06-27
source: RAW_inputs/meetings/increment_after_open_workspace.md
tags: [vision-wiki, source-summary, discovery, workspace]
confidence: high
related: [Wiki/conflicts/2026-06-27-review-post-before-edit-persistence, DDD_Wiki/model_health, DDD_Wiki/use_cases/utility_editor_workflow]
---

# Increment After Open Workspace

## Context

Источник отвечает на code-aware discovery-вопросы о ближайшем полноценном инкременте после уже реализованного открытия workspace. Он трактует продукт как workflow вокруг authoritative utility network edit version, а не как generic map CRUD.

## Main Points

- Ближайший vertical slice: workspace -> update existing feature -> persist `operation=updated` -> readback diff -> draft validation flags.
- `ReviewPackage` и `submit_for_review` должны идти после persisted change set, иначе review layer будет опираться на пустой UI snapshot.
- Первая mutation - update существующего feature: geometry и ограниченные editable properties.
- Version-scoped write API должен быть отдельным command-side слоем для workspace edits; `WorkOrderRepository` лучше оставить для открытия edit version и сборки workspace aggregate.
- Новые durable review states пока не нужны; readiness выражается computed predicates.
- Editor summary/evidence до submit живут рядом с `EditVersion`, а при submit копируются в materialized `ReviewPackage` snapshot.
- Associations в первом review должны быть read-only evidence; association mutation откладывается.
- Smoke path сначала расширяется до edit-save-readback, не до submit mock.

## Created Or Updated Nodes

- [[../../Wiki/conflicts/2026-06-27-review-post-before-edit-persistence]]
- [[../../Wiki/commands/update_edit_version_feature]]
- [[../../Wiki/domain_events/edit_version_feature_updated]]
- [[../../Wiki/specifications/edit_version_has_persisted_change_set]]
- [[../../DDD_Wiki/model_health]]
