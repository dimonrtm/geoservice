---
title: Utility GIS Editing Domain
type: concept
status: active
created: 2026-06-07
updated: 2026-06-13
source: "RAW_inputs/documents/utility_gis_editor_domain_dictionary.md; RAW_inputs/meetings/utility_gis_editor_broad_domain_answers.md; RAW_inputs/meetings/utility_gis_reviewer_broad_domain_answers.md"
tags: [utility-network, domain-language, authoritative-editing, workflow, as-built, network-model]
---

# Utility GIS Editing Domain

## Определение

`Utility GIS editing` - управляемое изменение инженерной сети через рабочие версии, проверки сетевых правил, обнаружение конфликтов и контролируемую публикацию в authoritative state.

Изменение затрагивает две связанные модели:

- physical network state: расположение, geometry, оборудование и фактическое
  as-built состояние;
- logical network state: connectivity, associations, topology, trace и
  эксплуатационное поведение сети.

## Почему Это Не CRUD Карты

Изменение geometry или attributes может нарушить connectivity, trace или downstream use. Поэтому сохраненный объект еще не считается официальным: система должна отделять `Edit version` от `Default`, запрещать silent overwrite и показывать доказуемый путь от work order до post.

Field reality может отличаться от проектной схемы. As-built/redlining pipeline
должен связывать work order, redline, фотографии, оборудование и фактические
изменения с GIS change set.

## Канонический Workflow

1. `Utility GIS editor` получает `Work order` и открывает `AOI`.
2. Система создает `Edit version` от текущего `Default`.
3. Editor меняет `Network feature` или `Association` и сохраняет `Change set`.
4. Изменения создают область, требующую `Validation`.
5. `Reconcile` сравнивает рабочую версию с актуальным `Default`.
6. Обнаруженные `Conflict` явно разрешаются через conflict view.
7. `Reviewer` оценивает review package и принимает или отклоняет
   подготовленные изменения.
8. `Publisher` выполняет `Post` проверенного результата в `Default`; в
   упрощенном Release 1 эту responsibility несет роль `Reviewer`.
9. Audit сохраняет evidence решения и итог authoritative state.

## Основные Термины

| Термин | Значение Для GeoService |
|---|---|
| `Network feature` | Объект инженерной сети: line, device, junction или другой пространственный элемент. |
| `Association` | Непространственная связь между сетевыми объектами. |
| `Edit version` | Изолированный рабочий контекст правок до публикации. |
| `Default` | Основное опубликованное состояние данных. |
| `Authoritative state` | Доверенное состояние, доступное downstream consumers после контролируемого post. |
| `Physical network state` | Геометрия, размещение, оборудование и фактическое as-built состояние сети. |
| `Logical network state` | Connectivity, associations, topology и trace-поведение сети. |
| `As-built / redline` | Evidence фактически выполненных полевых работ относительно проекта или прежней схемы. |
| `Validation` | Проверка demo network rules, connectivity и допустимости изменений. |
| `Reconcile` | Сравнение edit version с изменившимся `Default`. |
| `Conflict` | Конкурирующие несовместимые изменения объекта, атрибута, geometry или association. |
| `Post` | Публикация проверенных изменений из edit version в `Default`. |
| `Review package` | Связанный набор diff, validation, trace, conflicts, work order, документов, фотографий, comments и audit context. |
| `Publisher` | Responsibility финальной публикации approved change set; может быть отдельной организационной ролью. |
| `Audit trail` | История actor, action, work order/version, before/after, review и результата. |

## Языковые Границы

- `Save edit` означает сохранение в рабочей версии, а не публикацию.
- `Post to Default` означает изменение authoritative state.
- `Validation error`, `topology error` и `connectivity error` точнее общего выражения "ошибка сети".
- `Attribute conflict`, `geometry conflict`, `update/delete conflict` и `association conflict` точнее выражения "конфликт карты".
- `Approve` означает разрешение публикации конкретного неизмененного change
  set; оно не обязательно совпадает с технической операцией `Post`.
- `QA/QC passed` не означает, что инженерный смысл изменения подтвержден.

## Review Package

Минимальный review context отвечает на пять вопросов:

1. Что изменилось?
2. Почему изменилось?
3. Чем подтверждено?
4. Как изменение влияет на physical и logical network state?
5. Почему результат безопасно публиковать как authoritative?

Для connectivity changes одного trace недостаточно: нужен набор контрольных
сценариев по измененному и соседним объектам.

## Граница Текущего Demo

Источник описывает домен шире Release 1. Для текущего GeoService приняты упрощенная change-set модель, demo validation, explicit review и optimistic conflicts. Full branch versioning, production topology engine, trace engine и production utility network model остаются non-goals.

Electric, water, gas и telecom используют сходную physical/logical network
рамку, но требуют разных domain rules. Release 1 остается electric demo и не
становится универсальной multi-utility platform.

## Неясно

- Какие части словаря станут публичными API names после проектирования implementation contract.
- Какие demo network rules достаточно убедительно показывают последствия geometry/association conflict.
- Должны ли `Reviewer` и `Publisher` быть разными ролями вне demo.
- Нужен ли routing review queue по domain expertise и уровню риска.

## Источники

- `RAW_inputs/documents/utility_gis_editor_domain_dictionary.md`
- `RAW_inputs/meetings/utility_gis_editor_broad_domain_answers.md`
- `RAW_inputs/meetings/utility_gis_reviewer_broad_domain_answers.md`

## Связи

- [[../chats/2026-06-07-utility-gis-editor-domain-dictionary]]
- [[../chats/2026-06-13-utility-gis-editor-broad-domain-rehearsal]]
- [[../chats/2026-06-13-utility-gis-reviewer-broad-domain-rehearsal]]
- [[../entities/personas/utility_gis_editor]]
- [[../entities/personas/utility_gis_reviewer]]
- [[jtbd]]
- [[../solution/USM]]
- [[../solution/architecture_vision]]
- [[../../Code_wiki/глоссарий/technical_terms]]
