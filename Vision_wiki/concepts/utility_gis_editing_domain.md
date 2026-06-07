---
title: Utility GIS Editing Domain
type: concept
status: draft
created: 2026-06-07
updated: 2026-06-07
source: RAW_inputs/documents/utility_gis_editor_domain_dictionary.md
tags: [utility-network, domain-language, authoritative-editing, workflow]
---

# Utility GIS Editing Domain

## Определение

`Utility GIS editing` - управляемое изменение инженерной сети через рабочие версии, проверки сетевых правил, обнаружение конфликтов и контролируемую публикацию в authoritative state.

## Почему Это Не CRUD Карты

Изменение geometry или attributes может нарушить connectivity, trace или downstream use. Поэтому сохраненный объект еще не считается официальным: система должна отделять `Edit version` от `Default`, запрещать silent overwrite и показывать доказуемый путь от work order до post.

## Канонический Workflow

1. `Utility GIS editor` получает `Work order` и открывает `AOI`.
2. Система создает `Edit version` от текущего `Default`.
3. Editor меняет `Network feature` или `Association` и сохраняет `Change set`.
4. Изменения создают область, требующую `Validation`.
5. `Reconcile` сравнивает рабочую версию с актуальным `Default`.
6. Обнаруженные `Conflict` явно разрешаются через conflict view.
7. `Reviewer` принимает или отклоняет подготовленные изменения.
8. `Post` публикует проверенный результат в `Default`; версия закрывается.

## Основные Термины

| Термин | Значение Для GeoService |
|---|---|
| `Network feature` | Объект инженерной сети: line, device, junction или другой пространственный элемент. |
| `Association` | Непространственная связь между сетевыми объектами. |
| `Edit version` | Изолированный рабочий контекст правок до публикации. |
| `Default` | Основное опубликованное состояние данных. |
| `Authoritative state` | Доверенное состояние, доступное downstream consumers после контролируемого post. |
| `Validation` | Проверка demo network rules, connectivity и допустимости изменений. |
| `Reconcile` | Сравнение edit version с изменившимся `Default`. |
| `Conflict` | Конкурирующие несовместимые изменения объекта, атрибута, geometry или association. |
| `Post` | Публикация проверенных изменений из edit version в `Default`. |
| `Audit trail` | История actor, action, work order/version, before/after, review и результата. |

## Языковые Границы

- `Save edit` означает сохранение в рабочей версии, а не публикацию.
- `Post to Default` означает изменение authoritative state.
- `Validation error`, `topology error` и `connectivity error` точнее общего выражения "ошибка сети".
- `Attribute conflict`, `geometry conflict`, `update/delete conflict` и `association conflict` точнее выражения "конфликт карты".

## Граница Текущего Demo

Источник описывает домен шире Release 1. Для текущего GeoService приняты упрощенная change-set модель, demo validation, explicit review и optimistic conflicts. Full branch versioning, production topology engine, trace engine и production utility network model остаются non-goals.

## Неясно

- Какие части словаря станут публичными API names после проектирования implementation contract.
- Какие demo network rules достаточно убедительно показывают последствия geometry/association conflict.

## Источники

- `RAW_inputs/documents/utility_gis_editor_domain_dictionary.md`

## Связи

- [[../chats/2026-06-07-utility-gis-editor-domain-dictionary]]
- [[../entities/personas/utility_gis_editor]]
- [[jtbd]]
- [[../solution/USM]]
- [[../solution/architecture_vision]]
- [[../../Code_wiki/глоссарий/technical_terms]]
