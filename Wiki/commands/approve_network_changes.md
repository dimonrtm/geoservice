---
title: "Утвердить проверенные изменения сети"
type: command
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/UtilityGisEditor.md"
tags: [domain-knowledge, utility-gis]
confidence: inferred
related: [DDD_Wiki/aggregates/network_edit_version, Wiki/policies/publication, Wiki/domain_events/network_changes_approved]
---

# Утвердить проверенные изменения сети

## Actor

Участник с полномочием утверждения.

## Target

Предъявленный проверенный объём рабочей версии.

## Preconditions

Утверждающему доступны состав правок, основания, результаты проверки правил и топологии и разрешение конфликтов в указанном объёме.

## Outcome

В рабочей версии фиксируют рассмотренный состав и [[Wiki/domain_events/network_changes_approved|решение об утверждении]]. Этот объём можно передать на публикацию. Выявленная ошибка требует исправления и повторной проверки. Совмещение полномочий и последствия последующей смежной правки остаются открытыми в NET-02 и NET-06. [[Wiki/_registry/questions|Реестр вопросов]].

Основание в исходной модели. [Офисная, полевая и оперативная работа с сетью](../../RAW_inputs/documents/UtilityGisEditor.md#базовые-и-продвинутые-workflows).
