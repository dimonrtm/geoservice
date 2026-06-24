---
title: Метрики Utility GIS Editor
type: concept
status: active
created: 2026-06-07
updated: 2026-06-23
source: "user answers to /discover --phase Ф7, 2026-06-07; RAW_inputs/documents/utility_gis_editor_metrics.md; RAW_inputs/documents/utility_gis_editor_post_problems.md; RAW_inputs/documents/utility_gis_editor_manual_baseline_algorithm.md; RAW_inputs/meetings/geometry_association_conflict_f7.md; RAW_inputs/meetings/geometry_association_conflict_f8.md"
tags: [metrics, phase-f7, utility-gis-editor, authoritative-editing]
---

# Метрики Utility GIS Editor

## North Star Metric

`Safe Authoritative Post Rate` - доля всех начатых work orders, безопасно доведенных от edit до post в `Default`.

```text
Safe Authoritative Post Rate =
safe work orders posted to Default
/
all work orders started in GeoService
* 100%
```

Отмененные и незавершенные work orders входят в знаменатель. Целевой уровень - `>=95%` на 200 work orders: минимум 190 safe posts.

## Условия Safe Post

- Edits сохранены в edit version.
- Validation успешна, critical issues отсутствуют.
- Reconcile выполнен, все conflicts разрешены.
- Approval соответствует риску изменения.
- Post выполнен в актуальный `Default`.
- В течение 7 календарных дней не возникла post-проблема.

Проблемой после post считается нарушение корректности, полноты, connectivity, topology, trace или доверенности authoritative state, потребовавшее rollback, ручную правку, повторную сверку, повторный work order либо вмешательство reviewer/admin/downstream consumer.

Категории: `POST_DATA_LOSS`, `POST_TOPOLOGY_ERROR`, `POST_TRACE_ERROR`, `POST_CONFLICT_MISRESOLVED`, `POST_MANUAL_CORRECTION`, `POST_WORK_ORDER_MISMATCH`, `POST_DOWNSTREAM_ERROR`.

## Secondary Metrics

| Метрика | Назначение |
|---|---|
| `Time to Safe Post` | Время от открытия work order до safe post; для synthetic MVP ориентир P95 от first edit до post `<=5 минут`. |
| `Validation Pass Rate` | Доля запущенных validations без critical topology/network errors. |
| `Conflict Resolution Rate` | Доля detected conflicts, которые явно и успешно разрешены. |
| `Post Failure Rate` / `Reconcile Retry Rate` | Частота защитных отказов post и повторных reconcile. |
| `Rework / Manual Correction Rate` | Доля posted work orders с post-проблемой в 7-дневном окне; ориентир `<=2-5%`. |

## Safety И Quality Guardrails

- `Conflict Escape Rate`: `0%` для подготовленных safety-critical conflicts.
- `Review Error Count`: 0 Critical, 0 High, не более 1 Medium и 3 Minor на work order.
- `Return Rate`: ранний общий уровень `<=10-15%`; geometry/associations `<=10%`; topology/trace `<=5-10%`; зрелая цель `<=5%`.
- Silent overwrite, пропущенный critical conflict и любой Critical/High review error являются blockers независимо от North Star aggregate.

## Performance Guardrails

Обязательные P95:

- single edit save `<=2 сек`;
- small AOI validation `<=15 сек`;
- reconcile без conflicts `<=10 сек`;
- показ conflicts `<=20 сек`;
- открытие conflict diff `<=5 сек`;
- post to `Default` `<=15 сек`;
- отказ stale post `<=5 сек`.

Временно допустимо нарушить targets initial map load, jump to AOI, batch save 5-20 edits, large AOI validation, reconcile с большим числом conflicts и full map refresh after post.

Benchmark выполняется 30 повторов на reference hardware.

## Release 2 Consequence Package Metrics

Для Release 2 `geometry/association conflict` North Star отличается от
Release 1 `Safe Authoritative Post Rate`: package должен помочь
квалифицированному человеку быстро принять reviewable go/no-go решение по
сетевому конфликту и сохранить основание решения, не скрывая hard blockers и
не обещая production-safe `post` без свежей проверки.

Главная developer-demo метрика - `contract readiness pass rate`: доля прогонов
canonical scenario и stale/blocker/pre-post sidecar variants, где система
корректно строит package, показывает blockers, помечает stale state и формирует
audit object, пригодный для repeat review.

Абсолютное условие: `false-safe verdict count = 0` на канонических hard-block
сценариях. Один false-safe на dirty trace path, invalid subnetwork, unresolved
association delta, stale approval/package или missing required evidence
проваливает demo независимо от aggregate metrics.

Secondary demo metrics:

| Метрика | Назначение |
|---|---|
| `Package Build Success` | Package содержит `Base / Mine / Default`, version context, dirty areas, blockers и audit skeleton без деградации. |
| `Evidence Completeness` | Для сценария собраны geometry diff, association delta, dirty/validation state, subnetwork status и human decision trail. |
| `Blocker Detection` | Hard blockers найдены воспроизводимо и переводят package в `blocked post` или `stale`. |
| `Stale Detection` | Previous package/approval инвалидируется после network-relevant changes, нового `Default` after reconcile, новых conflicts или измененного validation outcome. |
| `Audit Completeness` | Audit сохраняет verdict, evidence basis, blocker/stale reasons, actor, timestamp, next step и pre-post outcome. |
| `Time-to-decision` / `External-check opens` | Внутренние demo indicators для сравнения с scripted baseline; не являются product claim до реальных `Editor`/`Reviewer`. |

Counter-metrics:

- `False-safe verdict count`;
- `False-block rate`;
- `Duplicate-view rate`;
- `Time added by package`;
- `Unclear next step rate`.

Минимальный experiment: один scripted golden walkthrough на canonical transformer
terminal case, минимум 10 детерминированных повторов canonical scenario,
минимум 10 мутированных прогонов stale / blocker / pre-post failure variants и
до 30 automated runs, если нужно измерить стабильность package build и blocker
detection.

Для каждого run сохраняются `seed/checksum`, `scenario_id`, `package_id`,
`version_id`, version timestamps/properties, risk tier, blockers, dirty-area
status, subnetwork status, trace/subnetwork freshness, decision, chosen next
step, audit object, time-to-decision и manual/external checks.

Manual baseline для Release 2 снимается отдельно от Release 1: сравнение идет
против `ArcGIS native Conflicts view + reconcile/post + локальный SOP +
экспертный handoff` на том же transformer terminal scenario.

Ф8 добавляет four gates перед реализацией:

- `contract gate`: frozen state machine, package schema, blocker semantics и
  stale triggers;
- `safety gate`: canonical scenario и stale/pre-post sidecar воспроизводимо
  показывают hard blockers; false-safe является абсолютным veto;
- `observability gate`: каждый run сохраняет package id, input checksum,
  blockers, freshness snapshots, decision и audit object;
- `validation gate`: claims сильнее `helps explain/detect/block` запрещены до
  real `Editor`/`Reviewer` sessions.

В audit object из run schema переносятся только доказательные поля:
`package_id`, `scenario_id`, `seed/checksum`, source snapshot ids, `risk_tier`,
`blockers[]`, `trace_consistency`, `subnetwork_status`,
`evidence_completeness`, `actor_role`, `decision`, timestamps,
`stale_events[]`, `manual_checks_count` и `final_post_outcome`. Performance
counters, stack traces и debug fields остаются в observability/log stream.

## Manual Baseline

Ручной baseline измеряется на 10-20 work orders категорий low/medium/high. Фиксируются active work, waiting time и external delay раздельно.

Минимальные показатели: Manual Time to Safe Post, Manual Review Time, Manual Reconcile Time, Manual Return Rate, Manual Rework Rate, Manual Review Error Count и Manual Touch Count.

## Evidence

- Benchmark reports: `docs/benchmarks/utility-gis-editor/`.
- При необходимости reports дублируются как CI artifacts.
- Structured audit facts: PostgreSQL audit tables.
- Тяжелые evidence должны быть immutable и связаны с идентификаторами полного workflow; включение object storage в первый local demo требует отдельного scope-решения.

## Связи

- [[../chats/2026-06-07-phase-f7-metrics-and-risks]]
- [[../chats/2026-06-23-geometry-association-conflict-f7]]
- [[../chats/2026-06-23-geometry-association-conflict-f8]]
- [[../decisions/risk_assumption_log]]
- [[../decisions/followups/index]]
- [[../solution/nfr]]
- [[../solution/roadmap]]
