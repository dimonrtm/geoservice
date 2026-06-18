---
title: JTBD GeoService
type: concept
status: active
created: 2026-06-02
updated: 2026-06-18
source: "user answers to /discover --phase Ф2, 2026-06-02; RAW_inputs/documents/Ф2.md; RAW_inputs/meetings/utility_gis_editor_answers.md; RAW_inputs/meetings/utility_gis_reviewer_answers.md; RAW_inputs/meetings/utility_gis_editor_broad_domain_answers.md; RAW_inputs/meetings/utility_gis_reviewer_broad_domain_answers.md; RAW_inputs/meetings/geometry_association_conflict_f2.md"
tags: [jtbd, discovery, phase-f2, authoritative-editing, reviewer, research, synthetic-evidence]
---

# JTBD GeoService

## Статус

Primary JTBD `Utility GIS editor` и связанный reviewer JTBD приняты как
активный design-contract на основе research и синтетических репетиций
интервью. Они не подтверждены наблюдением реального рабочего процесса.
Кадастровый сценарий сохранен как deferred.

## Job Statements

| Когда | Пользователь Хочет | Чтобы |
|---|---|---|
| `Utility GIS editor` вносит изменение по work order при неполных полевых данных и параллельной работе других редакторов | Собрать контекст изменения, изолировать правки, проверить connectivity/trace, разобрать conflicts и контролируемо опубликовать результат | Не допустить неверного состояния сети, сохранить lineage и сделать решение проверяемым для reviewer и следующего редактора |
| `Utility GIS editor` после edit/validate/reconcile сталкивается с `geometry/association conflict` | Понять, меняет ли conflict только representation или authoritative network behavior, и выбрать безопасный route решения | Не выполнить unsafe post, не переэскалировать простой случай и сохранить доказуемую логику решения |
| `Utility GIS reviewer` получает подготовленное изменение инженерной сети | Увидеть единый evidence context, проверить diff, associations, validation, trace, conflicts и документы, затем объяснимо принять или вернуть change set | Не пропустить скрытую ошибку сети и разрешить публикацию только для актуального, доказанного и неизмененного результата |
| Кадастровый инженер выполняет split/merge участков параллельно с другими делами | Сохранить lineage, разобрать конфликт и опубликовать согласованное кадастровое изменение | Не допустить юридически значимой ошибки границ и сохранить прослеживаемую историю; deferred research-сценарий |

## Текущий Обходной Путь

- Для utility-сценария текущий обходной путь включает отдельную версию, reconcile/post, review перед публикацией и ручной разбор конфликтов.
- Контекст собирается вручную из GIS, work order, PDF, фотографий, Excel, справочников и сообщений.
- При возврате на исправление редактор повторяет validation, trace и reconcile и заново поднимает исходные материалы.
- Reviewer вручную сопоставляет GIS diff с work order, PDF, фотографиями,
  сообщениями и сведениями специалистов.
- Editor и reviewer вручную реконструируют связь field/as-built evidence с
  physical и logical network state.
- Для `geometry/association conflict` editor вручную соединяет
  Differences/Conflicts view, association tools, validation/dirty areas,
  trace before/after, subnetwork checks, work order, field evidence,
  screenshots, notes и устные подтверждения.
- После исправления reviewer повторно проверяет affected area, потому что
  change set или connectivity могли измениться шире замечания.
- Для кадастра дополнительно важна дисциплина "одна версия - одно кадастровое дело".
- Для инженерной сети дополнительно важны topology validation и проверка authoritative network state.

## Desired Outcome

- Пользователь понимает, какие изменения конфликтуют, кто должен принять решение и можно ли безопасно публиковать результат.
- Authoritative state обновляется без silent overwrite и без потери прослеживаемости.
- Work order, evidence, измененные объекты, validation results, reviewer remarks и audit доступны как единый проверяемый контекст.
- Причина approve/reject связана с конкретным evidence и относится только к
  актуальному неизмененному change set.
- Для conflict resolution пользователь видит consequence package:
  association/terminal diff, validation state, dirty-area scope, trace impact,
  subnetwork status, field evidence и suggested route.

## Границы Evidence

- Синтетические репетиции editor и reviewer подтверждают внутреннюю связность
  JTBD для design и demo.
- Частота, длительность и распространенность боли не подтверждены реальными пользователями.
- Распределение reviewer/post полномочий, routing очереди и допустимость
  совмещения ролей требуют внешней validation.

## Связи

- [[../entities/personas/authoritative_gis_editing_candidates]]
- [[../entities/personas/utility_gis_editor]]
- [[../entities/personas/utility_gis_reviewer]]
- [[../chats/2026-06-02-phase-f2-users-and-pain]]
- [[../chats/2026-06-12-utility-gis-editor-synthetic-interview-rehearsal]]
- [[../chats/2026-06-13-utility-gis-reviewer-synthetic-interview-rehearsal]]
- [[../chats/2026-06-13-utility-gis-editor-broad-domain-rehearsal]]
- [[../chats/2026-06-13-utility-gis-reviewer-broad-domain-rehearsal]]
- [[../chats/2026-06-18-geometry-association-conflict-f2]]
- [[../solution/USM]]
- [[../decisions/followups/index]]
