---
title: Новый Release 1 Utility GIS Workflow
type: decision
status: active
created: 2026-06-11
updated: 2026-06-11
source: "user answers to /discover --phase Ф8, 2026-06-11; docs/superpowers/specs/2026-06-11-release-1-utility-workflow-design.md"
tags: [decision, release-1, utility-gis-editor, workflow]
---

# Новый Release 1 Utility GIS Workflow

## Контекст

Старый Release 1 описывал generic browser GIS: layers, bbox, Feature CRUD, WebSocket и object-level `version`/`409`. Discovery Ф2-Ф7 выбрал `Utility GIS editor` и сформировал более конкретный authoritative editing workflow, но старый и новый scope оставались смешаны в одних нодах.

## Решение

`Utility GIS editor` становится единственным основным сценарием Release 1.

Обязательный путь:

`Login -> Work order -> Edit version -> Network edit -> Validation -> Reconcile -> Conflict resolution -> Submit review -> Reviewer approval -> Post to Default -> Audit verification`.

Generic `Layer/Feature CRUD`, bbox, MapLibre, PostGIS, JWT, `version`/`409` и WebSocket сохраняются как внутренний технический foundation. Они не являются отдельным пользовательским сценарием или самостоятельным критерием готовности.

## Обоснование

- Utility workflow дает конкретную пользовательскую задачу и критерий безопасного результата.
- Текущий код содержит полезный foundation, поэтому полная перепись не нужна.
- Параллельное сохранение двух публичных продуктов размоет scope.
- Полный workflow нужен, чтобы проверить authoritative post, а не только карту и CRUD.

## Последствия

- Старое generic определение Release 1 заменяется новым.
- API и frontend проектируются вокруг work orders и edit versions.
- `Editor` и `Reviewer` разделены.
- Post требует validation, reconcile, conflict resolution и approval.
- `synthetic_utility_feeder_01` является обязательным demo dataset.
- Старые requirements/docs требуют отдельной синхронизации с новым Release 1.
- Текущий код требует compliance audit и значительной доменной достройки.

## Связи

- [[../chats/2026-06-11-phase-f8-release-1-closeout]]
- [[../concepts/first_release_mvp]]
- [[../solution/USM]]
- [[../solution/architecture_vision]]
- [[../solution/nfr]]
- [[../solution/roadmap]]
- [[followups/index]]
- [[conflicts/2026-06-11-old-release-1-vs-utility-workflow]]
- [Design spec](../../docs/superpowers/specs/2026-06-11-release-1-utility-workflow-design.md)
