---
title: "Наряд и позиции работ"
type: entity
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/UtilityGisEditor.md"
tags: [domain-knowledge, utility-gis]
confidence: inferred
related: [Wiki/entities/network_feature, Wiki/entities/field_observation, DDD_Wiki/aggregates/network_work_order, DDD_Wiki/use_cases/outage_workflow]
---

# Наряд и позиции работ

Наряд задаёт работу с сетью. Офисный процесс также может начинаться с заявки на изменение. В аварийном процессе диспетчер формирует задание по результату трассировки. Бригада получает относящиеся к работе активы и возвращает сведения об исполнении.

В концептуальной диаграмме документа наряд содержит позиции, каждая позиция относится к активу. После восстановления услуги сеть и статусы работ актуализируют согласованно. Названия статусов и полный жизненный цикл наряда источник оставляет открытыми.

[UtilityGisEditor.md · Базовые и продвинутые workflows](../../RAW_inputs/documents/UtilityGisEditor.md#базовые-и-продвинутые-workflows)

В задании по отключению диспетчер различает расчётный охват и фактически восстановленную часть. Полученное подтверждение закрывает только охваченный им объём. При наличии остатка наряд остаётся открытым. [[Wiki/commands/record_service_restoration|Учесть восстановление по части задания]]. [NET-03](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-03) · [NET-12](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-12).

В исходной диаграмме каждый экземпляр `WORK_ORDER_ITEM` относится к одному наряду (`WORK_ORDER`) и одному активу. Один актив может участвовать в нескольких позициях. Даже если позиция указывает задвижку, принадлежность [[Wiki/entities/field_observation|конкретного замера]] требуется установить отдельно. Общий статус задания и учтённый объём его позиций согласуются внутри [[DDD_Wiki/aggregates/network_work_order|агрегата наряда]]. [Связи в диаграмме](../../RAW_inputs/documents/UtilityGisEditor.md#бизнес-модели-и-метрики-успеха) · [NET-07](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-07).
