---
title: Старый Release 1 Против Utility Workflow
type: conflict
status: active
created: 2026-06-11
updated: 2026-06-11
source: "RAW_inputs/documents/спринт 1.odt; user answers to /discover --phase Ф8, 2026-06-11"
tags: [conflict, release-1, utility-gis-editor]
---

# Старый Release 1 Против Utility Workflow

## Конфликтующие Утверждения

Старый Release 1 определял продукт через generic layers, Feature CRUD, WebSocket и object-level `version`/`409`.

Ф2-Ф8 определили основной продуктовый сценарий как полный `Utility GIS editor` workflow: work order, edit version, validation, reconcile, conflict resolution, review, post и audit.

Одновременное использование обоих определений как равноправного scope создает два разных продукта и противоречивые acceptance criteria.

## Решение

Активным является новый Release 1 из [[../release_1_utility_workflow]].

Generic capabilities сохраняются только как внутренний foundation. Старые requirements и desired API notes остаются историческими источниками до отдельной docs-синхронизации по `FU-2026-06-11-002`.

## Последствия

- Generic layer picker и свободный Feature CRUD не определяют готовность Release 1.
- Обязательна code compliance matrix против нового workflow.
- Старые docs нельзя использовать как текущий product contract без оговорки superseded.

## Связи

- [[../../chats/2026-06-11-phase-f8-release-1-closeout]]
- [[../release_1_utility_workflow]]
- [[../followups/index]]
- [[../../concepts/first_release_mvp]]
- [[../../solution/USM]]
