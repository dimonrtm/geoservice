---
title: Идентичность экземпляра набора и записи
type: concept
status: active
created: 2026-11-07
updated: 2026-11-07
source: RAW_inputs/research_results/2026-11-07-utility-gis-editor-dataset-qualification-research.md
tags: [domain-knowledge, dataset-qualification, simulated-organization]
confidence: high
related: [Wiki/specifications/demo_dataset_instance_qualified, Wiki/concepts/change_basis_lifecycle, Wiki/concepts/assessment_statement_lifecycle]
---

# Идентичность экземпляра набора и записи

## Смысл

Различаются логический набор и его редакция, конкретный экземпляр данных в окружении, запись feature и обозначаемый ею актив. Имя слоя, локальный ключ и совпадение геометрии не взаимозаменяемы. Для синтетической fixture обозначение L-003 относится к сценарию; существование реального физического актива не предполагается.

Между экземплярами требуется явное сопоставление записей с происхождением. Один локальный ID может быть однозначным только внутри своего контекста. Копирование не переносит автоматически receipt, историю операций и заключение о качестве на новую запись.

## Применение

При квалификации упражнения фиксируются экземпляр, редакция, WorkOrder/EditVersion, feature и связь с asset designation. Если новый seed и старый volume имеют одинаковое имя набора, их соответствие проверяется отдельно. Геометрический хеш может характеризовать снимок, но не доказывает идентичность актива.

Структура линии проверяется отдельно: топологическое равенство допускает иное число/порядок вершин. Поэтому двухточечная линия не становится eligible fixture от совпадения множества точек с трёхточечной.

Это понятие уточняет [[Wiki/policies/demo_dataset_qualification_policy]] и [[Wiki/specifications/demo_dataset_instance_qualified]]. Новые aggregate, глобальная система идентификаторов или API этим не вводятся.

## Происхождение и уверенность

Внешние основания: S10 (OGC MUDDI — objectID/recordID/systemID), S29 (USGS — PID metadata), S49 (DCAT — dataset/distribution), S41–S42 (структурное и топологическое равенство) в [[RAW_inputs/research_results/2026-11-07-utility-gis-editor-dataset-qualification-research]]. Выбор состава ручной карточки — решение условной организации, ответы 6–8. High означает определённость понятия, не проверку конкретной БД.

Связи: [[Wiki/concepts/change_basis_lifecycle]], [[Wiki/concepts/assessment_statement_lifecycle]].
