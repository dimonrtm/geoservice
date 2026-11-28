---
title: "Зарегистрировать полевое наблюдение по наряду"
type: command
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/2026-11-27-field-information-answers.md"
tags: [domain-knowledge, utility-gis, field-evidence]
confidence: inferred
related: [DDD_Wiki/aggregates/field_observation, Wiki/commands/identify_observed_asset, Wiki/value_objects/evidence_extent]
---

# Зарегистрировать полевое наблюдение по наряду

## Actor

Полевая бригада передаёт наблюдение, редактор принимает его в офисе.

## Target

Отдельный [[DDD_Wiki/aggregates/field_observation|замер или осмотр]] по наряду с собственным обозначением.

## Preconditions

Известны место, время, результат замера или осмотра, ориентиры и доступный материал. Если рядом две похожие задвижки, бригада указывает обе возможные привязки.

## Outcome

Офис может учесть наблюдение, даже когда карточки кандидатов ещё нельзя менять. Дефект привязывают к месту и охвату осмотра, повторный осмотр дополняет историю. При наличии отличительного признака редактор [[Wiki/commands/identify_observed_asset|устанавливает актив]]. Для изменения его доступности требуется отдельное эксплуатационное основание. Так, фотография опознанного насоса даёт свидетельство его присутствия, а для вывода о подключении нужны другие сведения.

Решения условной организации через `expert_repson`. [NET-07](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-07) · [NET-08](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-08) · [NET-16](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-16) · [Офисная, полевая и оперативная работа с сетью](../../RAW_inputs/documents/UtilityGisEditor.md#базовые-и-продвинутые-workflows).
