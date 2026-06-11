---
title: Release 1 MVP
type: concept
status: active
created: 2026-05-30
updated: 2026-06-11
source: "RAW_inputs/documents/спринт 1.odt; Vision_wiki/chats/2026-06-04-phase-f4-solution-scope.md; RAW_inputs/documents/utility_gis_editor_acceptance_criteria.md; user answers to /discover --phase Ф8, 2026-06-11"
tags: [concept, release-1, mvp, utility-gis-editor]
---

# Release 1 MVP

## Определение

Release 1 - полный vertical slice `Utility GIS editor`:

`Login -> Work order -> Edit version -> Network edit -> Validation -> Reconcile -> Conflict resolution -> Submit review -> Reviewer approval -> Post to Default -> Audit verification`.

Старое generic GIS определение заменено решением Ф8. JWT, PostGIS, MapLibre, bbox, Feature CRUD, `version`/`409` и WebSocket сохраняются только как внутренний технический foundation.

## Что Известно

- Основной пользователь: `Utility GIS editor`.
- Роли Release 1: `Editor` и `Reviewer`, совмещение запрещено.
- Обязательные сущности: `WorkOrder`, `EditVersion`, `NetworkFeature`, `NetworkAssociation`, `ChangeSet`, validation, reconcile, conflict, review, post и audit.
- Dataset: `synthetic_utility_feeder_01`.
- Главный результат: безопасный authoritative post без silent overwrite.
- Полный критерий описан в [[../decisions/release_1_utility_workflow]].

## Граница

В scope входят feature/association change sets, demo validation, reconcile, conflict explanation `Base / Mine / Default`, reviewer decision, transactional post и audit.

Не входят generic GIS как отдельный продукт, full branch versioning, production topology/trace engine, offline sync, CRDT/OT, rich ACL, external GIS и реальные utility data.

Главный критерий готовности: полный demo workflow завершается post в `Default`; protective failures сохраняют edits, а audit доказывает всю цепочку.

## Источники

- `RAW_inputs/documents/спринт 1.odt`
- `Vision_wiki/chats/2026-06-04-phase-f4-solution-scope.md`
- `RAW_inputs/documents/utility_gis_editor_acceptance_criteria.md`

## Связи

- [[../solution/USM]]
- [[../solution/roadmap]]
- [[../decisions/release_1_utility_workflow]]
- [[../chats/2026-06-11-phase-f8-release-1-closeout]]
- [[../chats/2026-06-04-phase-f4-solution-scope]]
- [[../../Code_wiki/архитектура/api_contract_first_release_requirements]]
- [[../chats/2026-05-31-initial-discover]]
