---
title: Open Edit Version
type: command
status: active
created: 2026-06-24
updated: 2026-06-24
source: "Code_wiki/архитектура/api_and_realtime.md; docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-domain-model-design.md"
tags: [domain-knowledge, command, release-1]
confidence: high
related: [Wiki/entities/work_order, Wiki/entities/edit_version, Wiki/specifications/editor_assigned_to_work_order]
---

# Open Edit Version

## Actor

Назначенный `Editor`.

## Target

Агрегат `WorkOrder` и его active `DefaultState`.

## Preconditions

- `EditorAssignedToWorkOrder` возвращает true.
- `WorkOrder` существует и имеет допустимый статус.
- У `WorkOrder` нет другой active open edit version, либо ее нужно вернуть повторно.

## Outcome

Создается или возвращается `EditVersion`, фиксируется `baseNetworkRevision`, `WorkOrder` переводится `assigned -> in_progress`, публикуется факт [[Wiki/domain_events/edit_version_opened]].
