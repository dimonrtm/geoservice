---
title: Edit Geometry Precision Policy
type: policy
status: planned
created: 2026-07-26
updated: 2026-07-31
source: "RAW_inputs/meetings/tolerance_rules.md; RAW_inputs/meetings/demo_utility_gis.md"
tags: [domain-knowledge, policy, edit-version, geometry, precision]
confidence: high
related: [Wiki/glossary/positional_accuracy_for_acceptance, Wiki/glossary/coordinate_storage_precision, Wiki/policies/positional_accuracy_acceptance_policy, Wiki/commands/update_edit_version_feature_geometry, Wiki/specifications/edit_version_basic_draft_validation, DDD_Wiki/invariants/edit_version_persisted_edit_invariants]
---

# Edit Geometry Precision Policy

## Rule

Перед сравнением и сохранением перемещённая вершина детерминированно приводится к [[Wiki/glossary/coordinate_storage_precision]]. Обычное сохранение не перенормализует нетронутые вершины и не выполняет скрытый snapping к объектам сети.

Storage grid загружается из metadata фактического сохраняющего dataset, а не из настроек map display или допуска позиционной приёмки. Planned contract выполняет server-side canonicalization и использует детерминированное округление midpoint `ROUND_HALF_AWAY_FROM_ZERO`; вычисление должно использовать Decimal или целочисленный scale, чтобы binary floating point не менял результат. Client отображает geometry, возвращённую сервером после сохранения.

После канонизации проверяются инварианты геометрии. Если результат совпал с текущим сохранённым состоянием, действие является no-op. Если результат стал невалидным, непростым, схлопнутым или нарушил другие hard guards, сохранение отклоняется атомарно.

Полная перенормализация линии и совместное перемещение общих топологических узлов являются отдельными явными операциями и не входят в first-save slice.

## Decision Outcome

- `changed`: каноническая координата отличается, а все hard guards соблюдены;
- `no-op`: канонический результат совпадает с текущим сохранённым состоянием;
- `rejected`: канонизация привела к недопустимой геометрии или нарушению инварианта.

Конкретные `xyResolution`, `xyTolerance`, CRS и coordinate unit demo dataset остаются открытыми metadata-вопросами. Числовые значения из source не являются утверждённой конфигурацией проекта.
