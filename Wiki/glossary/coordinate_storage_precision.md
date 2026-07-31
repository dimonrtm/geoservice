---
title: Точность Хранения Координат
type: glossary
status: active
created: 2026-07-26
updated: 2026-07-31
source: "RAW_inputs/meetings/tolerance_rules.md; RAW_inputs/meetings/demo_utility_gis.md"
tags: [domain-knowledge, glossary, geometry, precision]
confidence: high
related: [Wiki/glossary/positional_accuracy_for_acceptance, Wiki/policies/edit_geometry_precision_policy, DDD_Wiki/invariants/edit_version_persisted_edit_invariants]
---

# Точность Хранения Координат

`Точность хранения координат` — канонический шаг координатной сетки и правило числового равенства координат в конкретном слое или хранилище.

Она определяет, как введённая координата преобразуется перед сравнением и сохранением. Это отдельное понятие от [[Wiki/glossary/positional_accuracy_for_acceptance]]: требование к качеству данных задаёт спецификация работы, а точность хранения — пространственная модель слоя или БД.

Фактическое значение берётся из metadata пространственной привязки сохраняющего dataset: `WKID`/`WKT`, coordinate unit, `xyResolution`, `xyTolerance`, origin/domain и применяемые transformations. Для Z/M используются отдельные настройки, если они входят в модель. Значения карты, display precision и класс актива не являются источником storage grid.

У всех classes одного Utility Network feature dataset общая XY spatial reference и resolution; разные datasets могут иметь разные параметры. Конкретные metadata demo dataset пока не зафиксированы.
