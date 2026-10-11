---
title: Positional Accuracy Acceptance Policy
type: policy
status: planned
created: 2026-07-31
updated: 2026-10-12
source: "RAW_inputs/meetings/demo_utility_gis.md; RAW_inputs/research_results/2026-10-11-utility-gis-editor-save-recovery-research.md"
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

### Уточнение Исследования 2026-10-11

Правила исследования приняты пользователем 2026-10-12 по [отдельному решению](../../docs/sprint_2/2026-10-12-save-recovery-rules-decision.md). Предложение о распределении ответственности ниже принято как правило; конкретные specification, допуск и сотрудники всё ещё не определены. Это принятие не означает подтверждения точности demo dataset.

Ответ 14 нового research предлагает передать утверждение применимости specification владельцу данных и ответственному за геодезическое качество. В документе должны быть версия, scope, класс объектов, измеряемая характеристика, допуск/единицы, CRS, метод проверки и независимое evidence. Это предложение с confidence medium, а не назначение реальных сотрудников. ASPRS — возможная методическая основа при её принятии организацией, не автоматический числовой допуск GeoService. Конкретные документ и tolerance по-прежнему не установлены.

Ответы 5 и 13 предлагают независимо показывать сохранённость правки и качество: Revert/no-op не подтверждают точность исходной линии. См. [[Wiki/glossary/editing_result_states]]. Исходное правило ниже остаётся в силе.

Отсутствие позиционного evidence не превращает first save в invalid geometry и не должно подменяться `XY resolution` или `XY tolerance`. Оно является downstream acceptance blocker, а не техническим hard guard сохранения.
