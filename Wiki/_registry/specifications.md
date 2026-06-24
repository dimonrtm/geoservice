---
title: Specifications Registry
type: index
status: active
created: 2026-06-24
updated: 2026-06-24
source: docs/superpowers/specs/2026-06-24-domain-knowledge-layer-design.md
tags: [domain-knowledge, registry, specification]
confidence: n/a
related: [Wiki/index]
---

# Specifications Registry

| Specification | Predicate | Failure Meaning | Confidence | Source |
| --- | --- | --- | --- | --- |
| [[Wiki/specifications/editor_assigned_to_work_order]] | Текущий активный editor является назначенным исполнителем. | Нельзя открыть edit version/workspace. | high | `Code_wiki/архитектура/api_and_realtime.md` |
| [[Wiki/specifications/edit_version_ready_for_review]] | Последний reconcile с текущим `Default`, нет unresolved conflicts, validation clean от veto, evidence и editor summary готовы. | Review преждевременен или blocked. | high | `RAW_inputs/meetings/implementation_contract_for_review_and_post.md` |
| [[Wiki/specifications/post_allowed]] | Package approved, не stale, blockers отсутствуют, `Default` fresh, evidence соответствует risk tier, technical gate пройден. | Post заблокирован. | high | `RAW_inputs/meetings/implementation_contract_for_review_and_post.md` |
