---
title: Workspace Loaded
type: system-event
status: active
created: 2026-06-24
updated: 2026-06-24
source: "Code_wiki/архитектура/api_and_realtime.md; Code_wiki/архитектура/data_model.md"
tags: [domain-knowledge, system-event, api]
confidence: high
related: [Wiki/entities/work_order, Wiki/entities/edit_version, Wiki/value_objects/aoi]
---

# Workspace Loaded

## Producer

`GET /api/v1/work-orders/{workOrderId}/edit-versions/{editVersionId}/workspace`.

## Consumers

Frontend workspace редактора.

## Meaning

Система прочитала `WorkOrder`, `EditVersion`, `AOI`, filtered features и associations для существующей open edit version. Событие техническое: оно не открывает `WorkOrder` и не создает `EditVersion`.
