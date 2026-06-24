---
title: Feeder
type: entity
status: active
created: 2026-06-24
updated: 2026-06-24
source: "docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-domain-model-design.md; Code_wiki/архитектура/data_model.md"
tags: [domain-knowledge, entity, utility-network]
confidence: high
related: [Wiki/entities/network_feature, Wiki/entities/network_association, DDD_Wiki/aggregates/work_order, DDD_Wiki/bounded_contexts/utility_network]
---

# Feeder

## Identity

`Feeder` имеет стабильный `id`, уникальный `code` и имя.

## Lifecycle

В Sprint 1 служит устойчивой границей demo dataset и workspace, а не полноценной моделью электрического расчета.

## Responsibilities

Группирует `NetworkFeature` и `NetworkAssociation` в пределах demo utility network.

## Invariants

- Каждый demo `NetworkFeature` принадлежит ровно одному `Feeder`.
- Оба конца association принадлежат тому же `Feeder`.
- Удаление непустого `Feeder` запрещено.
