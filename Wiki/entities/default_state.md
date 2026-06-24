---
title: Default State
type: entity
status: active
created: 2026-06-24
updated: 2026-06-24
source: "Code_wiki/архитектура/data_model.md; docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-domain-model-design.md"
tags: [domain-knowledge, entity, default]
confidence: high
related: [Wiki/entities/work_order, Wiki/entities/edit_version, Wiki/commands/post_to_default, DDD_Wiki/aggregates/work_order]
---

# Default State

## Identity

`DefaultState` связан с конкретным `WorkOrder` и хранит `baseNetworkRevision` текущей инженерной сети, от которой сделан baseline-срез.

## Lifecycle

В Sprint 1 имеет статус `active`; автоматический refresh не входит в scope.

## Responsibilities

Предоставляет baseline для создания `EditVersion` и защиты post от публикации поверх изменившегося authoritative состояния.

## Invariants

При post несовпадение `DefaultState.base_network_revision` с текущей актуальной сетью должно блокировать публикацию.
