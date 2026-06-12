---
title: JTBD GeoService
type: concept
status: active
created: 2026-06-02
updated: 2026-06-12
source: "user answers to /discover --phase Ф2, 2026-06-02; RAW_inputs/documents/Ф2.md; RAW_inputs/meetings/utility_gis_editor_answers.md"
tags: [jtbd, discovery, phase-f2, authoritative-editing, research, synthetic-evidence]
---

# JTBD GeoService

## Статус

Primary JTBD `Utility GIS editor` принят как активный design-contract на основе research и синтетической репетиции интервью. Он не подтвержден наблюдением реального рабочего процесса. Кадастровый сценарий сохранен как deferred.

## Job Statements

| Когда | Пользователь Хочет | Чтобы |
|---|---|---|
| `Utility GIS editor` вносит изменение по work order при неполных полевых данных и параллельной работе других редакторов | Собрать контекст изменения, изолировать правки, проверить connectivity/trace, разобрать conflicts и контролируемо опубликовать результат | Не допустить неверного состояния сети, сохранить lineage и сделать решение проверяемым для reviewer и следующего редактора |
| Кадастровый инженер выполняет split/merge участков параллельно с другими делами | Сохранить lineage, разобрать конфликт и опубликовать согласованное кадастровое изменение | Не допустить юридически значимой ошибки границ и сохранить прослеживаемую историю; deferred research-сценарий |

## Текущий Обходной Путь

- Для utility-сценария текущий обходной путь включает отдельную версию, reconcile/post, review перед публикацией и ручной разбор конфликтов.
- Контекст собирается вручную из GIS, work order, PDF, фотографий, Excel, справочников и сообщений.
- При возврате на исправление редактор повторяет validation, trace и reconcile и заново поднимает исходные материалы.
- Для кадастра дополнительно важна дисциплина "одна версия - одно кадастровое дело".
- Для инженерной сети дополнительно важны topology validation и проверка authoritative network state.

## Desired Outcome

- Пользователь понимает, какие изменения конфликтуют, кто должен принять решение и можно ли безопасно публиковать результат.
- Authoritative state обновляется без silent overwrite и без потери прослеживаемости.
- Work order, evidence, измененные объекты, validation results, reviewer remarks и audit доступны как единый проверяемый контекст.

## Границы Evidence

- Синтетическая репетиция подтверждает внутреннюю связность JTBD для design и demo.
- Частота, длительность и распространенность боли не подтверждены реальными пользователями.
- Внешняя validation откладывается до появления доступа к представителям роли.

## Связи

- [[../entities/personas/authoritative_gis_editing_candidates]]
- [[../entities/personas/utility_gis_editor]]
- [[../chats/2026-06-02-phase-f2-users-and-pain]]
- [[../chats/2026-06-12-utility-gis-editor-synthetic-interview-rehearsal]]
- [[../solution/USM]]
- [[../decisions/followups/index]]
