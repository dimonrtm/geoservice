---
title: Ф6 Ограничения И NFR
type: session
status: draft
created: 2026-06-06
updated: 2026-06-06
source: "user answers to /discover --phase Ф6, 2026-06-06"
tags: [discovery, phase-f6, constraints, nfr, demo]
---

# Ф6 Ограничения И NFR

## Контекст

Ф6 уточняет измеримые эксплуатационные рамки local Docker Compose demo после Ф5. Требования относятся к developer demo на synthetic dataset и не являются production SLA или enterprise compliance guarantees.

## Ответы Ф6

| Область | Решение |
|---|---|
| Обязательный срок | Жесткой даты готовности нет. |
| Технологии | Технологический стек обсуждаем; текущие технологии не являются безусловно фиксированными. |
| Reference hardware | Ноутбук Asus TUF Gaming 2022 года, AMD Ryzen 7 5000 series, 16 GB RAM. |
| Browser | На первом этапе Chrome; расширение browser support возможно позже. |
| Startup time | Первый запуск Docker Compose должен укладываться в несколько минут. |
| Повторный запуск | Обычный повторный запуск сохраняет данные; явный reset восстанавливает исходный seed. |
| Reset time | Reset должен завершаться за несколько минут. |
| Dataset и concurrency | `synthetic_utility_feeder_01`: 1 AOI, 1 feeder, 7 junctions, 6 line segments, 6 devices, 8-10 associations, 2 work orders, 3 users, `Default` + 2 edit versions, 4 conflict-сценария. |
| Latency | Новые точные цели для map load, save, validation, reconcile и post не заданы. |
| Realtime | WebSocket updates должны доходить до других клиентов за 1-2 секунды. |
| Auth | JWT Bearer token. |
| Roles | `Editor` и `Reviewer`; совмещение ролей одним пользователем запрещено. |
| Observability | Нужны healthcheck, container logs, correlation ID и понятные UI errors. |
| Backup/SLA | Для local demo backup/restore и SLA не требуются. |
| GeoJSON import | Входит в первый walking skeleton. |

## Audit И Reset

Принят двухрежимный подход:

- обычный reset восстанавливает synthetic seed и сохраняет `audit_log`;
- отдельный `full-clean` удаляет demo data и audit;
- audit должен переживать restart и обычный reset;
- в audit фиксируются actor, role, action, timestamp, target entity, work order/version, before/after summary и result.

Минимальные audit events:

- login success/failure;
- создание edit version;
- изменение feature или association;
- validation start/result;
- reconcile start/result;
- conflict resolution;
- submit for review;
- reviewer approve/reject;
- post в `Default`;
- обычный reset и `full-clean`.

## Неопределенные Performance Targets

Для map load, save, validation, reconcile и post отдельные числовые latency-цели пока не вводятся. Их нужно измерить на reference hardware после появления end-to-end walking skeleton и только затем решить, нужны ли дополнительные NFR.

## Связи

- [[../solution/nfr]]
- [[../decisions/constraints]]
- [[../solution/architecture_vision]]
- [[../decisions/risk_assumption_log]]
- [[../decisions/followups/index]]
- [[2026-06-05-phase-f5-business-rollout]]
