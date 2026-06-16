---
title: Граница High И Critical Для Trace Change
type: conflict
status: resolved
created: 2026-06-14
updated: 2026-06-16
source: "RAW_inputs/meetings/release2_conflict_explanation_editor_reviewer_answers.md; RAW_inputs/meetings/Reviwer Decision.md"
tags: [conflict, release-2, risk-tier, trace, conflict-explanation, resolved]
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

## Решение

`RAW_inputs/meetings/Reviwer Decision.md` разрешает расхождение для planned
Release 2 policy:

- trace change не становится `Critical` автоматически;
- `Critical` возникает, когда trace delta меняет authoritative network
  behavior: affected service, subnetwork, controllers, safety isolation,
  traversability/barriers, rule-dependent connectivity или operational outputs;
- trace delta без service/subnetwork/safety semantics и без
  rule/terminal/controller impact может оставаться `High`;
- association diff или trace change остаются минимум `High`, если затрагивают
  сетевой смысл пакета и требуют reviewer decision.

## Последствия

- [[../conflict_resolution_routing]] обновлен: `Critical` теперь связан не с
  самим фактом trace delta, а с изменением authoritative network behavior.
- [[../release_2_conflict_explanation]] обновлен: reviewer decision работает с
  change package, а approval и `post authorization` разделены.
- `FU-2026-06-14-002` можно считать resolved для planned policy; отдельная
  user validation Release 2 routing остается открытой через `FU-2026-06-14-001`.
- Текущий Release 1 не меняется.
