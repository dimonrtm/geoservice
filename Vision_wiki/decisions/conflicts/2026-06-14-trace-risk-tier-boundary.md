---
title: Граница High И Critical Для Trace Change
type: conflict
status: needs-review
created: 2026-06-14
updated: 2026-06-14
source: RAW_inputs/meetings/release2_conflict_explanation_editor_reviewer_answers.md
tags: [conflict, release-2, risk-tier, trace, conflict-explanation]
---

# Граница High И Critical Для Trace Change

## Конфликтующие Утверждения

- Новый источник: association diff или trace change требуют минимум `High`;
  `Critical` возникает при affected service/customers, safety/isolation impact,
  network rule violation или subnetwork error.
- Существующая planned нода [[../conflict_resolution_routing]]: любое изменение
  trace входит в определение `Critical`.

## Источники

- Новый источник:
  `RAW_inputs/meetings/release2_conflict_explanation_editor_reviewer_answers.md`.
- Старая нода: [[../conflict_resolution_routing]], основанная на
  `RAW_inputs/meetings/utility_gis_editor_geometry_association_conflict_answers.md`.

Оба RAW-файла являются доверенными design/research inputs, но не direct user
evidence. Новый источник новее и подробнее описывает explanation, однако сам по
себе не дает достаточного основания молча заменить ранее принятую границу.

## Действие

До реализации Release 2 согласовать классификацию на сценариях:

- trace changed, но affected service/subnetwork не изменились;
- trace changed ожидаемо и подтвержден work order;
- trace changed вместе с safety/isolation impact;
- association changed без изменения connectivity и trace.

Решение вести через `FU-2026-06-14-002`. Текущий Release 1 не менять.
