---
title: Release 1 Vs Release 2 Review Policy
type: conflict
status: resolved
created: 2026-06-24
updated: 2026-06-26
source: "docs/release_1/2026-06-11-release-1-utility-workflow-sprints.md; Vision_wiki/decisions/release_2_conflict_explanation.md; RAW_inputs/meetings/implementation_contract_for_review_and_post.md; RAW_inputs/meetings/ic_review_package_and_simulated_post.md"
tags: [domain-knowledge, conflict, release-1, release-2]
confidence: high
related: [Wiki/policies/reviewer_post_policy, Wiki/policies/stale_approval_policy, DDD_Wiki/model_health]
---

# Release 1 Vs Release 2 Review Policy

## Contradiction

Release 1 описывает end-to-end path до review/post как future product increment, а Release 2 уже вводит detailed consequence package, stale approval, blockers, risk tiers и audit semantics. Эти правила полезны, но их нельзя автоматически считать обязательными для реализации Release 1.

## Blocks

Единую непротиворечивую state machine review/post и планирование ближайшего 14-дневного спринта.

## Evidence

- Roadmap Release 1 фокусируется на последовательных sprint increments.
- Decision Release 2 фиксирует pre-post decision-support layer и множество hard blockers.

## Resolution Question

Какие правила Release 2 должны стать частью ближайшего path Release 1, а какие остаются отдельным future context?

## Resolution

Новые источники предлагают решать вопрос не по названию релиза, а через целевую operating model и ближайшие маленькие спринты. Следующий отдельный contract должен встраиваться в существующий `WorkOrder` / `EditVersion` flow и покрывать полный путь `submit_for_review -> reviewer decision -> computed can_post -> simulated post -> durable audit`. `ReviewPackage`, safety-complete blockers, stale invalidation, computed `can_post`, audit decision proof и zero false-safe gate входят в must-scope. Старый standalone Release 2 artifact остается legacy/reference; production-parity topology engine, full native conflict resolver, batch review queue, SLA-механика, websocket для stale events и claims про production-safe post остаются вне scope без real validation.
