---
title: "Восстановление услуги подтверждено"
type: domain-event
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/2026-11-27-field-information-answers.md"
tags: [domain-knowledge, utility-gis, field-evidence]
confidence: inferred
related: [DDD_Wiki/aggregates/network_work_order, Wiki/commands/record_service_restoration, DDD_Wiki/use_cases/outage_workflow]
---

# Восстановление услуги подтверждено

## Source Aggregate

[[DDD_Wiki/aggregates/network_work_order|Наряд]] учитывает результат для указанной части работ и сохраняет неподтверждённый остаток. По одному сообщению можно подтвердить несколько точек, если для каждой из них установлено восстановление.

## Happened In The Past

Диспетчер установил факт восстановления услуги в определённых точках или на установленном участке на указанное время. Это может произойти после сообщения об окончании ремонта. Неполученное показание оставляет результат по точке неизвестным.

## Downstream Reactions

Эксплуатация отражает подтверждённый объём в сети, диспетчер учитывает выполненную часть наряда. Если у остальных потребителей услуга ещё не подтверждена, остаток работы открыт.

Основание — решения условной организации в исследовании полевых сведений. [NET-03](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-03) · [Исходный процесс](../../RAW_inputs/documents/UtilityGisEditor.md#базовые-и-продвинутые-workflows).
