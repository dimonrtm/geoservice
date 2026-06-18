---
title: Utility GIS Reviewer
type: entity
status: active
created: 2026-06-13
updated: 2026-06-18
source: "RAW_inputs/meetings/utility_gis_reviewer_answers.md; RAW_inputs/meetings/utility_gis_reviewer_broad_domain_answers.md; RAW_inputs/meetings/Reviwer Decision.md; RAW_inputs/meetings/geometry_association_conflict_f2.md"
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
- Для Release 2 принимает reviewer decision как approval of change package for
  post readiness; это не обязательно означает, что сам `Reviewer` выполняет
  технический `post` в `Default`.
- В `geometry/association conflict` является вторичным пользователем:
  подключается для competing representations, association/attribute logic,
  `High` risk или package approval, но не является первичным носителем боли.

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
7. После исправления или stale approval повторно проверить delta-since-approval
   с доступом к полной previously approved package baseline.
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
- для `High` reviewer принимает финальное решение по содержанию package;
- для `Critical` reviewer участвует в dual control вместе с профильным
  специалистом или utility-network admin;
- `post authorization` отделен от reviewer package approval и требует
  актуального reconcile/technical gate.

## Боли-Гипотезы

- Evidence приходится собирать из GIS, work order, PDF, фото, Excel, чатов и
  истории версии.
- После возврата приходится заново поднимать контекст и перепроверять весь
  affected area.
- Geometry и attributes видны лучше, чем association changes до/после.
- Автоматические проверки не доказывают инженерный смысл изменения.
- Для reviewer escalation требуется уже собранный context package:
  association/terminal diff, validation/dirty areas, trace before/after,
  subnetwork status и field evidence.
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

- является ли review queue общей или маршрутизируется по специализации;
- допустимо ли совмещение ролей для низкорисковых изменений;
- обязателен ли комментарий при любом approve;
- какие проверки и документы являются формальным регламентом.

`RAW_inputs/meetings/Reviwer Decision.md` рекомендует разделить reviewer package
approval и technical `post authorization`: `Reviewer` подтверждает содержательную
готовность пакета, а право публикации в `Default` остается отдельным gate у
уполномоченной роли / владельца authoritative state. Это accepted-for-design,
но не direct user evidence.

Эти вопросы отслеживаются в `FU-2026-06-13-002`.

## Связи

- [[../../chats/2026-06-13-utility-gis-reviewer-user-interview-checklist]]
- [[../../chats/2026-06-13-utility-gis-reviewer-synthetic-interview-rehearsal]]
- [[../../chats/2026-06-13-utility-gis-reviewer-broad-domain-rehearsal]]
- [[../../chats/2026-06-16-release-2-reviewer-decision]]
- [[../../chats/2026-06-18-geometry-association-conflict-f2]]
- [[../../concepts/jtbd]]
- [[../../decisions/risk_assumption_log]]
- [[../../decisions/release_1_utility_workflow]]
- [[../../decisions/followups/index]]
- [[../../solution/USM]]
