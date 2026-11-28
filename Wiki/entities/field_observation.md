---
title: "Полевое наблюдение"
type: entity
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/2026-11-27-field-information-answers.md"
tags: [domain-knowledge, utility-gis, field-evidence]
confidence: inferred
related: [Wiki/entities/network_feature, Wiki/entities/inspection, DDD_Wiki/aggregates/field_observation, DDD_Wiki/use_cases/field_office_sync]
---

# Полевое наблюдение

Бригада обозначает конкретный замер по наряду. По этому обозначению офис может вернуться к тому же наблюдению после выезда, даже если на местности были две похожие задвижки. К наблюдению относятся место и время, измеренная величина или замеченный признак, ориентиры и доступные материалы. Важен фактически обследованный объём.

При неопределённости офис сохраняет возможные привязки. После опознания редактор указывает установленный актив и основание выбора. Принятие наблюдения ещё оставляет открытым вопрос о правке геометрии или эксплуатационного состояния. Для старого осмотра трубы сохраняются изначальный объект и охват даже после деления ребра.

По решению условной организации привязка принимается отдельно для каждого замера. Если для одного замера найден однозначный ориентир, редактор может указать актив и основание выбора, пока соседний замер из того же пакета ещё ожидает опознания. За согласованность этого решения отвечает [[DDD_Wiki/aggregates/field_observation|агрегат полевого наблюдения]]. Подтверждённый результат [[Wiki/entities/inspection|осмотра актива]] сохраняет дату и фактически обследованную часть.

Основание — решения условной организации в исследовании полевых сведений. [NET-07](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-07) · [NET-01](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-01) · [NET-05](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-05) · [NET-08](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-08) · [Исходный процесс](../../RAW_inputs/documents/UtilityGisEditor.md#базовые-и-продвинутые-workflows).
