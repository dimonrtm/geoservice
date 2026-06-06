---
title: Constraints
type: decision
status: draft
created: 2026-06-05
updated: 2026-06-06
source: "Vision_wiki/chats/2026-06-05-phase-f5-business-rollout.md; Vision_wiki/chats/2026-06-06-phase-f6-constraints-and-nfr.md"
tags: [constraints, rollout, demo, discovery]
---

# Constraints

Рабочие ограничения GeoService после Ф5. Они фиксируют границы demo и не являются production requirements.

## Rollout Constraints

| Область | Ограничение |
|---|---|
| Decision maker | Первый принимающий решение - владелец pet-проекта. |
| Rollout format | Локальное demo. |
| Primary audience | Разработчик. |
| Runtime | Local Docker Compose. |
| Data | Только synthetic dataset, без реальных utility data. |
| Demo value | `learning value` и демонстрация более простого pipeline. |
| Primary flow | Сначала показать `Editor flow`. |
| Roles | В первом demo нужны `Editor` и `Reviewer`. |
| Required setup | README, seed/reset script, demo сценарий, troubleshooting. |

## Ф6 Runtime Constraints

| Область | Ограничение |
|---|---|
| Deadline | Жесткой даты готовности нет. |
| Technology choice | Технологии обсуждаемы; текущий стек не является безусловно фиксированным. |
| Reference hardware | Asus TUF Gaming 2022, AMD Ryzen 7 5000 series, 16 GB RAM. |
| Browser | Chrome на первом этапе. |
| Startup | Несколько минут. |
| Restart | Сохраняет текущее demo state. |
| Reset | За несколько минут восстанавливает seed и сохраняет audit. |
| Full clean | Отдельно удаляет demo data и audit. |
| Realtime | WebSocket delivery за 1-2 секунды. |
| Auth | JWT Bearer token. |
| Separation of duties | `Editor` и `Reviewer` не совмещаются одним пользователем. |
| Observability | Healthcheck, container logs, correlation ID, понятные UI errors. |
| SLA/backup | Не требуются для local demo. |

## Integration Constraints

| Статус | Интеграции |
|---|---|
| Нужны для demo | `PostGIS seed`, JWT `auth`, `import GeoJSON`. |
| Не нужны для demo | External GIS, `ArcGIS`/`QGIS` export, CI demo data reset. |

## Promise Boundaries

Не обещать в текущем demo:

- замену `ArcGIS Enterprise + Utility Network`;
- production-grade branch versioning;
- полноценный topology engine или trace engine;
- hosted/SaaS rollout;
- enterprise ACL/compliance/audit guarantees;
- offline sync, CRDT/OT или multi-site collaboration;
- интеграции с external GIS;
- доказанный commercial ROI.

## Связи

- [[../chats/2026-06-05-phase-f5-business-rollout]]
- [[../chats/2026-06-06-phase-f6-constraints-and-nfr]]
- [[../solution/roadmap]]
- [[../solution/nfr]]
- [[risk_assumption_log]]
- [[followups/index]]
