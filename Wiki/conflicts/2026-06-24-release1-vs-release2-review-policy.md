---
title: Release 1 Vs Release 2 Review Policy
type: conflict
status: resolved
created: 2026-06-24
updated: 2026-06-24
source: "docs/release_1/2026-06-11-release-1-utility-workflow-sprints.md; Vision_wiki/decisions/release_2_conflict_explanation.md; RAW_inputs/meetings/implementation_contract_for_review_and_post.md"
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

Новый источник предлагает решать вопрос не по названию релиза, а через целевую operating model и ближайший вертикальный срез. В ближайшие 14 дней как `must` входят: узкий `ReviewPackage` aggregate, минимальный evidence package, трехуровневый `RiskTier`, hard blockers с absolute veto, ограниченная `StaleApprovalPolicy` и audit с двумя решениями `approve package` / `can post`. Later остаются rich routing, richer trace explanations, repeat-review UX, sample-review policy и полноценный human `Publisher` desk. Out of scope остаются production-parity topology engine, full native conflict resolver, batch review queue, SLA-механика и claims про production-safe post без real validation.
