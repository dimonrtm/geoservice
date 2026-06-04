---
title: Product Vision Board GeoService
type: concept
status: draft
created: 2026-05-31
updated: 2026-06-04
source: "Vision_wiki/chats/2026-05-31-phase-f1-why-now.md; Vision_wiki/chats/2026-06-02-phase-f2-users-and-pain.md; RAW_inputs/documents/03.06.2026deep-research-report.md; Vision_wiki/chats/2026-06-04-phase-f4-solution-scope.md"
tags: [product-vision-board, discovery, research]
---

# Product Vision Board GeoService

## Vision

Исследовать подходы к совместному редактированию геометрии и проверить, насколько далеко можно довести сложную геоинформационную систему методами AI-first разработки.

## Target Group

- Подтверждено: разработчик проекта как исследователь и первый пользователь.
- Гипотеза Ф2: primary research-persona - `Utility GIS editor`, работающий с authoritative network layer. Кадастровый сценарий отложен как более сложный для реализации.

## Needs

- Подтверждено: практическое исследование различных методов совместного редактирования геометрии.
- Гипотеза: контролируемое совместное изменение utility network без silent overwrite и без неверного состояния сети после параллельных правок.
- Гипотеза Ф3: наиболее узкая зона ценности - объяснение сложного utility conflict, review decision и доказуемость authoritative post, а не замена полноценной GIS-платформы.

## Product

Ф4 зафиксировала приоритет результата как demo. Текущий product-scope - focused conflict/review layer для `Utility GIS editor`, который показывает, что review сетевой правки стал проще и безопаснее: изменение проходит working version, validation, сравнение с authoritative state, reviewer decision и publication без silent overwrite.

## Business Goals

- Главный приоритет Ф4: подготовить работающий demo.
- Portfolio, применение в реальной работе и будущий продукт остаются вторичными возможными результатами, но не расширяют scope текущего релиза.

## Связи

- [[about_project]]
- [[lean_canvas]]
- [[jtbd]]
- [[../chats/2026-05-31-phase-f1-why-now]]
- [[../chats/2026-06-02-phase-f2-users-and-pain]]
- [[../chats/2026-06-03-phase-f3-alternatives]]
- [[../chats/2026-06-04-phase-f4-solution-scope]]
- [[../entities/personas/authoritative_gis_editing_candidates]]
- [[../entities/personas/utility_gis_editor]]
- [[../solution/USM]]
