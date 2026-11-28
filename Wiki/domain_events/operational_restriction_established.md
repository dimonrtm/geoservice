---
title: "Подтверждено эксплуатационное ограничение актива"
type: domain-event
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/2026-11-27-field-information-answers.md"
tags: [domain-knowledge, utility-gis, field-evidence]
confidence: inferred
related: [DDD_Wiki/aggregates/network_asset, Wiki/commands/record_operational_restriction, Wiki/specifications/operational_restriction_evidenced]
---

# Подтверждено эксплуатационное ограничение актива

## Source Aggregate

[[DDD_Wiki/aggregates/network_asset|Актив]] хранит основание доступности. Сведения поступают от эксплуатации или из проверенного фактического отключения.

## Happened In The Past

Для опознанного актива установлено, какую часть затрагивает ограничение, в чём оно состоит, когда действовало и чем подтверждено. Подтверждение эксплуатации или проверенное свидетельство отключения позволяет различить временное ограничение и постоянный вывод.

## Downstream Reactions

Эксплуатация и диспетчер учитывают новую доступность в пределах установленного действия. Зафиксированный дефект и списание в учётной системе могут вызвать проверку. До выяснения характера отключения диспетчер получает признак неопределённости. Осмотры и запись о физическом присутствии сохраняются на активе.

Решения условной организации через `expert_repson`. [NET-08](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-08) · [NET-16](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-16) · [Офисная, полевая и оперативная работа с сетью](../../RAW_inputs/documents/UtilityGisEditor.md#базовые-и-продвинутые-workflows).
