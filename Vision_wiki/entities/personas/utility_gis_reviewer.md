---
title: Utility GIS Reviewer
type: entity
status: active
created: 2026-06-13
updated: 2026-06-13
source: "RAW_inputs/meetings/utility_gis_reviewer_answers.md; RAW_inputs/meetings/utility_gis_reviewer_broad_domain_answers.md"
tags: [persona, reviewer, utility-network, authoritative-editing, synthetic-evidence]
---

# Utility GIS Reviewer

## Статус

Design-персона GeoService, поддержанная синтетической репетицией интервью.
Роль и workflow не подтверждены разговором или наблюдением реального
проверяющего инженерной GIS-сети.

## Роль

- Независимо проверяет изменение инженерной сети перед публикацией в
  authoritative state.
- Оценивает не только техническую валидность GIS-данных, но и соответствие
  фактическим полевым работам и эксплуатационному смыслу.
- При недостаточном evidence возвращает изменение редактору с конкретными
  замечаниями.
- Подтверждает готовность change set к публикации.
- Выступает контрольным слоем между field reality, engineering documents,
  physical/logical network model и operational systems.

## Рабочая Задача

Получить подготовленную edit version и определить, можно ли безопасно
опубликовать изменение сети без ошибочной connectivity, потери lineage,
неразрешенного конфликта или недоказанного инженерного решения.

## Рабочий Процесс

1. Открыть review context: work order, автор, affected area и change summary.
2. Сравнить changed features и associations с `Default`.
3. Отдельно проверить geometry, attributes и logical connectivity.
4. Проверить validation, topology, dirty areas, набор контрольных trace и
   conflict resolutions.
5. Сверить изменение с документами, фотографиями и сведениями ответственных
   специалистов.
6. Принять изменение, вернуть его с объяснимыми замечаниями или передать
   профильному специалисту.
7. После исправления повторно проверить весь affected area и актуальность
   change set.
8. Зафиксировать решение и evidence для audit.

## Критерии Решения

- unresolved conflicts отсутствуют;
- topology и dirty areas находятся в допустимом состоянии;
- контрольные trace-сценарии подтверждают ожидаемую connectivity;
- geometry, attributes и associations соответствуют work order и evidence;
- обязательные атрибуты заполнены;
- изменение сохраняет lineage старых объектов;
- контекст понятен следующему специалисту без устного объяснения автора;
- approval относится к неизмененному и актуальному change set.

## Боли-Гипотезы

- Evidence приходится собирать из GIS, work order, PDF, фото, Excel, чатов и
  истории версии.
- После возврата приходится заново поднимать контекст и перепроверять весь
  affected area.
- Geometry и attributes видны лучше, чем association changes до/после.
- Автоматические проверки не доказывают инженерный смысл изменения.
- Один trace может не обнаружить проблему соседнего участка сети.
- Универсальный reviewer может не увидеть domain-specific эксплуатационный
  риск.
- Review package приходится вручную собирать из нескольких систем.

## Desired Outcome

- Reviewer видит в одном контексте diff, associations, validation, trace,
  conflicts, документы, замечания и audit.
- Причина принятия или возврата понятна editor и следующему проверяющему.
- Публикация разрешена только для актуального неизмененного change set.
- Authoritative state не получает скрытую connectivity или association error.

## Открытые Границы Роли

Синтетический источник не подтверждает:

- выполняет ли reviewer `post` самостоятельно;
- является ли review queue общей или маршрутизируется по специализации;
- допустимо ли совмещение ролей для низкорисковых изменений;
- обязателен ли комментарий при любом approve;
- какие проверки и документы являются формальным регламентом.

Эти вопросы отслеживаются в `FU-2026-06-13-002`.

## Связи

- [[../../chats/2026-06-13-utility-gis-reviewer-user-interview-checklist]]
- [[../../chats/2026-06-13-utility-gis-reviewer-synthetic-interview-rehearsal]]
- [[../../chats/2026-06-13-utility-gis-reviewer-broad-domain-rehearsal]]
- [[../../concepts/jtbd]]
- [[../../decisions/risk_assumption_log]]
- [[../../decisions/release_1_utility_workflow]]
- [[../../decisions/followups/index]]
- [[../../solution/USM]]
