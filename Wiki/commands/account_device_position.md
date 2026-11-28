---
title: "Учесть подтверждённое положение устройства"
type: command
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/2026-11-27-field-information-answers.md"
tags: [domain-knowledge, utility-gis, field-evidence]
confidence: inferred
related: [DDD_Wiki/aggregates/device_position_history, Wiki/value_objects/device_position_reading, Wiki/domain_events/device_position_confirmed, Wiki/system_events/device_report_received]
---

# Учесть подтверждённое положение устройства

## Actor

Диспетчер, получивший полевое подтверждение для оперативного расчёта.

## Target

Положение конкретного устройства на момент действия сообщения.

## Preconditions

Установлены устройство, положение, время действия и источник подтверждения. При нескольких сообщениях учитывается их применимость на момент расчёта.

## Outcome

Подтверждение доступно в истории. Более раннее положение, полученное позже, не вытесняет последующее. При неразрешимом противоречии диспетчер отмечает положение неизвестным и явно учитывает это в расчёте охвата. Постоянную схему соединений редактируют отдельной операцией.

Основание — решения условной организации в исследовании полевых сведений. [NET-12](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-12) · [NET-13](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-13) · [Исходный процесс](../../RAW_inputs/documents/UtilityGisEditor.md#базовые-и-продвинутые-workflows).
