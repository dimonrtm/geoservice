---
title: Review Decision
type: entity
status: active
created: 2026-06-24
updated: 2026-06-24
source: "Vision_wiki/decisions/release_2_conflict_explanation.md; RAW_inputs/meetings/implementation_contract_for_review_and_post.md"
tags: [domain-knowledge, entity, review, release-2]
confidence: high
related: [Wiki/actors/reviewer, Wiki/policies/reviewer_post_policy, DDD_Wiki/aggregates/review_package]
---

# Review Decision

## Identity

`ReviewDecision` связан с package id, actor role, timestamps, decision scope, rationale, risk tier, blockers, completeness flags, stale events и final post outcome.

## Lifecycle

Минимальная state machine различает `ready_for_review`, `approved_package`, `post_authorized`, `posted`, а также поперечные состояния `blocked`, `stale` и `escalated`.

## Responsibilities

Фиксирует human decision по change package и отделяет `approve package` от технического `can post`.

## Audit Boundary

Domain audit хранит package/work order/edit version ids, actor, role, decision, rationale, risk tier, blocker flags, stale events, evidence snapshot checksum, trace/subnetwork freshness verdict и final post outcome. Timings, correlation id и retry counters относятся к telemetry/debug.
