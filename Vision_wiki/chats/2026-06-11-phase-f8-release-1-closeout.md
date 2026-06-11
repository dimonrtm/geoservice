---
title: Ф8 Новый Release 1 Utility GIS Workflow
type: session
status: active
created: 2026-06-11
updated: 2026-06-11
source: "user answers to /discover --phase Ф8, 2026-06-11"
tags: [discovery, phase-f8, release-1, utility-gis-editor]
---

# Ф8 Новый Release 1 Utility GIS Workflow

## Контекст

Ф8 закрывает discovery Ф1-Ф7 и устраняет конфликт между старым generic Release 1 и выбранным сценарием `Utility GIS editor`.

## Ключевые Решения

- `Utility GIS editor` является единственным основным сценарием нового Release 1.
- Из старого Release 1 сохраняется только совместимый технический foundation.
- Generic `Layer/Feature CRUD` не является публичным пользовательским сценарием.
- Release 1 включает полный workflow до authoritative post.
- Подтверждены продуктовая граница, доменная модель, API/storage, frontend UX, ошибки, тесты и переход от текущего кода.
- Конфликт старого и нового scope зарегистрирован отдельно и разрешен в пользу utility workflow.

## Зафиксированные Гипотезы

- Change-set модель достаточна для demo вместо full branch versioning.
- Demo validation может убедительно показать utility safety.
- Пользователь поймет Save/Post, `EditVersion`/`Default` и conflict review.
- Текущий стек сможет выполнить draft P95.
- Synthetic workflow даст полезное evidence.

## Анализ Текущего Кода

Уже существует foundation:

- JWT login;
- PostGIS feature storage;
- layer discovery и bbox loading;
- generic Feature CRUD;
- optimistic concurrency `version`/`409`;
- WebSocket events;
- Vue/MapLibre frontend.

Критические пробелы:

- `WorkOrder`, `EditVersion` и change set;
- `NetworkAssociation`;
- validation;
- reconcile и conflict model;
- reviewer flow;
- transactional post;
- полный audit trail;
- utility dataset и reset semantics;
- work-order based frontend.

## Открытые Вопросы

- Фактическое соответствие кода новому Release 1.
- Конкретная implementation decomposition.
- Результаты UX, validation, conflict и performance experiments.
- Синхронизация старых requirements docs.

## Следующие Шаги

1. Подготовить implementation plan и code compliance matrix.
2. Реализовать один вертикальный `WorkOrder` от login до safe post.
3. После walking skeleton провести UX tests, conflict drill и benchmark.

## Связи

- [[../decisions/release_1_utility_workflow]]
- [[../decisions/conflicts/2026-06-11-old-release-1-vs-utility-workflow]]
- [[../concepts/first_release_mvp]]
- [[../solution/USM]]
- [[../decisions/followups/index]]
- [Design spec](../../docs/superpowers/specs/2026-06-11-release-1-utility-workflow-design.md)
