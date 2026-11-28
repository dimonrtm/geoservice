---
title: "Ввод построенной части подтверждён эксплуатацией"
type: domain-event
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/2026-11-27-field-information-answers.md"
tags: [domain-knowledge, utility-gis, field-evidence]
confidence: inferred
related: [DDD_Wiki/aggregates/network_asset, Wiki/commands/record_commissioned_part, Wiki/specifications/built_part_traceable]
---

# Ввод построенной части подтверждён эксплуатацией

## Source Aggregate

Эксплуатация — источник факта ввода. В модели GeoService [[DDD_Wiki/aggregates/network_asset|актив]] учитывает допуск и границы его действия.

## Happened In The Past

Эксплуатация засвидетельствовала допуск определённой части сети к использованию. В модели актива к введённому объёму относится основание допуска. Границы однозначно устанавливают, к какой части строящейся сети относится этот факт. Измерение, приёмка съёмки и публикация геометрии могли произойти раньше.

## Downstream Reactions

Диспетчер вправе учитывать эту часть в расчёте, когда известны её рабочие подключения. Остальной построенный объём сохраняет прежний статус. Неустановленная врезка продолжает ограничивать трассировку.

Решения условной организации через `expert_repson`. [NET-10](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-10) · [NET-09](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-09) · [Офисная, полевая и оперативная работа с сетью](../../RAW_inputs/documents/UtilityGisEditor.md#базовые-и-продвинутые-workflows).
