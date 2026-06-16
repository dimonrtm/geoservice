---
title: Reviewer Decision Для Release 2
type: session
status: active
created: 2026-06-16
updated: 2026-06-16
source: RAW_inputs/meetings/Reviwer Decision.md
tags: [discovery, release-2, reviewer, conflict-explanation, utility-network]
---

# Reviewer Decision Для Release 2

## Контекст

Источник уточняет recommended policy для Release 2 в сценарии `Utility GIS editor`.
Это design/architecture input с опорой на utility authoritative editing,
branch versioning, reconcile/post и Utility Network semantics. Источник не
является direct user interview и не подтверждает распространенность процесса у
реальных `Editor`/`Reviewer`.

## Ключевые Решения

- `Reviewer decision` для Release 2 трактуется как approval of change package
  for post readiness, а не как одиночное решение по conflict resolution.
- `Approve package` и `ready/post authorized` разделяются: approval подтверждает
  содержательную корректность пакета, а `post` остается отдельным техническим
  gate против текущего `Default`.
- `Reviewer` получает пакет после `Editor proposal`, reconcile against current
  `Default` и pre-review gate: validation/topology, trace или subnetwork impact
  и Differences view.
- `Normal` допускает audit + sample review без индивидуального reviewer
  approval только для низкорисковых случаев без network impact.
- `High` требует финального решения `Reviewer` по содержанию пакета.
- `Critical` требует dual control: `Reviewer` + профильный специалист или
  utility-network admin; финальное право publication в `Default` принадлежит
  владельцу authoritative state / version administrator equivalent.
- Trace change не становится `Critical` автоматически. `Critical` возникает,
  если trace delta меняет authoritative network behavior: affected service,
  subnetwork, controllers, safety isolation, traversability/barriers,
  rule-dependent connectivity или operational outputs.
- Stale approval возникает после изменений geometry, associations, network
  attributes, terminal/path configuration, `Default`, validation/dirty/error
  status или subnetwork status.
- Repeat review должен быть delta-first with anchored baseline: сначала delta
  после последнего approval, но с доступом к полной previously approved package
  baseline.

## Post Blockers

`post` должен блокироваться при:

- невыполненном reconcile или изменении `Default` после reconcile;
- unreviewed conflicts;
- dirty areas в зоне предполагаемого сетевого эффекта;
- error dirty areas, network errors или invalid topology state;
- dirty/invalid subnetwork в affected contour;
- unresolved association diff с влиянием на connectivity, containment или
  structural attachment;
- unexpected trace impact без согласованного rationale;
- missing evidence для field facts, safety-related changes или service-impacting
  corrections.

## Acceptance Examples

- Безопасный `High`: ограниченный geometry/attribute diff, clean validation,
  trace без subnetwork/controller impact; `Reviewer` принимает финальное
  package approval, а `post` возможен только если `Default` не изменился.
- `Critical`: association или terminal/path change меняет upstream/downstream
  behavior или dirty/invalid subnetwork; без dual approval и clean subnetwork
  state `post` невозможен.
- Stale approval: после approval изменился `Default` или пакет; approval
  помечается stale, показывается delta-since-approval и обновленный package
  summary, `post` заблокирован до repeat review.

## Следствия Для Wiki

- [[../decisions/release_2_conflict_explanation]] уточняет `Reviewer decision`
  как package approval и разделяет approval/post authorization.
- [[../decisions/conflict_resolution_routing]] уточняет границу `High/Critical`
  для trace change.
- [[../decisions/conflicts/2026-06-14-trace-risk-tier-boundary]] закрывается
  как resolved for planned Release 2 policy.
- [[../entities/personas/utility_gis_reviewer]] получает refined role boundary:
  `Reviewer` не является скрытым editor и не обязательно выполняет `post`.

## Follow-up

- Проверить модель с реальными `Editor` и `Reviewer`, потому что источник
  остается design/architecture input.
- Перед implementation contract превратить policy в конкретную state machine,
  API/events и audit schema.
