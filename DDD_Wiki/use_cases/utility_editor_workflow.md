---
title: Utility Editor Workflow
type: use-case
status: active
created: 2026-06-24
updated: 2026-06-27
source: "Vision_wiki/decisions/release_1_utility_workflow.md; docs/release_1/2026-06-11-release-1-utility-workflow-sprints.md; RAW_inputs/meetings/implementation_contract_for_review_and_post.md; RAW_inputs/meetings/ic_review_package_and_simulated_post.md; RAW_inputs/meetings/increment_after_open_workspace.md"
tags: [domain-knowledge, ddd, use-case]
confidence: high
related: [Wiki/glossary/utility_gis_editing, Wiki/commands/open_edit_version, Wiki/commands/post_to_default]
---

# Utility Editor Workflow

## Scenario

`Editor` входит в систему, видит назначенную `WorkOrder`, открывает `EditVersion`, работает внутри изолированного workspace, выполняет validation/reconcile изменений, разрешает conflicts, отправляет package на review, получает semantic approval, проходит computed pre-post gate, а технически разрешенный result публикуется в authoritative `Default` через `Publisher` / system `post-gate` с audit.

## Current Implemented Slice

Sprint 1 покрывает login, список назначенных `WorkOrder`, открытие `EditVersion` и загрузку workspace. Следующий code-aware slice должен расширить этот путь до edit-save-readback: update существующего feature в workspace, сохранение `operation=updated`, readback diff и draft validation flags.

## Planned Slices

Следующий integrated review/post путь должен быть встроен в текущий `WorkOrder` / `EditVersion` flow, но только после persisted change set. Сначала: workspace -> update existing feature -> persist `operation=updated` -> readback diff -> draft validation flags. Затем: `submit_for_review`, package build, reviewer decision, computed `can_post`, simulated post и durable audit. Планирование идет маленькими спринтами; старый standalone Release 2 implementation contract остается reference/legacy source, а не текущим implementation source of truth.
