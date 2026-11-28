---
title: "Учесть восстановление услуги по части задания"
type: command
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/2026-11-27-field-information-answers.md"
tags: [domain-knowledge, utility-gis, field-evidence]
confidence: inferred
related: [DDD_Wiki/aggregates/network_work_order, Wiki/specifications/service_return_evidenced, Wiki/domain_events/service_restoration_confirmed]
---

# Учесть восстановление услуги по части задания

## Actor

Диспетчер сопоставляет сообщение бригады или независимую проверку с выданным заданием.

## Target

Восстановление услуги по указанным точкам или участкам в охвате конкретного задания.

## Preconditions

Известны место, время, наблюдаемый признак возврата услуги и часть задания, на которую распространяется подтверждение. Расчётный охват сам по себе этих сведений не даёт.

## Outcome

Подтверждённая часть учитывается при обновлении сети и статуса работ. Оставшаяся часть остаётся открытой. При сообщении лишь о завершении ремонта диспетчер ожидает подтверждения услуги.

Основание — решения условной организации в исследовании полевых сведений. [NET-03](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-03) · [NET-12](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-12) · [Исходный процесс](../../RAW_inputs/documents/UtilityGisEditor.md#базовые-и-продвинутые-workflows).
