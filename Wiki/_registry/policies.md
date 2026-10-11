---
title: Policies Registry
type: index
status: active
created: 2026-06-24
updated: 2026-10-12
source: docs/superpowers/specs/2026-06-24-domain-knowledge-layer-design.md
tags: [domain-knowledge, registry, policy]
confidence: n/a
related: [Wiki/index]
---

# Policies Registry

| Policy | Rule | Decision Outcome | Confidence | Source |
| --- | --- | --- | --- | --- |
| [[Wiki/policies/editor_recovery_policy]] | Принято 2026-10-12: удерживать намерение, выяснять неизвестный исход, не затирать свежую геометрию старым ответом | Сравнение, прежний retry либо новое явное намерение | high | `RAW_inputs/research_results/2026-10-11-utility-gis-editor-save-recovery-research.md` |
| [[Wiki/policies/geometry_quality_escalation_policy]] | Принято 2026-10-12: запрет нулевых XY-сегментов и отдельное исправление исходных дефектов | Исправить candidate либо передать дефект ответственному | high | `RAW_inputs/research_results/2026-10-11-utility-gis-editor-save-recovery-research.md` |
| [[Wiki/policies/change_history_retention_policy]] | Принято 2026-10-12: срок history задаёт records policy организации; число лет не определено | Утвердить срок и исключения; вопрос остаётся открыт | high | `RAW_inputs/research_results/2026-10-11-utility-gis-editor-save-recovery-research.md` |
| [[Wiki/policies/edit_geometry_precision_policy]] | Канонизировать server-side только изменённую вершину по metadata сохраняющего dataset, затем проверить hard guards; не выполнять скрытый snapping или full-line renormalization. | changed/no-op/rejected | high | `RAW_inputs/meetings/tolerance_rules.md`; `RAW_inputs/meetings/demo_utility_gis.md` |
| [[Wiki/policies/positional_accuracy_acceptance_policy]] | Разрешить technical save с `POSITIONAL_ACCURACY_UNVERIFIED`, но требовать утверждённую specification и independent evidence до review/completion/post. | verified/unverified/exceeded | high | `RAW_inputs/meetings/demo_utility_gis.md` |
| [[Wiki/policies/reviewer_post_policy]] | `Reviewer` принимает `approve package`, `return for changes`, `request evidence` или `escalate`; stale/block вычисляет система. | approved/returned/evidence_requested/escalated | high | `RAW_inputs/meetings/ic_review_package_and_simulated_post.md` |
| [[Wiki/policies/stale_approval_policy]] | Изменения `Default`, geometry, association, network attribute, terminal config, validation, trace/subnetwork или evidence делают approval устаревшим. | Repeat review или recompute package | high | `RAW_inputs/meetings/ic_review_package_and_simulated_post.md` |
