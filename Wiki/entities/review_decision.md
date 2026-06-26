---
title: Review Decision
type: entity
status: active
created: 2026-06-24
updated: 2026-06-26
source: "Vision_wiki/decisions/release_2_conflict_explanation.md; RAW_inputs/meetings/implementation_contract_for_review_and_post.md; RAW_inputs/meetings/ic_review_package_and_simulated_post.md"
tags: [domain-knowledge, entity, review, release-2]
confidence: high
related: [Wiki/actors/reviewer, Wiki/policies/reviewer_post_policy, DDD_Wiki/aggregates/review_package]
---

# Review Decision

## Identity

`ReviewDecision` связан с package id, actor role, timestamps, decision scope, rationale, risk tier, blockers, completeness flags, stale events и final post outcome.

## Lifecycle

Минимальная state machine различает `draft`, `ready_for_review`, `under_review`, `approved`, `returned`, `escalated`, `stale`, `can_post`, `blocked_post` и `simulated_posted`. `can_post` является вычисляемой спецификацией, а не durable authorization state.

## Responsibilities

Фиксирует human decision по change package и отделяет `approve package` от технического `can_post`.

## Audit Boundary

Domain audit хранит package/work order/edit version ids, actor, role, decision, rationale, risk tier at decision, blocker snapshot, stale events, evidence refs/checksums, freshness snapshot, pre-post result и simulated/final post outcome. Timings, correlation id, retries и debug refs относятся к telemetry/observability.
