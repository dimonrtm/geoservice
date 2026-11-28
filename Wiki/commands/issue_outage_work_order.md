---
title: "Сформировать оперативное задание по трассировке"
type: command
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/2026-11-27-field-information-answers.md"
tags: [domain-knowledge, utility-gis, field-evidence]
confidence: inferred
related: [DDD_Wiki/aggregates/network_work_order, Wiki/policies/operational_trace, Wiki/value_objects/calculated_outage_extent]
---

# Сформировать оперативное задание по трассировке

## Actor

Диспетчер, определяющий работу аварийной бригады.

## Target

Наряд для бригады на проверку устройств и затронутых ветвей проблемного участка.

## Preconditions

Диспетчер выбирает проблемный участок, время расчёта и опубликованные рабочие подключения. По связности, направлению и применимым положениям устройств он определяет отключающие устройства и области проверки.

## Outcome

Если на результат влияет неизвестное положение, диспетчер сравнивает правдоподобные варианты и указывает в наряде отдельно определённый и возможный расчётный охват. Бригада получает также запрос на проверку спорного устройства. Если из-за других пробелов варианты сравнить нельзя, в задании указывают «охват не установлен». По ответу поля диспетчер обновляет расчёт. Для закрытия работ требуется подтверждение возврата услуги на соответствующей части. [[Wiki/value_objects/calculated_outage_extent|Значение охвата]].

Решения условной организации через `expert_repson`. [NET-12](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-12) · [NET-13](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-13) · [NET-03](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-03) · [Офисная, полевая и оперативная работа с сетью](../../RAW_inputs/documents/UtilityGisEditor.md#базовые-и-продвинутые-workflows).
