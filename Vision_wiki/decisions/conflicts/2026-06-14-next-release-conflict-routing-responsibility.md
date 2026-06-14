---
title: Ответственный И Эскалация В Conflict Routing Следующего Релиза
type: conflict
status: resolved
created: 2026-06-14
updated: 2026-06-14
source: "RAW_inputs/meetings/utility_gis_editor_geometry_association_conflict_answers.md; user clarification on source trust, 2026-06-14"
tags: [conflict, next-release, conflict-resolution, routing, responsibility, resolved]
---

# Ответственный И Эскалация В Conflict Routing Следующего Релиза

## Конфликтующие Утверждения

Planned workshop decision [[../conflict_resolution_routing]] утверждает:

- простой конфликт первым решает автор изменения в `Default`;
- `High` эскалируется профильному специалисту через 2 рабочих часа;
- `Simple` эскалируется через 2 рабочих дня.

Новый синтетический источник предлагает:

- первое предложение делает автор edit version;
- окончательное назначение лучше определять по affected network area,
  компетенции и risk tier, а не по авторству;
- `High` решает `Reviewer` после предложения `Editor`;
- безопасный `Normal` может проходить с audit и sample review;
- `Simple` лучше не эскалировать.

Обе модели согласны, что critical network impact блокирует `post`, требует
совместной проверки и при необходимости участия профильного специалиста и
Data Owner.

## Источники

- Новый источник:
  `RAW_inputs/meetings/utility_gis_editor_geometry_association_conflict_answers.md`.
- Summary:
  [[../../chats/2026-06-14-utility-gis-editor-conflict-routing-synthetic-research]].
- Старая нода: [[../conflict_resolution_routing]].
- Workshop:
  [[../../chats/2026-06-14-geometry-association-conflict-resolution-workshop]].

## Решение

Пользователь установил иерархию доверия:

1. `RAW_inputs/meetings/utility_gis_editor_geometry_association_conflict_answers.md`
   является более доверенным design/research source.
2. Assistant-led workshop в чате является менее доверенным input и сохраняется
   только как история развилки.

Planned decision [[../conflict_resolution_routing]] обновлен по RAW source:

- routing определяется affected network area, компетенцией и risk tier;
- `Simple` не требует обязательной эскалации;
- безопасный `Normal` допускает audit + sample review;
- `High` решает `Reviewer` после предложения `Editor`;
- `Critical` требует совместного решения и немедленного подключения профильного
  специалиста.

## Остаточный Follow-up

`FU-2026-06-14-001` остается открытым не для выбора между двумя источниками, а
для проверки канонической planned модели с реальными `Editor` и `Reviewer`.
Текущий Release 1 не меняется.
