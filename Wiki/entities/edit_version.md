---
title: "Рабочая версия сети"
type: entity
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/UtilityGisEditor.md"
tags: [domain-knowledge, utility-gis]
confidence: inferred
related: [Wiki/entities/network_project, Wiki/entities/edit_event, Wiki/concepts/design_revision, Wiki/policies/publication, DDD_Wiki/aggregates/network_edit_version, DDD_Wiki/use_cases/utility_editor_workflow]
---

# Рабочая версия сети

В рабочей версии редактор готовит изменения геометрии, атрибутов и связей. Перед публикацией он сопоставляет изменения с актуальной сетью, а при ошибке исправляет результат и проводит повторную проверку. После утверждения изменения переходят в официальный слой.

В диаграмме данных каждая версия (`VERSION`) входит в [[Wiki/entities/network_project|проект ГИС]] и содержит [[Wiki/entities/edit_event|записи действий пользователей]]. Подготовленный объём правок проходит проверку и утверждение. Границу согласованности правок и результата проверки задаёт [[DDD_Wiki/aggregates/network_edit_version|агрегат рабочей версии сети]]. Вопрос о совмещении полномочий утверждения и публикации остаётся открытым.

В строительном процессе редактор может учитывать фактическую съёмку в рабочей версии, даже если применимость выданного подрядчику чертежа ещё спорна. [[Wiki/concepts/design_revision|Редакция проекта строительства]] определяет основание для вывода о соответствии построенного участка. [Решение GeoService по NET-11](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-11).

[UtilityGisEditor.md · Базовые и продвинутые workflows](../../RAW_inputs/documents/UtilityGisEditor.md#базовые-и-продвинутые-workflows)
