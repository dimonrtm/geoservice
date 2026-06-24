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
| [[Wiki/actors/reviewer]] | Проверяет package и принимает semantic `approve package`. | Решения по review package | high | `RAW_inputs/meetings/implementation_contract_for_review_and_post.md` |
| [[Wiki/actors/publisher]] | Выполняет technical `PostToDefault` / version administrator gate. | Post в authoritative `Default` после `PostAllowed` | high | `RAW_inputs/meetings/implementation_contract_for_review_and_post.md` |
