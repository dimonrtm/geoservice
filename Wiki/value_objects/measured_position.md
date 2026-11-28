---
title: "Измеренное положение актива"
type: value-object
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/2026-11-27-field-information-answers.md"
tags: [domain-knowledge, utility-gis, field-evidence]
confidence: inferred
related: [Wiki/commands/resolve_asset_coordinates, Wiki/specifications/observation_identifies_asset, Wiki/entities/field_observation]
---

# Измеренное положение актива

## Meaning

Редактор сравнивает координаты для одной точки опознанного актива. Для интерпретации измеренного положения существенны точка на объекте, координаты, система координат и момент, к которому относится измерение. Метод, качество, происхождение и последующие работы позволяют оценить основание выбора.

## Equality

При одинаковых объекте, точке и времени геометрические значения сопоставляют в общей системе координат. Совпадение чисел в разных системах ещё не устанавливает совпадение положения. Совпадающие положения могут иметь разные по качеству основания. Исследование не задаёт универсальный числовой порог эквивалентности.

## Immutability

При повторной съёмке фиксируют новое измерение. Выбор одного значения в рабочей версии сохраняет причину выбора и исходные основания. При неустановленном активе замер сохраняется с наблюдением.

Решения условной организации через `expert_repson`. [NET-01](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-01) · [NET-07](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-07) · [Офисная, полевая и оперативная работа с сетью](../../RAW_inputs/documents/UtilityGisEditor.md#базовые-и-продвинутые-workflows).
