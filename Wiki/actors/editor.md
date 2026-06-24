---
title: Editor
type: actor
status: active
created: 2026-06-24
updated: 2026-06-24
source: "docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-domain-model-design.md; Vision_wiki/concepts/utility_gis_editing_domain.md"
tags: [domain-knowledge, actor, release-1]
confidence: high
related: [Wiki/entities/work_order, Wiki/commands/open_edit_version, DDD_Wiki/bounded_contexts/work_order]
---

# Editor

## Responsibility

`Editor` получает назначенную `WorkOrder`, открывает `EditVersion`, работает в изолированном workspace и готовит изменения инженерной сети к validation, reconcile и review.

## Permissions

- Видит только назначенные ему `WorkOrder`.
- Может открыть editor workspace только для назначенной `WorkOrder`.
- Не может открыть reviewer workspace и не должен менять authoritative `Default` напрямую.

## Open Questions

Нужно проверить на реальных пользователях, какие действия роли называются `Utility GIS editor`, `GIS editor`, `utility network editor` или другой должностной формулировкой.
