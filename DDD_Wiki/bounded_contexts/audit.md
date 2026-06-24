---
title: Audit Context
type: bounded-context
status: planned
created: 2026-06-24
updated: 2026-06-24
source: "Vision_wiki/decisions/release_2_conflict_explanation.md; docs/release_1/2026-06-11-release-1-utility-workflow-sprints.md"
tags: [domain-knowledge, ddd, bounded-context, audit]
confidence: medium
related: [Wiki/domain_events/authoritative_post_completed, Wiki/entities/review_decision, DDD_Wiki/bounded_contexts/review_post]
---

# Audit Context

## Ubiquitous Language Boundary

`Audit trail`, `actor`, `action`, `work order/version`, `decision`, `stale event`, `post outcome` и флаги полноты evidence входят в язык аудита.

## Model Ownership

Контекст хранит устойчивый след решений и post outcomes. Он не решает, безопасен ли package; он фиксирует, почему решение было принято.

## Interfaces

Получает domain events из review/post workflow и предоставляет реконструкцию для support, validation и demo evidence.
