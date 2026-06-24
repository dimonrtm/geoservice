---
title: Actors Registry
type: index
status: active
created: 2026-06-24
updated: 2026-06-24
source: docs/superpowers/specs/2026-06-24-domain-knowledge-layer-design.md
tags: [domain-knowledge, registry, actor]
confidence: n/a
related: [Wiki/index]
---

# Actors Registry

| Actor | Responsibility | Permissions | Confidence | Source |
| --- | --- | --- | --- | --- |
| [[Wiki/actors/editor]] | Открывает назначенную `WorkOrder` и `EditVersion`, готовит изменения. | Только назначенные `WorkOrder` | high | `docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-domain-model-design.md` |
| [[Wiki/actors/reviewer]] | Проверяет package и принимает/отклоняет готовность к публикации. | Решения по review package | high | `Vision_wiki/decisions/release_2_conflict_explanation.md` |
| [[Wiki/actors/publisher]] | Отвечает за финальную публикацию. | Требует подтверждения | medium | `Vision_wiki/concepts/utility_gis_editing_domain.md` |
