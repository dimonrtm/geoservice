---
title: Editor Assigned To Work Order
type: specification
status: active
created: 2026-06-24
updated: 2026-06-24
source: "docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-domain-model-design.md; Code_wiki/архитектура/api_and_realtime.md"
tags: [domain-knowledge, specification, authorization]
confidence: high
related: [Wiki/actors/editor, Wiki/entities/work_order, Wiki/commands/open_edit_version]
---

# Editor Assigned To Work Order

## Predicate

Текущий active user имеет роль `Editor` и является assignee указанной `WorkOrder`.

## Failure Meaning

Пользователь не может открыть edit version или workspace; API возвращает not found/role/state error по текущему contract.

## Used By

`OpenEditVersion`, `WorkspaceLoaded`, список `WorkOrder` и workspace authorization.
