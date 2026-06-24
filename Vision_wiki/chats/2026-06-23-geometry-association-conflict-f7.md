---
title: Geometry/Association Conflict Ф7 Metrics And Risks
type: chat
status: active
created: 2026-06-23
updated: 2026-06-23
source: RAW_inputs/meetings/geometry_association_conflict_f7.md
tags: [discovery, phase-f7, release-2, geometry-association-conflict, metrics, risks]
---

# Geometry/Association Conflict Ф7 Metrics And Risks

## Контекст Источника

Источник фиксирует Ф7 для Release 2 `geometry/association conflict`: как
проверять consequence-first package в developer demo, какие метрики считать,
какие hard blockers имеют абсолютный veto и какие claims нельзя делать до
реальной validation с `Editor`/`Reviewer`.

Это design/research input, а не direct user interview и не production SLA.

## Главные Тезисы

- Главный сигнал developer demo - `contract readiness pass rate`, но только при
  нулевом `false-safe` на канонических hard-block сценариях.
- North Star Release 2 package: помочь квалифицированному человеку быстро
  принять reviewable go/no-go решение по сетевому конфликту и сохранить, почему
  оно принято, не скрывая hard blockers и не обещая production-safe post без
  свежей проверки.
- `Time-to-decision` и `external-check opens` полезны как secondary demo
  metrics, но не как доказанные product claims до реальных пользователей.
- `false-safe verdict count` является абсолютной counter-metric: один
  false-safe в hard-block case проваливает demo независимо от остальных
  показателей.
- Minimal experiment строится на canonical transformer terminal case: сравнить
  native geometry diff / `Current-Target-Common Ancestor` с consequence package,
  который показывает affected path, association delta, dirty/validation state,
  subnetwork status, trace-sensitive risk statement и safe next step.
- Stale/pre-post sidecar обязателен: package/approval должен становиться stale
  после network-relevant edits, нового `Default` after reconcile, нового
  conflict, invalid subnetwork, dirty areas на affected path или изменения
  validation outcome.

## Метрики Developer Demo

Primary metric:

- `contract readiness pass rate` - доля прогонов canonical scenario и sidecar
  variants, где package корректно построен, blockers найдены, stale помечен, а
  audit object пригоден для repeat review.

Secondary metrics:

- `package build success`;
- `evidence completeness`;
- `blocker detection`;
- `stale detection`;
- `audit completeness`;
- `time-to-decision` и `external-check opens` как внутренние demo indicators.

Counter-metrics:

- `false-safe verdict count`;
- `false-block rate`;
- `duplicate-view rate`;
- `time added by package`;
- `unclear next step rate`.

## Absolute Veto Blockers

- unresolved association delta;
- dirty trace path или validate consistency failure;
- invalid subnetwork или failed update subnetwork;
- stale approval/package;
- missing required evidence для risk tier и claimed network consequence.

Полезный `blocked post` должен иметь воспроизводимую причину из authoritative
state и сниматься после исправления конкретного состояния. Если native state
clean, conflict больше нет, subnetwork valid и evidence не менялось, блокировка
считается false-block.

## Эксперимент И Run Data

До реальных интервью достаточно developer-confidence threshold:

- один scripted golden walkthrough;
- не меньше 10 детерминированных повторов canonical scenario;
- не меньше 10 мутированных прогонов stale / blocker / pre-post failure
  variants;
- до 30 общих automated runs, если нужно оценить стабильность package build и
  blocker detection.

Для каждого run сохраняются `seed/checksum`, `scenario_id`, `package_id`,
`version_id`, version timestamps/properties, risk tier, blockers, dirty-area
status, subnetwork status, trace/subnetwork freshness, decision, chosen next
step, audit object, time-to-decision и manual/external checks.

Manual baseline для Release 2 нужен отдельно: сравнивать нужно с `ArcGIS native
Conflicts view + reconcile/post + локальный SOP + экспертный handoff`, а не
только с Release 1.

## Риски И Course Change

Самые рискованные гипотезы:

- computed evidence realism;
- risk tier calibration;
- stale detection completeness;
- role trust;
- field evidence scope;
- performance/friction package build.

Курс нужно менять, если package не объясняет consequence за 1-2 минуты scripted
review, участник сразу уходит во внешний GIS или экспертный handoff, hard
blockers не воспроизводятся из authoritative state, audit object не помогает
repeat review после stale или хотя бы один canonical hard-block case дает
false-safe.

## Follow-up'ы

- Подготовить measurement harness для Release 2 developer demo: canonical
  scenario, sidecar variants, run schema и pass/fail criteria.
- После developer demo вынести на реальную validation вопросы о понятности risk
  tier, достаточности evidence, доверии к blocker verdict, приемлемости sample
  review для `Normal`, нужности specialist escalation и пригодности audit для
  repeat review.

## Связи

- [[2026-06-23-geometry-association-conflict-f7-checklist]]
- [[2026-06-23-geometry-association-conflict-f6]]
- [[../concepts/metrics]]
- [[../decisions/risk_assumption_log]]
- [[../decisions/release_2_conflict_explanation]]
- [[../decisions/followups/index]]
- [[../solution/roadmap]]
