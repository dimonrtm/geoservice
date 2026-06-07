---
title: Ф7 Метрики, Риски И Проверка
type: session
status: active
created: 2026-06-07
updated: 2026-06-07
source: "user answers to /discover --phase Ф7, 2026-06-07; RAW_inputs/documents/utility_gis_editor_metrics.md; RAW_inputs/documents/utility_gis_editor_post_problems.md; RAW_inputs/documents/utility_gis_editor_manual_baseline_algorithm.md; RAW_inputs/documents/utility_gis_editor_risky_assumptions.md; RAW_inputs/documents/utility_gis_editor_minimal_experiments.md"
tags: [discovery, phase-f7, metrics, risks, utility-gis-editor]
---

# Ф7 Метрики, Риски И Проверка

## Цель

Ф7 объединяет три результата: качество demo, `learning value` и проверку пригодности AI-first разработки для сложного GIS workflow.

## Главная Метрика

North Star metric - `Safe Authoritative Post Rate`:

```text
work orders, безопасно опубликованные в Default без post-проблем
/
все work orders, начатые в GeoService
* 100%
```

В знаменатель входят отмененные и незавершенные work orders. Цель - `>=95%` на выборке 200 work orders, то есть минимум 190 safe posts.

Safe post требует успешных validation/reconcile, resolved conflicts, соблюдения approval rules и отсутствия проблемы в течение 7 календарных дней после post. Aggregate rate не компенсирует safety blocker: silent overwrite, пропущенный safety-critical conflict или Critical/High review error означает провал проверки независимо от процента.

## Подтверждение Post

- GeoService выполняет автоматические validation/reconcile/conflict checks.
- Низкорисковое изменение может подтвердить `Editor`, если проверки успешны.
- Изменения topology, trace, associations или критичных объектов требуют подтверждения `Reviewer`, `Data steward` или `Version administrator` до post.

## Baseline И Измерения

- Сравнение выполняется с ручным разбором полного пути до safe post.
- Ручной baseline снимается на 10-20 work orders разной сложности.
- Основная продуктовая проверка использует 200 work orders.
- Performance benchmark выполняется 30 повторов.
- Evidence: benchmark reports в `docs/benchmarks/utility-gis-editor/`, structured audit facts в PostgreSQL audit tables; тяжелые evidence связываются через `work_order_id`, `edit_version_id`, `validation_run_id`, `reconcile_run_id`, `conflict_id`, `review_id`, `post_id`.

## UX Сигнал Смены Курса

Курс нужно менять, если `Utility GIS editor` не может уверенно пройти путь от work order до safe post: путает Save и Post, не различает edit version и `Default`, не понимает validation/reconcile/conflict blocking или не может объяснить, когда данные стали authoritative.

## Принятый Реестр Рисков

Demo blockers: пропущенный конфликт, silent overwrite, unsafe/stale post, потеря edits, Critical/High review error, нарушение approval rule, неполный audit trail, post-проблема в 7-дневном окне и непонимание ключевых workflow states.

Экспериментальные риски: зависимые повторы synthetic work orders, недостаточно реалистичный dataset, неодинаковая severity-классификация reviewers, неопределенный manual baseline, слишком простые work orders и преждевременное расширение local demo до immutable object storage.

## Связи

- [[../concepts/metrics]]
- [[../decisions/risk_assumption_log]]
- [[../decisions/followups/index]]
- [[../solution/nfr]]
- [[../solution/roadmap]]
- [[2026-06-06-utility-gis-editor-target-times]]
