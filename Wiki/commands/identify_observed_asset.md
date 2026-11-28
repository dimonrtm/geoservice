---
title: "Привязать наблюдение к опознанному активу"
type: command
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/2026-11-27-field-information-answers.md"
tags: [domain-knowledge, utility-gis, field-evidence]
confidence: inferred
related: [DDD_Wiki/aggregates/field_observation, Wiki/specifications/observation_identifies_asset, Wiki/domain_events/observed_asset_identified, DDD_Wiki/use_cases/field_office_sync]
---

# Привязать наблюдение к опознанному активу

## Actor

ГИС-редактор, разбирающий полевой результат.

## Target

[[DDD_Wiki/aggregates/field_observation|Полевое наблюдение]] по наряду. Редактор устанавливает привязку одного наблюдения независимо от результатов по другим наблюдениям того же пакета.

## Preconditions

Наблюдение можно найти по его обозначению. Есть ориентир, схема или результат повторного выезда, который различает активы-кандидаты.

## Outcome

Редактор фиксирует актив и основание привязки. При двух равноправных кандидатах наблюдение остаётся доступным для уточнения, обе карточки сохраняют прежние координаты. После опознания редактор отдельно решает, какую геометрию принять.

Основание — решения условной организации в исследовании полевых сведений. [NET-07](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-07) · [NET-01](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-01) · [Исходный процесс](../../RAW_inputs/documents/UtilityGisEditor.md#базовые-и-продвинутые-workflows).
