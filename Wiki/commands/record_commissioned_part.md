---
title: "Учесть ввод построенной части в эксплуатацию"
type: command
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/2026-11-27-field-information-answers.md"
tags: [domain-knowledge, utility-gis, field-evidence]
confidence: inferred
related: [DDD_Wiki/aggregates/network_asset, Wiki/specifications/built_part_traceable, Wiki/domain_events/part_commissioning_confirmed]
---

# Учесть ввод построенной части в эксплуатацию

## Actor

Эксплуатация подтверждает допуск, редактор учитывает его для соответствующей части сети.

## Target

Подтверждённый объём ввода и основание в эксплуатационном состоянии актива.

## Preconditions

Границы допуска позволяют отличить введённую часть от остальной стройки. Форма подтверждения зависит от отрасли.

## Outcome

После учёта допуска доступна запись о вводе для указанной части. Для трассировки диспетчер отдельно проверяет, какие рабочие подключения введённой части установлены в опубликованной сети. При частичном вводе допуск распространяется только на указанную часть. Если врезка неизвестна, путь через неё остаётся недоступен даже при подтверждённом вводе. [[Wiki/specifications/built_part_traceable|Условия участия в трассировке]].

Решения условной организации через `expert_repson`. [NET-10](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-10) · [NET-09](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-09) · [Офисная, полевая и оперативная работа с сетью](../../RAW_inputs/documents/UtilityGisEditor.md#базовые-и-продвинутые-workflows).
