---
title: Integrated Review Package And Simulated Post
type: session
status: active
created: 2026-06-26
updated: 2026-06-26
source: "RAW_inputs/meetings/ic_review_package_and_simulated_post.md; user chat 2026-06-26"
tags: [meeting, review-post, implementation-contract, workflow]
---

# Integrated Review Package And Simulated Post

## Контекст

Источник отвечает на discovery-вопросы по новому review/post implementation contract. Он уточняет, что value доказывается не read-only package сам по себе, а полным маленьким срезом текущего `WorkOrder` / `EditVersion` workflow до simulated post и durable audit.

Дополнительный ответ пользователя в чате 2026-06-26 зафиксировал: новый контракт должен быть отдельным от старого `docs/release_2/geometry_association_conflict/2026-06-23-implementation-contract-v0.1.md`; старый contract считать legacy/reference; планировать дальше маленькими спринтами, а не релизами.

## Ключевые Решения

- Текущий slice должен идти по цепочке `submit_for_review -> reviewer decision -> computed can_post -> simulated post -> durable audit`, а не останавливаться на `ReviewPackage` после reconcile.
- `Publisher` в developer demo - system actor `post-gate` без отдельного human UI; `Reviewer` принимает semantic decision по package, а система отдельно проверяет `can_post` и выполняет simulated post.
- Допустимые решения `Reviewer` в v0.1: `approve package`, `return for changes`, `request evidence`, `escalate`.
- `stale` - системное состояние, а `block post` - вычисляемый результат pre-post check; они не являются ручными решениями `Reviewer`.
- `High` остается в полномочиях `Reviewer`, если evidence complete и absolute veto отсутствуют; `Critical` в developer demo завершается `escalated` как terminal non-goal.
- `can_post` должен быть вычисляемой спецификацией на чтении, а не persisted authoritative state; сохранять нужно pre-post check snapshot, post attempt и outcome в audit.
- Главный negative fixture для demo - `DefaultChangedAfterReconcile`.
- Primary acceptance gate - zero false-safe on absolute veto cases; secondary gates: contract-readiness pass rate, audit completeness и controlled time-to-decision.

## Уточнения Модели

- Минимальная state machine: `draft -> ready_for_review -> under_review -> approved | returned | escalated -> stale | can_post | blocked_post -> simulated_posted`.
- Mandatory stale events: `DefaultChangedAfterReconcile`, новый reconcile, geometry/association/network-attribute/terminal-config mutation, validation/dirty/error status change, trace/subnetwork evidence change и mutation evidence, на котором держалось reviewer decision.
- Absolute veto set для v0.1 должен быть сокращенным, но safety-complete: unresolved association delta, dirty/error state в affected extent или trace path, changed Default after reconcile, changed validation result, invalid subnetwork status для subnetwork-relevant scenario, unexpected trace delta; `Missing evidence` - veto только когда policy требует evidence для risk tier.
- `traceResult` и `subnetworkStatus` являются policy-required when relevant, а не globally required для каждого package.
- Domain audit хранит decision proof: package/work order/edit version ids, actor, decision, rationale, risk tier at decision, blocker snapshot, evidence refs/checksums, freshness snapshot, stale events, pre-post result и simulated post outcome. Timings, correlation id, retries и debug refs относятся к observability.
- Для v0.1 достаточно API/actions: `GET package`, `submit-for-review`, `reviewer decision`, `pre-post-check`, `simulate-post`, `GET audit`; stale invalidation можно держать через internal events и polling, без websocket.

## Разрешенные Конфликты

- [[../../Wiki/conflicts/2026-06-26-legacy-contract-vs-integrated-flow]]: новый implementation contract должен быть отдельным и интегрированным в текущий flow; старый Release 2 artifact остается legacy/reference.

## Follow-up

- [ ] Подготовить новый отдельный contract artifact для integrated review/post slice.
- [ ] Отдельной docs-задачей пометить старый Release 2 contract artifact как legacy/reference, чтобы он не воспринимался source of truth для текущей реализации.
- [ ] Проверить human-layer гипотезы с реальными `Editor`/`Reviewer`: risk wording, evidence sufficiency, trust к blockers, repeat review и границы `Critical`.

## Связи

- [[../../DDD_Wiki/bounded_contexts/review_post]]
- [[../../DDD_Wiki/aggregates/review_package]]
- [[../../DDD_Wiki/use_cases/utility_editor_workflow]]
- [[../../Wiki/specifications/post_allowed]]
- [[../../Wiki/policies/reviewer_post_policy]]
- [[../../Wiki/conflicts/2026-06-26-legacy-contract-vs-integrated-flow]]
