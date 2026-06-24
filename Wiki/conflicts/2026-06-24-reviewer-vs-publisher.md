---
title: Reviewer Vs Publisher Responsibility
type: conflict
status: active
created: 2026-06-24
updated: 2026-06-24
source: "Vision_wiki/concepts/utility_gis_editing_domain.md; Vision_wiki/decisions/release_2_conflict_explanation.md"
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
