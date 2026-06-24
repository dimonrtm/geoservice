---
title: Geometry/Association Conflict Ф8 Closeout
type: chat
status: active
created: 2026-06-23
updated: 2026-06-23
source: RAW_inputs/meetings/geometry_association_conflict_f8.md
tags: [discovery, phase-f8, release-2, geometry-association-conflict, closeout]
---

# Geometry/Association Conflict Ф8 Closeout

## Контекст Источника

Источник закрывает discovery Ф1-Ф8 для Release 2 `geometry/association
conflict` и фиксирует, что можно переносить в implementation contract, а что
остается design-гипотезой до реальных `Editor`/`Reviewer`.

Это design/research input и closeout-резюме, а не direct user interview, не
production SLA и не готовая техническая спецификация.

## Главные Тезисы

- Release 2 нужно фиксировать как decision-support и control layer вокруг
  `reconcile -> consequence package -> review -> post`, а не как новый движок
  conflict resolution.
- Центральное решение Release 2: `approval of change package as a pre-post
  gate`. `Editor` разрешает конфликт в native edit workflow, а GeoService
  собирает consequence package и помогает принять human decision, можно ли
  допускать пакет дальше.
- `Reviewer` получает package после reconcile и после сборки evidence на
  снимке, где известны `Base / Mine / Default`, association delta,
  dirty/validation state и trace/subnetwork freshness.
- `approve package` и `can post` должны быть разными состояниями: approval
  подтверждает смысловое решение, а `can post` требует актуального target/default
  state, отсутствия hard blockers и non-stale approval.
- Implementation contract v0.1 должен заморозить states, package schema,
  blocker semantics, stale triggers, minimal audit object и non-goals.
- Human layer остается гипотезой: точная risk calibration,
  High/Critical authority matrix, sample review для `Normal`, evidence
  sufficiency thresholds, repeat-review UX и language of trust.

## Ready For Implementation Contract

К implementation contract готовы:

- scope Release 2 как pre-post decision-support layer;
- handoff после reconcile и package build;
- minimal package schema: `Base / Mine / Default`, geometry diff, association
  delta, dirty areas, validation/topology status, trace consistency/freshness,
  subnetwork status при затронутой subnetwork semantics, work order/change
  request id, explanatory comments/history и field evidence для High/Critical
  или неочевидного rationale;
- разделение `approve package` и `can post`;
- absolute veto blockers: unresolved association delta, dirty trace path или
  отсутствующая validated topology, invalid subnetwork/update-subnetwork
  failure, stale approval, missing mandatory evidence для High/Critical,
  unexplained unexpected trace impact;
- stale triggers: geometry, association, network attributes, terminal
  configuration, validation result, reconcile against changed target/default и
  subnetwork status changes;
- minimal audit object: package id, snapshot/version ids, risk tier, blockers,
  evidence completeness flags, trace/subnetwork freshness, decision, actor
  role, timestamps, stale events, final post outcome и ссылка на
  reconcile/technical log;
- canonical transformer/service-device association case plus stale/pre-post
  failure sidecar.

## Hypotheses Until Real Validation

До real `Editor`/`Reviewer` validation остаются гипотезами:

- точная calibration `Normal / High / Critical`;
- authority matrix для High/Critical;
- sample review policy для `Normal`;
- field evidence sufficiency thresholds;
- UX repeat review и `delta since previous approval`;
- language of trust: какие формулировки действительно понятны и не создают
  false-safe confidence.

## Contract Blockers And Deferrable Questions

Implementation contract реально блокируют:

- владелец финального решения для `Critical`;
- evidence matrix по tier;
- exact events, переводящие approval/package в `stale`;
- MVP boundary между read-only decision support и action buttons;
- гарантированно доступные demo/runtime integrations для work order,
  trace/subnetwork data и evidence.

Можно не блокировать первый контракт:

- sample review policy для `Normal`;
- specialist escalation UX;
- SLA queue;
- batch review;
- broader enterprise rollout и production hardening.

## Следующие Артефакты

После Ф8 нужны:

- implementation contract v0.1 как ADR-style Markdown contract с
  machine-readable YAML/JSON appendices;
- fixture/checksum и canonical scenario dataset;
- Base-Mine-Default snapshot ids;
- computed geometry diff и association delta;
- dirty area snapshot, validation result, trace result with consistency flag,
  subnetwork status snapshot;
- blocker list, risk-tier output, decision outcome, stale event log, audit
  object JSON;
- timing metrics по package build, evidence load, stale invalidation и audit
  save;
- отдельный real validation checklist для `Editor`/`Reviewer`.

## Acceptance Gates

- `contract gate`: frozen state machine, package schema, blocker semantics и
  stale triggers.
- `safety gate`: canonical scenario и stale/pre-post sidecar воспроизводимо
  показывают hard blockers; false-safe является абсолютным veto.
- `observability gate`: каждый run сохраняет package id, input checksum,
  blockers, freshness snapshots, decision и audit object.
- `validation gate`: claims сильнее `helps explain/detect/block` запрещены до
  real Editor/Reviewer sessions.

## Допустимый Claim

Допустимый developer-demo claim:

`В developer demo Release 2 собирает consequence package для utility-network
конфликта, делает видимыми hard blockers и помогает сформировать более
обоснованное go/no-go решение перед post на synthetic scenario.`

Недопустимые claims до validation: `Release 2 обеспечивает safe post`, `снижает
ошибки в production`, `заменяет reviewer`, `доказывает корректность
authoritative state`.

## Non-Goals

- новый topology engine;
- full ArcGIS parity;
- full in-product conflict editing UI;
- batch review queue и SLA routing;
- production-grade on-prem hardening;
- authoritative-safe post claims без real validation.

## Follow-up'ы

- Подготовить implementation contract v0.1.
- Подготовить отдельный real validation checklist для `Editor`/`Reviewer`.
- Разнести ADR candidates: `Decision ownership and escalation matrix` и
  `Freshness and re-review semantics`.

## Связи

- [[2026-06-23-geometry-association-conflict-f8-checklist]]
- [[2026-06-23-geometry-association-conflict-f7]]
- [[2026-06-23-geometry-association-conflict-f6]]
- [[../decisions/release_2_conflict_explanation]]
- [[../concepts/metrics]]
- [[../decisions/risk_assumption_log]]
- [[../solution/roadmap]]
- [[../decisions/followups/index]]
