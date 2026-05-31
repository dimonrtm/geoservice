---
title: Фазы Наполнения Wiki
type: method
status: active
created: 2026-05-30
updated: 2026-05-30
source: null
tags: [wiki, discovery, phases]
---

# Фазы Наполнения Wiki

Этот файл задает порядок, в котором discovery наполняет project knowledge wiki. Фазы нужны, чтобы агент не прыгал к решению до понимания проблемы, пользователей и ограничений.

## Принцип

- Первый `/discover` задает только стартовую анкету и создает пустые solution-артефакты.
- Фазы Ф1-Ф3 закрывают проблему, пользователей и рынок.
- Ф4 переходит к решению и scope.
- Ф5-Ф7 уточняют бизнес, ограничения, NFR, метрики и риски.
- Ф8 превращает встречу в wiki-ноды и follow-up'ы.

## Карта Фаз

| Фаза | Цель | Основные Ноды |
|---|---|---|
| Ф0 | Подготовить материалы и участников | `RAW_inputs/`, `memory/project-state.md` |
| Ф1 | Понять проблему и why-now | `Vision_wiki/concepts/about_project.md`, PVB, LC |
| Ф2 | Понять пользователей и боль | `Vision_wiki/entities/personas/`, JTBD, USM |
| Ф3 | Понять альтернативы и рынок | `Vision_wiki/entities/competitors/`, LC, RAL |
| Ф4 | Определить решение и scope | `Vision_wiki/solution/USM.md`, `roadmap.md`, `architecture_vision.md` |
| Ф5 | Определить внедрение и бизнес-модель | LC, roadmap, constraints |
| Ф6 | Собрать ограничения и NFR | `Vision_wiki/solution/nfr.md`, `Vision_wiki/decisions/constraints.md` |
| Ф7 | Определить метрики и риски | `Vision_wiki/concepts/metrics.md`, RAL, follow-up'ы |
| Ф8 | Разнести результаты по wiki | `Vision_wiki/chats/`, `Vision_wiki/decisions/followups/index.md`, `memory/project-state.md` |

## Стартовые Solution-Артефакты

Первый `/discover` должен проверить и при необходимости создать:

- `Vision_wiki/solution/USM.md`
- `Vision_wiki/solution/roadmap.md`
- `Vision_wiki/solution/nfr.md`
- `Vision_wiki/solution/architecture_vision.md`

Эти файлы остаются черновиками до появления ответов или RAW sources. Не заполнять их догадками.
