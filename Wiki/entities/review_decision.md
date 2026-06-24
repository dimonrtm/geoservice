---
title: Review Decision
type: entity
status: planned
created: 2026-06-24
updated: 2026-06-24
source: "Vision_wiki/decisions/release_2_conflict_explanation.md"
tags: [domain-knowledge, entity, review, release-2]
confidence: medium
related: [Wiki/actors/reviewer, Wiki/policies/reviewer_post_policy, DDD_Wiki/aggregates/review_package]
---

# Review Decision

## Identity

`ReviewDecision` должен быть связан с package id, actor role, timestamps, risk tier, blockers, полнотой evidence и final post outcome.

## Lifecycle

Release 2 вводит состояния package/approval: draft package, ready for review, approved, stale, blocked post, escalated, repeated review.

## Responsibilities

Фиксирует human decision по change package и отделяет `approve package` от технического `can post`.

## Open Questions

Нужна точная schema/API contract в implementation contract v0.1.
