---
title: Reviewer Vs Publisher Responsibility
type: conflict
status: resolved
created: 2026-06-24
updated: 2026-06-26
source: "Vision_wiki/concepts/utility_gis_editing_domain.md; Vision_wiki/decisions/release_2_conflict_explanation.md; RAW_inputs/meetings/implementation_contract_for_review_and_post.md; RAW_inputs/meetings/ic_review_package_and_simulated_post.md"
tags: [domain-knowledge, conflict, review, post]
confidence: high
related: [Wiki/actors/reviewer, Wiki/actors/publisher, Wiki/commands/post_to_default]
---

# Reviewer Vs Publisher Responsibility

## Contradiction

Domain sources описывают `Publisher` как ответственность за финальную публикацию, но упрощенный Release 1 может возложить эту ответственность на `Reviewer`. Release 2 отдельно разводит `approve package` и `post authorization`.

## Blocks

Полную модель ролей/прав для post workflow и точный ownership команды `PostToDefault`.

## Evidence

- `Vision_wiki/concepts/utility_gis_editing_domain.md` различает review package и Publisher.
- `Vision_wiki/decisions/release_2_conflict_explanation.md` разделяет approve package и can post.

## Resolution Question

В целевой модели `Publisher` является отдельной ролью, ответственностью data owner или техническим шагом reviewer/post workflow?

## Resolution

`Publisher` является отдельной технической ролью / version administrator для `PostToDefault`. `Reviewer` принимает semantic `approve package`, но не становится владельцем authoritative state. В ближайшем integrated developer demo фактический post выполняет system actor `post-gate` через simulated post после reviewer decision и computed `can_post`, сохраняя границу ответственности для будущей целевой модели.
