---
title: Контракт Реализации Review/Post
type: session
status: active
created: 2026-06-24
updated: 2026-06-24
source: RAW_inputs/meetings/implementation_contract_for_review_and_post.md
tags: [meeting, review-post, implementation-contract, utility-network]
---

# Контракт Реализации Review/Post

## Контекст

Источник отвечает на discovery-вопросы по review/post implementation contract
для `Utility GIS editor`: ownership `PostToDefault`, ближайший вертикальный
срез, `ReviewPackage`, state machine, evidence, risk tiers, stale policy,
integrations и audit boundary.

Источник является design/architecture input, а не real `Editor`/`Reviewer`
interview.

## Ключевые Решения

- `Publisher` является отдельной технической ролью / version administrator для
  `PostToDefault`; `Reviewer` выполняет semantic `approve package`.
- В ближайшем вертикальном срезе фактический post может выполнить
  demo-system action после reviewer approval, чтобы не расширять scope
  отдельным human `Publisher` desk.
- `Data Owner` задает policy, risk matrix и делегирование полномочий, но не
  выполняет routine post.
- Для `Normal` обязательного второго контроля нет; для `High` основное решение
  принимает `Reviewer`; для `Critical` требуется подтверждение профильного
  специалиста.
- Ближайший must-scope: `ReviewPackage` aggregate, минимальный evidence package,
  `Normal`/`High`/`Critical`, hard blockers с absolute veto, ограниченная
  `StaleApprovalPolicy` и audit с `approve package` / `can post`.
- Ближайший vertical slice должен доходить до review/post end-to-end:
  `work order -> named edit version -> validation -> reconcile -> package build
  -> reviewer decision -> stale/blocker recheck -> simulated post -> audit
  outcome`.
- `ReviewPackage` нужно заводить сейчас как отдельный aggregate, иначе stale
  invalidation, repeat review и audit расползутся по ad hoc полям
  `EditVersion`.

## Уточнения Модели

- Минимальная state machine после `InProgress`: `editing -> validated ->
  reconciled -> ready_for_review -> approved_package -> post_authorized ->
  posted`.
- Поперечные состояния: `blocked`, `stale`, `escalated`.
- `EditVersion` готова к review только после последнего reconcile с текущим
  `Default`, отсутствия unresolved conflicts, validation без absolute veto,
  минимального evidence package, editor summary/comment и фиксированного
  built-from state.
- Mandatory stale events: новый reconcile, изменение `Default` в package scope,
  изменение geometry, association delta, network attribute, terminal
  configuration, validation result, trace/subnetwork freshness или required
  evidence.
- Domain audit хранит package/work order/edit version ids, actor, role,
  decision, rationale, risk tier, blocker flags, stale events, evidence snapshot
  checksum, trace/subnetwork freshness verdict и final post outcome.
- Correlation ID, timings, retry counters и technical error details относятся к
  telemetry/debug, а не к domain audit.

## Разрешенные Конфликты

- [[../../Wiki/conflicts/2026-06-24-reviewer-vs-publisher]]: `Publisher`
  отделен от `Reviewer`; ближайший срез использует demo-system action для
  technical post.
- [[../../Wiki/conflicts/2026-06-24-release1-vs-release2-review-policy]]:
  ближайший срез включает `ReviewPackage`, evidence, risk tier, blockers,
  stale policy и audit; rich routing, full topology engine, batch review/SLA и
  production-safe claims остаются вне scope.

## Последующие Шаги

- [ ] Подготовить implementation contract v0.1 для review/post developer demo.
- [ ] Проверить human-layer гипотезы с реальными `Editor`/`Reviewer`: trust
      wording, evidence sufficiency, `Critical` specialist confirmation,
      repeat-review UX и границы `Publisher`.

## Связи

- [[../decisions/release_2_conflict_explanation]]
- [[../decisions/followups/index]]
- [[../../Wiki/actors/reviewer]]
- [[../../Wiki/actors/publisher]]
- [[../../DDD_Wiki/aggregates/review_package]]
- [[../../DDD_Wiki/bounded_contexts/review_post]]
