---
title: Constraints
type: decision
status: draft
created: 2026-06-05
updated: 2026-06-23
source: "Vision_wiki/chats/2026-06-05-phase-f5-business-rollout.md; Vision_wiki/chats/2026-06-06-phase-f6-constraints-and-nfr.md; RAW_inputs/meetings/geometry_association_conflict_f6.md"
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

## Release 2 Geometry/Association Constraints

| Область | Ограничение |
|---|---|
| Demo environment | Только local Docker Compose на reference hardware. |
| MVP boundary | Read-only `conflict package` + consequence explanation + blocker verdict + audit write. |
| Native workflow | Не заменять native conflict editor, replace/reconcile/post actions остаются outside scope или stub/native workflow. |
| Core scenario | Для developer demo достаточно canonical transformer terminal/service-device connectivity case и stale/pre-post failure sidecar. |
| Product acceptance | Один scenario и один sidecar недостаточны для claims о реальном product acceptance. |
| Evidence model | Core evidence должно вычисляться из текущей модели; contextual evidence можно имитировать fixture-данными. |
| Fixture mode | Frozen replay допустим только с явной маркировкой контрольной версии/checksum. |
| Stale handling | Stale/failure sidecar обязательнее красивого happy path. |

## Release 2 Access Constraints

- Protected `Default` - целевой operating mode.
- `Editor` и `Reviewer` могут читать package и сохранять review.
- Actual `post` остается у version administrator / publishing role.
- Audit write append-only: решения и rationale добавляются, но не
  переписывают историю.
- Work order attachments и field evidence требуют scoped access.

## Release 2 Future ADR Candidates

- Собственный topology engine.
- Deep external GIS integration beyond current authoritative source.
- Batch review queue.
- SLA orchestration.
- Object storage strategy для evidence snapshots.
- Production on-prem/security hardening.
- Multi-scenario routing calibration.
- Production-grade specialist workflow.

## Связи

- [[../chats/2026-06-05-phase-f5-business-rollout]]
- [[../chats/2026-06-06-phase-f6-constraints-and-nfr]]
- [[../chats/2026-06-23-geometry-association-conflict-f6]]
- [[../solution/roadmap]]
- [[../solution/nfr]]
- [[risk_assumption_log]]
- [[followups/index]]
