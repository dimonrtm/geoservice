---
title: Utility Editor Workflow
type: use-case
status: active
created: 2026-06-24
updated: 2026-06-24
source: "Vision_wiki/decisions/release_1_utility_workflow.md; docs/release_1/2026-06-11-release-1-utility-workflow-sprints.md"
tags: [domain-knowledge, ddd, use-case]
confidence: high
related: [Wiki/glossary/utility_gis_editing, Wiki/commands/open_edit_version, Wiki/commands/post_to_default]
---

# Utility Editor Workflow

## Scenario

`Editor` входит в систему, видит назначенную `WorkOrder`, открывает `EditVersion`, работает внутри изолированного workspace, выполняет validation/reconcile изменений, разрешает conflicts, отправляет на review, получает approval, а approved result публикуется в authoritative `Default` с audit.

## Current Implemented Slice

Sprint 1 покрывает login, список назначенных `WorkOrder`, открытие `EditVersion` и загрузку workspace.

## Planned Slices

Editing, validation, reconcile/conflict resolution, review/post и audit запланированы на последующие 14-дневные спринты.
