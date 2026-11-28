---
title: "Выбрать геометрию при расхождении координат"
type: command
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/2026-11-27-field-information-answers.md"
tags: [domain-knowledge, utility-gis, field-evidence]
confidence: inferred
related: [DDD_Wiki/aggregates/network_edit_version, Wiki/entities/field_observation, Wiki/value_objects/measured_position]
---

# Выбрать геометрию при расхождении координат

## Actor

ГИС-редактор, который ведёт рабочую версию.

## Target

Геометрия опознанного актива, независимо уточнённая офисом и бригадой.

## Preconditions

Редактор проверяет, что совпадают объект, точка измерения и рассматриваемый момент. Координаты приведены к общей системе. Известны основания обоих изменений, метод измерения и обстоятельства последующих работ в объёме, достаточном для выбора.

## Outcome

Редактор сохраняет выбранную геометрию и причину в рабочей версии. Более свежий ввод сам по себе приоритета не даёт. Если измерения несопоставимы или перемещение неотличимо от ошибки, прежняя публикация сохраняется, а точку направляют на уточнение.

Основание — решения условной организации в исследовании полевых сведений. [NET-01](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-01) · [NET-07](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-07) · [Исходный процесс](../../RAW_inputs/documents/UtilityGisEditor.md#базовые-и-продвинутые-workflows).
