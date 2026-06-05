---
title: Constraints
type: decision
status: draft
created: 2026-06-05
updated: 2026-06-05
source: "Vision_wiki/chats/2026-06-05-phase-f5-business-rollout.md"
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

## Integration Constraints

| Статус | Интеграции |
|---|---|
| Нужны для demo | `PostGIS seed`, `auth`, `import GeoJSON`. |
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
- [[../solution/roadmap]]
- [[risk_assumption_log]]
- [[followups/index]]
