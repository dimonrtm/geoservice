---
title: Метрики Utility GIS Editor
type: concept
status: active
created: 2026-06-07
updated: 2026-06-07
source: "user answers to /discover --phase Ф7, 2026-06-07; RAW_inputs/documents/utility_gis_editor_metrics.md; RAW_inputs/documents/utility_gis_editor_post_problems.md; RAW_inputs/documents/utility_gis_editor_manual_baseline_algorithm.md"
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
- [[../decisions/risk_assumption_log]]
- [[../decisions/followups/index]]
- [[../solution/nfr]]
- [[../solution/roadmap]]
