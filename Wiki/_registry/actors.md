---
title: Actors Registry
type: index
status: active
created: 2026-06-24
updated: 2026-06-26
source: docs/superpowers/specs/2026-06-24-domain-knowledge-layer-design.md
tags: [domain-knowledge, registry, actor]
confidence: n/a
related: [Wiki/index]
---

# Actors Registry

| Actor | Responsibility | Permissions | Confidence | Source |
| --- | --- | --- | --- | --- |
| [[Wiki/actors/editor]] | Открывает назначенную `WorkOrder` и `EditVersion`, готовит изменения. | Только назначенные `WorkOrder` | high | `docs/release_1/sprint_1/2026-06-12-sprint-1-day-1-domain-model-design.md` |
| [[Wiki/actors/reviewer]] | Проверяет package и принимает `approve package`, `return for changes`, `request evidence` или `escalate`. | Semantic decision по review package; не technical post authorization | high | `RAW_inputs/meetings/ic_review_package_and_simulated_post.md` |
| [[Wiki/actors/publisher]] | Целевая technical role; в developer demo заменена system actor `post-gate`. | Simulated post после computed `can_post`; future post в authoritative `Default` | high | `RAW_inputs/meetings/ic_review_package_and_simulated_post.md` |
