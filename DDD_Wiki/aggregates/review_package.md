---
title: Review Package Aggregate
type: aggregate
status: active
created: 2026-06-24
updated: 2026-06-26
source: "Vision_wiki/decisions/release_2_conflict_explanation.md; RAW_inputs/meetings/implementation_contract_for_review_and_post.md; RAW_inputs/meetings/ic_review_package_and_simulated_post.md"
tags: [domain-knowledge, ddd, aggregate, review]
confidence: high
related: [Wiki/entities/review_decision, Wiki/value_objects/risk_tier, Wiki/policies/reviewer_post_policy]
---

# Review Package Aggregate

## Aggregate Root

`ReviewPackage` - aggregate root для consequence-first decision support перед post. Он имеет собственную идентичность, built-from state и связывает `EditVersion`, current/default snapshot, evidence, risk tier, blockers, review decision, stale status и post gate.

## Consistency Boundary

Package snapshot, evidence, risk tier, blockers, approval и stale status должны быть согласованы для конкретного reconcile/default state. Без отдельного aggregate stale invalidation, repeat review и audit расползаются по ad hoc полям `EditVersion`.

## V0.1 Slice

Новый integrated contract должен проверять полный путь `submit_for_review -> reviewer decision -> computed can_post -> simulated post -> durable audit`, а не standalone package preview. `can_post` вычисляется на чтении; durable truth хранится в audit как snapshot pre-post check и simulated post outcome.

## Minimal Required Fields

Обязательное decision-proof ядро: `packageId`, `workOrderId`, `editVersionId`, snapshot/version refs для `Mine` / `Default` / `Base`, `riskTier`, `blockers[]`, `evidenceCompleteness`, `associationDelta`, `validationSummary`, `freshnessSnapshot`, reviewer-facing rationale summary и evidence refs/checksums. `traceResult` и `subnetworkStatus` обязательны только when policy-relevant.

## Protected Invariants

- `approve package` не равно `can_post`.
- Stale approval блокирует simulated/technical post.
- Число false-safe verdict должно оставаться нулевым для absolute veto scenarios.
- `ReviewPackage` фиксирует evidence snapshot checksum и не переписывает прежний risk tier незаметно; новое evidence создает новый или stale package state.
