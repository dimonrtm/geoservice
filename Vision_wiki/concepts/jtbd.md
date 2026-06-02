---
title: JTBD GeoService
type: concept
status: draft
created: 2026-06-02
updated: 2026-06-02
source: "user answers to /discover --phase Ф2, 2026-06-02; RAW_inputs/documents/Ф2.md"
tags: [jtbd, discovery, phase-f2, authoritative-editing, research]
---

# JTBD GeoService

## Статус

JTBD ниже являются research-гипотезами. `Utility GIS editor` выбран как primary research-persona; кадастровый сценарий сохранен как deferred. Гипотезы еще не подтверждены наблюдением реального рабочего процесса.

## Job Statements

| Когда | Пользователь Хочет | Чтобы |
|---|---|---|
| `Utility GIS editor` вносит изменения в инженерную сеть параллельно с другими редакторами | Изолировать свои изменения, увидеть конфликт с authoritative state и контролируемо опубликовать результат | Не допустить неверного состояния сети, сохранить правки и получить проверяемое состояние после review |
| Кадастровый инженер выполняет split/merge участков параллельно с другими делами | Сохранить lineage, разобрать конфликт и опубликовать согласованное кадастровое изменение | Не допустить юридически значимой ошибки границ и сохранить прослеживаемую историю; deferred research-сценарий |

## Текущий Обходной Путь

- Для обоих сценариев research описывает branch-like workflow: отдельная версия на рабочую задачу, reconcile/post, review перед публикацией и ручной разбор конфликтов.
- Для кадастра дополнительно важна дисциплина "одна версия - одно кадастровое дело".
- Для инженерной сети дополнительно важны topology validation и проверка authoritative network state.

## Desired Outcome

- Пользователь понимает, какие изменения конфликтуют, кто должен принять решение и можно ли безопасно публиковать результат.
- Authoritative state обновляется без silent overwrite и без потери прослеживаемости.

## Неясно

- Какие результаты даст synthetic pilot primary JTBD `Utility GIS editor`.
- Какие части workflow относятся к Release 1, а какие остаются Later.

## Связи

- [[../entities/personas/authoritative_gis_editing_candidates]]
- [[../entities/personas/utility_gis_editor]]
- [[../chats/2026-06-02-phase-f2-users-and-pain]]
- [[../solution/USM]]
- [[../decisions/followups/index]]
