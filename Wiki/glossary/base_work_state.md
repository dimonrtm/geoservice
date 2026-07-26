---
title: Базовое Состояние Работы
type: glossary
status: active
created: 2026-07-26
updated: 2026-07-26
source: RAW_inputs/meetings/tolerance_rules.md
tags: [domain-knowledge, glossary, work-order, baseline]
confidence: high
related: [Wiki/entities/work_order, Wiki/entities/edit_version, Wiki/value_objects/draft_version_token, DDD_Wiki/aggregates/edit_version]
---

# Базовое Состояние Работы

`Базовое состояние работы` — единое зафиксированное состояние сети, относительно которого оцениваются все изменения одной назначенной работы.

У отдельных линий может быть собственная история и номер последнего изменения, но они не образуют отдельные базовые состояния внутри той же работы. В материалах для редактора допустим синоним `исходное состояние работы`; внутренние названия хранилища не должны подменять этот термин.
