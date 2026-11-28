---
title: "Получено сообщение о положении устройства"
type: system-event
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/2026-11-27-field-information-answers.md"
tags: [domain-knowledge, utility-gis, field-evidence]
confidence: inferred
related: [Wiki/domain_events/device_position_confirmed, DDD_Wiki/use_cases/outage_workflow]
---

# Получено сообщение о положении устройства

При получении полевого сообщения диспетчеру становятся доступны идентификатор устройства, сообщённое положение, время его действия и источник. Сообщения могут прийти в ином порядке, чем произошли переключения. Поздно полученное сообщение о более раннем положении дополняет историю.

Получение описывает доставку сведений. Какое положение применимо к расчёту, определяет предметное правило по времени действия и подтверждению. Транспорт, квитанции и формат сообщения исследованием не заданы.

Основание — решения условной организации в исследовании полевых сведений. [NET-13](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-13) · [Исходный процесс](../../RAW_inputs/documents/UtilityGisEditor.md#базовые-и-продвинутые-workflows).
