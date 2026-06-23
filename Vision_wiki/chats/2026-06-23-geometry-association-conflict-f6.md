---
title: Geometry/Association Conflict Ограничения И NFR
type: session
status: active
created: 2026-06-23
updated: 2026-06-23
source: RAW_inputs/meetings/geometry_association_conflict_f6.md
tags: [discovery, phase-f6, release-2, geometry-association-conflict, nfr, implementation-contract]
---

# Geometry/Association Conflict Ограничения И NFR

## Контекст

`RAW_inputs/meetings/geometry_association_conflict_f6.md` - research/design
input по Ф6 для Release 2 `geometry/association conflict`. Источник формулирует
implementation contract для consequence-first decision support поверх native
versioned utility editing workflow. Это не direct user interview, не production
SLA и не требование заменить native conflict editor.

Ф6 уточняет, что первое demo должно доказывать не красивый diff, а безопасность
решения перед `post` в условиях versioning, topology, associations, trace и
subnetwork semantics.

## Главные Тезисы

- Первый `conflict package` должен быть read-only слоем: Base/Mine/Default,
  geometry diff, association delta, dirty areas, validation/network errors,
  trace evidence и conditional subnetwork status.
- Work order, field evidence, photos, reviewer comments и narrative rationale
  полезны как contextual evidence, но не являются core evidence безопасности
  сетевого последствия.
- Core evidence должно вычисляться из текущей модели. Fixture/reference evidence
  допустимо только как явно маркированный frozen replay с checksum/контрольной
  версией.
- Для developer demo достаточно одного canonical transformer terminal/service
  device connectivity case и одного stale/pre-post failure sidecar. Для
  product acceptance этого недостаточно.
- MVP boundary: `read-only package + consequence explanation + blocker verdict
  + audit write`. Реальные replace/reconcile/post actions остаются вне первого
  Release 2 demo или за stub/native workflow.
- State machine должна включать `draft package`, `ready for review`,
  `approved`, `stale`, `blocked post`, `escalated`, `repeated review`.
- Package/approval становится stale после topology-relevant изменений named
  version, нового reconcile, изменения `Default`, validate after reconcile,
  update subnetwork или изменения risk-relevant evidence.
- Hard blockers включают unresolved conflicts, post-time re-reconcile need,
  error dirty areas/network errors, dirty areas на claimed trace path,
  dirty/invalid affected subnetwork и unresolved association delta.

## Implementation Contract

Минимальный внешний API первого demo:

- `GET package summary`;
- `GET package details`;
- `POST recompute package`;
- `POST reviewer decision`;
- `GET audit record`;
- `GET package status` или push-канал для stale/blocker/job updates;
- optional `POST pre-post check`, если demo показывает pre-post gate.

Внутренними service calls остаются adapters к version management, conflict
representations, association extractor, dirty area/validation reader, trace
executor, subnetwork-status reader, risk-tier classifier, stale detector, audit
writer и demo-fixture resolver.

## P95 Targets

Источник предлагает draft targets для малого developer demo:

| Операция | P95 |
|---|---:|
| Открытие готового package summary | <= 2 сек |
| Открытие evidence details | <= 2.5 сек |
| Stale/block status из уже рассчитанных сигналов | <= 1 сек |
| Audit save ACK | <= 1 сек |
| Audit readable in UI | <= 3 сек |

Trace, validate и update-subnetwork-sensitive evidence должны уходить в async
job с progress/freshness state, а не обещать синхронный sub-second result.

## Observability

Минимальные сигналы для debugging и доверия к package:

- `package_build_duration_ms`;
- `diff_extraction_ms`;
- `association_read_ms`;
- `dirty_area_fetch_ms`;
- `trace_job_ms`;
- `subnetwork_status_fetch_ms`;
- `audit_save_ms`;
- `stale_detection_ms`;
- `trace_consistency_failures`;
- `subnetwork_invalid_count`;
- `hard_blocker_count`;
- `package_recomputed_count`;
- `approval_staled_count`;
- source-of-truth moments: `version_modified`, `version_reconciled`,
  `common_ancestor`, `subnetwork_last_update`, `package_computed_at`.

## Security И Access

- Protected `Default` остается целевым operating mode.
- `Editor` и `Reviewer` могут читать package и сохранять review, но actual
  `post` должен оставаться у version administrator / publishing role.
- Audit write должен быть append-only: решения и rationale добавляются, но не
  переписывают историю.
- Field evidence и work order attachments требуют scoped access, потому что
  operational evidence может иметь отдельные права.

## Future ADR Candidates

В future scope вынесены:

- собственный topology engine;
- deep external GIS integration beyond current authoritative source;
- batch review queue;
- SLA orchestration;
- object storage strategy для evidence snapshots;
- production on-prem/security hardening;
- multi-scenario routing calibration;
- production-grade specialist workflow.

## Caveats

Ф6 усиливает implementation-contract boundary, но не доказывает внешнюю
product validation. До проверки с реальными `Editor`/`Reviewer` нельзя
утверждать, что package снижает review friction, предотвращает unsafe post или
заменяет открытие внешней GIS.

## Связи

- [[2026-06-23-geometry-association-conflict-f6-checklist]]
- [[2026-06-22-geometry-association-conflict-f5]]
- [[2026-06-20-geometry-association-conflict-f4]]
- [[../decisions/release_2_conflict_explanation]]
- [[../decisions/conflict_resolution_routing]]
- [[../solution/nfr]]
- [[../decisions/constraints]]
- [[../solution/architecture_vision]]
- [[../decisions/risk_assumption_log]]
- [[../decisions/followups/index]]
