---
title: "Положение устройства подтверждено"
type: domain-event
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/2026-11-27-field-information-answers.md"
tags: [domain-knowledge, utility-gis, field-evidence]
confidence: inferred
related: [DDD_Wiki/aggregates/device_position_history, Wiki/system_events/device_report_received, DDD_Wiki/use_cases/outage_workflow]
---

# Положение устройства подтверждено

## Source Aggregate

[[DDD_Wiki/aggregates/device_position_history|История положений устройства]] хранит подтверждения для одного устройства. Из неё диспетчер определяет применимое положение на момент расчёта.

## Happened In The Past

Для опознанного устройства известно фактическое положение на время действия и источник подтверждения. Одно свидетельство о положении не устанавливает изменение постоянного физического соединения.

## Downstream Reactions

Диспетчер использует последнее применимое подтверждение при трассировке на заданный момент. Более раннее подтверждение дополняет историю. Противоречащие сообщения без установленной последовательности делают текущее положение неизвестным.

Основание — решения условной организации в исследовании полевых сведений. [NET-13](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-13) · [NET-12](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-12) · [Исходный процесс](../../RAW_inputs/documents/UtilityGisEditor.md#базовые-и-продвинутые-workflows).
