---
title: Edit Version Opened
type: domain-event
status: active
created: 2026-06-24
updated: 2026-06-24
source: "Code_wiki/архитектура/api_and_realtime.md"
tags: [domain-knowledge, domain-event, release-1]
confidence: high
related: [Wiki/commands/open_edit_version, Wiki/entities/edit_version, DDD_Wiki/use_cases/utility_editor_workflow]
---

# Edit Version Opened

## Source Aggregate

`WorkOrder`.

## Happened In The Past

Назначенный `Editor` успешно открыл рабочую версию: новая `EditVersion` создана или существующая open version возвращена повторно.

## Downstream Reactions

Workspace может быть загружен для этой edit version; `WorkOrder` может перейти в `in_progress`; audit должен иметь возможность восстановить начало работы.
