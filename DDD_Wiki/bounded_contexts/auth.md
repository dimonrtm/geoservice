---
title: Auth Context
type: bounded-context
status: active
created: 2026-06-24
updated: 2026-06-24
source: "Code_wiki/архитектура/api_and_realtime.md; docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-domain-model-design.md"
tags: [domain-knowledge, ddd, bounded-context, auth]
confidence: high
related: [Wiki/actors/editor, Wiki/actors/reviewer, DDD_Wiki/bounded_contexts/work_order]
---

# Auth Context

## Ubiquitous Language Boundary

`User`, `role`, `active user`, `Editor`, `Reviewer`, token и role authorization входят в язык auth.

## Model Ownership

Auth владеет identity и role claims. Назначение `WorkOrder` остается в [[DDD_Wiki/bounded_contexts/work_order]].

## Interfaces

Предоставляет API текущего active user и role; контекст work order проверяет assignment authorization.
