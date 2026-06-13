---
title: Синтетическая Репетиция Интервью Utility GIS Reviewer
type: chat
status: active
created: 2026-06-13
updated: 2026-06-13
source: RAW_inputs/meetings/utility_gis_reviewer_answers.md
tags: [interview, synthetic, reviewer, utility-network, workflow, design-evidence]
---

# Синтетическая Репетиция Интервью Utility GIS Reviewer

## Статус Источника

`RAW_inputs/meetings/utility_gis_reviewer_answers.md` содержит реалистичные
смоделированные ответы от первого лица, а не запись разговора с реальным
проверяющим инженерной GIS-сети.

Источник поддерживает связность reviewer workflow для проектирования, но не
подтверждает фактическое распределение полномочий, распространенность боли,
частоту возвратов или реальные правила utility-организаций.

## Синтетический Review-Кейс

Reviewer проверяет аварийную замену участка кабельной линии 10 кВ, новую муфту,
изменение подключения распределительного шкафа и перевод старого участка в
неактивное состояние.

Первая проверка заканчивается возвратом из-за отсутствующего серийного номера
муфты и подозрительного trace до соседнего шкафа. После исправления reviewer
повторно проверяет весь затронутый участок, а не только исправленные поля.

## Поддержанный Для Проектирования Workflow

1. Получить submitted edit version, work order, список изменений, результаты
   validation/reconcile, документы, фотографии и комментарии редактора.
2. Изучить changed features и сравнить рабочую версию с `Default`.
3. Проверить geometry, attributes, associations, topology, dirty areas, trace и
   conflict history.
4. Сверить изменение с work order, исполнительной схемой, фотографиями и
   сведениями от мастера или диспетчера.
5. Вернуть изменение с конкретными замечаниями при недостаточном evidence или
   подозрительном сетевом результате.
6. После исправления повторно проверить affected area, validation, trace,
   dirty areas, conflicts и состав change set.
7. Зафиксировать решение, что изменение готово или не готово к публикации.
8. Перед `post` повторно проверить актуальность относительно `Default` и
   закрытие review comments.

## Критерии Безопасного Решения

- reconcile актуален, unresolved conflicts отсутствуют;
- topology валидирована, dirty areas закрыты;
- контрольные trace-сценарии дают ожидаемый результат;
- geometry, attributes и associations соответствуют фактическим работам;
- обязательные атрибуты и документы присутствуют;
- старые объекты сохраняют lineage через корректный статус;
- контекст изменения понятен без устного объяснения автора;
- после review change set не изменился.

## Боли И Риски

- Evidence разбросан между GIS, work order, PDF, фотографиями, Excel, чатами и
  историей версии.
- После возврата reviewer заново восстанавливает контекст и повторяет проверку
  всего affected area.
- Карта может выглядеть корректно при ошибочной association и неверном trace.
- Одного trace-сценария недостаточно для изменений connectivity.
- Автоматическая validation отсекает грубые ошибки, но не подтверждает
  инженерный смысл изменения.
- Review без удобного association diff может пропустить логическую ошибку сети.

## Продуктовый Сигнал

Review productivity зависит от единого проверяемого контекста вокруг изменения:

- changed objects и diff до/после;
- geometry, attributes и associations;
- validation, dirty areas и trace;
- conflicts и resolutions;
- work order, документы и фотографии;
- замечания редактора и reviewer;
- audit trail и актуальность относительно `Default`.

## Конфликты С Текущим Design

Синтетический источник предлагает варианты, которые не совпадают с текущим
Release 1 contract:

- reviewer подтверждает готовность, но `post` может выполнять `Version
  administrator` или senior editor;
- работы повышенного риска могут направляться профильному reviewer, а не в
  полностью общую очередь;
- для мелких низкорисковых правок роли иногда совмещаются, тогда как GeoService
  использует строгие взаимоисключающие роли.

Источник не является достаточным основанием менять design. Внешняя проверка
зафиксирована в `FU-2026-06-13-002`.

## Границы Подтверждения

- Это synthetic design evidence, а не external user validation.
- Детали могут воспроизводить уже принятые assumptions GeoService.
- Нужны реальное интервью, обезличенный checklist или наблюдение review-кейса.
- Одного интервью будет недостаточно для вывода о типичности процесса.

## Связи

- [[2026-06-13-utility-gis-reviewer-user-interview-checklist]]
- [[../entities/personas/utility_gis_reviewer]]
- [[../concepts/jtbd]]
- [[../decisions/risk_assumption_log]]
- [[../decisions/release_1_utility_workflow]]
- [[../decisions/followups/index]]
- [[../solution/USM]]
