---
title: Review Package Approved
type: domain-event
status: planned
created: 2026-06-24
updated: 2026-06-26
source: "Vision_wiki/decisions/release_2_conflict_explanation.md; RAW_inputs/meetings/ic_review_package_and_simulated_post.md"
tags: [domain-knowledge, domain-event, review]
confidence: medium
related: [Wiki/commands/approve_review_package, Wiki/entities/review_decision, DDD_Wiki/aggregates/review_package]
---

# Review Package Approved

## Source Aggregate

`ReviewPackage`.

## Happened In The Past

`Reviewer` принял содержательное решение, что package можно считать approved при текущих evidence и risk tier. Это событие не означает technical post authorization.

## Downstream Reactions

System `post-gate` может вычислить `PostAllowed` / `can_post`; stale rules начинают защищать approval от изменений `Default`, topology-relevant package parts и evidence.
