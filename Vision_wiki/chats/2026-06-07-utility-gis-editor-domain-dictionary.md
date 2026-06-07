---
title: Utility GIS Editor Domain Dictionary
type: session
status: active
created: 2026-06-07
updated: 2026-06-07
source: RAW_inputs/documents/utility_gis_editor_domain_dictionary.md
tags: [ingest, utility-network, domain-language, glossary]
---

# Utility GIS Editor Domain Dictionary

## Контекст

Источник собирает единый язык предметной области `Utility GIS editing`: роли, сетевые объекты, версии, validation, reconcile/post, конфликты, audit и состояния workflow.

## Главные Тезисы

- `Utility GIS editor` изменяет не картинку, а официальную модель инженерной сети, от которой зависят trace, connectivity и downstream-системы.
- Рабочая правка живет в `Edit version`; сохранение правки не означает публикацию в `Default`.
- Безопасный путь к authoritative state требует validation, reconcile, явного разрешения конфликтов, review и post.
- Ключевые типы конфликтов для demo: attribute, geometry, update/delete и association conflict.
- Audit должен связывать изменение с actor, work order, review и опубликованным результатом.

## Терминологические Решения

- Использовать `Save edit` для записи в рабочую версию и `Post to Default` для публикации.
- Использовать `Network feature` как общий термин для line, device и junction.
- Не называть сценарий просто CRUD или редактированием карты: существенны topology, versions, conflicts и authoritative publication.
- Список domain commands из источника является словарем для проектирования, но не утвержденным API-контрактом.

## Граница Scope

Словарь описывает полноценный доменный контекст, но не отменяет ограничения Ф4: текущий GeoService остается focused demo с change-set моделью, demo validation и optimistic conflict/review flow, без production-grade branch versioning и topology engine.

## Follow-up

- Новых follow-up'ов не добавлено.
- Известный конфликт RAW Markdown frontmatter расширен на этот источник в `FU-2026-06-01-004`.

## Связи

- [[../concepts/utility_gis_editing_domain]]
- [[../entities/personas/utility_gis_editor]]
- [[../concepts/jtbd]]
- [[../solution/USM]]
- [[../solution/architecture_vision]]
- [[../../Code_wiki/глоссарий/technical_terms]]
- [[../decisions/followups/index]]
