---
title: Подготовить и проверить осознанную правку линии
type: use-case
status: active
created: 2026-10-18
updated: 2026-10-18
source: RAW_inputs/research_results/2026-10-18-utility-gis-editor-use-case-answers.md
tags: [domain-knowledge, research, simulated-organization]
confidence: high
related: [DDD_Wiki/use_cases/utility_editor_workflow, Wiki/policies/intentional_line_editing_policy]
---

# Подготовить и проверить осознанную правку линии

## Цель и участник

Редактор уточняет допустимую часть существующей линии по заданию и получает объяснимое доказательство результата. Это детализация [[DDD_Wiki/use_cases/utility_editor_workflow]], а не новый bounded context.

## Основной поток

1. Проверить задание, версию и пригодность набора; установить объект среди кандидатов.
2. Подготовить одну разрешённую локальную правку. Не считать доступность инструмента идентичностью, сетку точностью, промежуточное положение намерением.
3. Осмотреть результат и ограничения. Отбросить локальную попытку либо явно сохранить.
4. Получить исход действия и отдельно прочитать current. Показать отличие от baseline, включая no-op.
5. Оценить сохранённую линию и основание; передать ограничения либо начать разбор. Проверить объявленную учебную ветку по [[Wiki/specifications/line_edit_exercise_completed]].

## Альтернативы

Неоднозначный объект — уточнение идентичности; неподдерживаемая операция — отдельный сценарий; запрещённое конечное движение — явная локальная попытка; неизвестный исход — [[DDD_Wiki/use_cases/interrupted_edit_work_recovery]]; сомнительный источник — [[Wiki/policies/geometry_quality_escalation_policy]]. Отмена наряда после Save не означает автоматический Revert.

## Граница согласованности

Существующие EditVersion/WorkOrder и [[DDD_Wiki/invariants/edit_version_persisted_edit_invariants]] сохраняются. Нет транзакции, охватывающей мышиный жест, полевую съёмку и публикацию. Receipt/current/baseline относятся к разным доказательствам; новое UI-действие не порождает автоматически domain event.

## Состояние реализации

Часть выбора и локального движения представлена в коде, но весь критерий и runtime не проверены. Текущее ограничение экрана ровно тремя вершинами не является общей доменной валидностью линии. Сверка очереди/metadata/fixture — FU-2026-10-11-001; полнота Save/Revert и намерения — FU-2026-10-13-004. Stale model health сохраняется. Правила: [[Wiki/policies/intentional_line_editing_policy]]. Доменный контекст: [[Wiki/concepts/field_observation_acceptance]], [[Wiki/concepts/network_representation_and_operational_state]].
