---
title: Positional Accuracy Acceptance Policy
type: policy
status: planned
created: 2026-07-31
updated: 2026-07-31
source: RAW_inputs/meetings/demo_utility_gis.md
tags: [domain-knowledge, policy, edit-version, geometry, accuracy, acceptance]
confidence: high
related: [Wiki/glossary/positional_accuracy_for_acceptance, Wiki/glossary/coordinate_storage_precision, Wiki/policies/edit_geometry_precision_policy, Wiki/specifications/edit_version_basic_draft_validation, Wiki/specifications/edit_version_ready_for_review, Wiki/commands/update_edit_version_feature_geometry]
---

# Positional Accuracy Acceptance Policy

## Rule

Позиционная точность существующего объекта оценивается только по утверждённой спецификации продукта данных или техническим условиям `WorkOrder`. Фактическое положение подтверждается независимым evidence в таком порядке: валидированное полевое или геодезическое измерение, утверждённая исполнительная съёмка, проверенные данные обследования. Для planned object источником может быть утверждённый проект.

`XY resolution`, `XY tolerance`, точность отображения и величина перемещения не заменяют допуск позиционной приёмки. Геометрия текущей GIS и basemap также не являются независимым доказательством точности.

## Inputs

- утверждённая спецификация с именем, версией, областью действия и числовым допуском;
- класс объекта, вид работ и территория, если они различаются в спецификации;
- provenance, метод, дата и качество измерения;
- CRS и единицы измерения evidence и проверяемого dataset.

Для текущего demo dataset эти конкретные значения и утверждённый документ пока не найдены. Числовой пример из source является предложенным test scenario, а не фактом проекта.

## Decision Outcome

- `POSITIONAL_ACCURACY_VERIFIED`: evidence соответствует утверждённой спецификации;
- `POSITIONAL_ACCURACY_UNVERIFIED`: спецификация или достаточное evidence отсутствуют; technical first save разрешён при соблюдении hard guards, но переход к review/completion/post запрещён;
- `POSITIONAL_ACCURACY_EXCEEDED`: измеренная ошибка превышает утверждённый допуск; принятие и публикация запрещены, working draft может сохраняться для исправления.

## Exceptions

Отсутствие позиционного evidence не превращает first save в invalid geometry и не должно подменяться `XY resolution` или `XY tolerance`. Оно является downstream acceptance blocker, а не техническим hard guard сохранения.
