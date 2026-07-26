---
title: Edit Geometry Precision Policy
type: policy
status: planned
created: 2026-07-26
updated: 2026-07-26
source: RAW_inputs/meetings/tolerance_rules.md
tags: [domain-knowledge, policy, edit-version, geometry, precision]
confidence: high
related: [Wiki/glossary/positional_accuracy_for_acceptance, Wiki/glossary/coordinate_storage_precision, Wiki/commands/update_edit_version_feature_geometry, Wiki/specifications/edit_version_basic_draft_validation, DDD_Wiki/invariants/edit_version_persisted_edit_invariants]
---

# Edit Geometry Precision Policy

## Rule

Перед сравнением и сохранением перемещённая вершина детерминированно приводится к [[Wiki/glossary/coordinate_storage_precision]]. Обычное сохранение не перенормализует нетронутые вершины и не выполняет скрытый snapping к объектам сети.

После канонизации проверяются инварианты геометрии. Если результат совпал с текущим сохранённым состоянием, действие является no-op. Если результат стал невалидным, непростым, схлопнутым или нарушил другие hard guards, сохранение отклоняется атомарно.

Полная перенормализация линии и совместное перемещение общих топологических узлов являются отдельными явными операциями и не входят в first-save slice.

## Decision Outcome

- `changed`: каноническая координата отличается, а все hard guards соблюдены;
- `no-op`: канонический результат совпадает с текущим сохранённым состоянием;
- `rejected`: канонизация привела к недопустимой геометрии или нарушению инварианта.
