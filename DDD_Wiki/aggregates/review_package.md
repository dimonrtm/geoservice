---
title: Review Package Aggregate
type: aggregate
status: active
created: 2026-06-24
updated: 2026-11-09
source: "Vision_wiki/decisions/release_2_conflict_explanation.md; RAW_inputs/meetings/implementation_contract_for_review_and_post.md; RAW_inputs/meetings/ic_review_package_and_simulated_post.md; RAW_inputs/meetings/increment_after_open_workspace.md; RAW_inputs/research_results/2026-11-09-utility-gis-editor-publication-answers.md"
tags: [domain-knowledge, ddd, aggregate, review]
confidence: high
related: [Wiki/entities/review_decision, Wiki/value_objects/risk_tier, Wiki/policies/reviewer_post_policy, Wiki/policies/review_package_withdrawal_policy, Wiki/policies/published_result_correction_policy]
---

# Review Package Aggregate

## Aggregate Root

`ReviewPackage` - aggregate root для consequence-first decision support перед post. Он имеет собственную идентичность, built-from state и связывает `EditVersion`, current/default snapshot, evidence, risk tier, blockers, review decision, stale status и post gate.

## Consistency Boundary

Package snapshot, evidence, risk tier, blockers, approval и stale status должны быть согласованы для конкретного reconcile/default state. Без отдельного aggregate stale invalidation, repeat review и audit расползаются по ad hoc полям `EditVersion`.

## V0.1 Slice

`ReviewPackage v0.1` появляется только после persisted change set в `EditVersion`. Он должен быть materialized snapshot поверх `edit_version_features` / `edit_version_associations` с backrefs на исходные rows, а не live-ссылка на временное UI-состояние. После этого integrated contract проверяет путь `submit_for_review -> reviewer decision -> computed can_post -> simulated post -> durable audit`, а не standalone package preview. `can_post` вычисляется на чтении; durable truth хранится в audit как snapshot pre-post check и simulated post outcome.

## Minimal Required Fields

Обязательное decision-proof ядро: `packageId`, `workOrderId`, `editVersionId`, snapshot/version refs для `Mine` / `Default` / `Base`, `riskTier`, `blockers[]`, `evidenceCompleteness`, `associationDelta`, `validationSummary`, `freshnessSnapshot`, reviewer-facing rationale summary и evidence refs/checksums. `traceResult` и `subnetworkStatus` обязательны только when policy-relevant.

## Protected Invariants

- `approve package` не равно `can_post`.
- Stale approval блокирует simulated/technical post.
- Число false-safe verdict должно оставаться нулевым для absolute veto scenarios.
- `ReviewPackage` фиксирует evidence snapshot checksum и не переписывает прежний risk tier незаметно; новое evidence создает новый или stale package state.

## Отзыв намерения — 2026-11-09

[[Wiki/policies/review_package_withdrawal_policy]] добавляет самостоятельное действие назначенного Editor/координатора, не пятое решение Reviewer. Принятый до допуска исполнения отзыв терминален для точного packageId; исторические snapshot/approval сохраняются, но не разрешают post. Повторная подача создаёт новый пакет и новое решение даже при совпавшем checksum; повторное evidence требует проверки применимости.

Принятие отзыва упорядочивается с допуском конкретной post-попытки. При допущенной попытке запрос удерживает новые попытки до доказанного исхода: успех ведёт к коррекции, окончание без эффекта — к отзыву. Нет двух одновременно неразобранных попыток. can_post/read не резервирует право, факт допуска не становится durable post_authorized. Это инвариант будущей модели, не новая реализованная схема Save.

Исправительный пакет связывается с опубликованным исходным по [[Wiki/policies/published_result_correction_policy]], но не наследует approval.
