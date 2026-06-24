---
title: Utility Editor Workflow
type: use-case
status: active
created: 2026-06-24
updated: 2026-06-24
source: "Vision_wiki/decisions/release_1_utility_workflow.md; docs/release_1/2026-06-11-release-1-utility-workflow-sprints.md; RAW_inputs/meetings/implementation_contract_for_review_and_post.md"
tags: [domain-knowledge, ddd, use-case]
confidence: high
related: [Wiki/glossary/utility_gis_editing, Wiki/commands/open_edit_version, Wiki/commands/post_to_default]
---

# Utility Editor Workflow

## Scenario

`Editor` входит в систему, видит назначенную `WorkOrder`, открывает `EditVersion`, работает внутри изолированного workspace, выполняет validation/reconcile изменений, разрешает conflicts, отправляет package на review, получает semantic approval, проходит stale/blocker recheck, а технически разрешенный result публикуется в authoritative `Default` через `Publisher` / demo-system action с audit.

## Current Implemented Slice

Sprint 1 покрывает login, список назначенных `WorkOrder`, открытие `EditVersion` и загрузку workspace.

## Planned Slices

Следующий целевой срез должен проверить review/post end-to-end: package build, reviewer decision, stale/blocker recheck, simulated post и audit outcome.
