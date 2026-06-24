---
title: Geometry/Association Conflict Метрики И Риски Checklist
type: chat
status: planned
created: 2026-06-23
updated: 2026-06-23
source: "user request to /discover --context geometry/association conflict --phase Ф7, 2026-06-23"
tags: [discovery, phase-f7, release-2, geometry-association-conflict, metrics, risks]
---

# Geometry/Association Conflict Метрики И Риски Checklist

## Цель Ф7

Подготовить встречу/рабочий проход по метрикам, рискам и проверке Release 2
`geometry/association conflict` после Ф4-Ф6.

Ф7 должна определить, как developer demo докажет или опровергнет ценность
consequence-first `conflict package`: сокращает ли он путь к уверенному
safe/unsafe решению, не создает ли false-safe verdict и какие гипотезы нужно
проверять до расширения scope.

## Контекст Встречи

- Контекст: Release 2 `geometry/association conflict`.
- Фаза: Ф7, метрики, риски и проверка.
- Предполагаемый участник: `разработчик demo`.
- Длительность по умолчанию: 45-60 минут.
- Нужное знание: какие metrics, guardrails и experiments нужны перед
  implementation contract и после первого developer demo.
- Материалы: Ф4-Ф6 ноды `geometry/association conflict`,
  [[../decisions/release_2_conflict_explanation]],
  [[../concepts/metrics]], [[../decisions/risk_assumption_log]],
  [[../decisions/followups/index]], [[../solution/roadmap]].

## Must-Вопросы

1. Какой главный сигнал успеха для developer demo: fewer external checks,
   time-to-confident-decision, false-safe prevention, audit quality или
   readiness to implement contract?
2. Как сформулировать North Star для Release 2 package, чтобы она не обещала
   production-safe post до real validation?
3. Какие 3-5 secondary metrics измерять в первом demo: package build success,
   evidence completeness, blocker detection, stale detection, audit completeness,
   time-to-decision, external-check opens?
4. Какие counter-metrics нельзя ухудшить: false-safe verdict, false-block rate,
   review fatigue, duplicate Conflicts view, time added by package, unclear next
   step?
5. Какой minimal experiment доказывает, что canonical transformer terminal case
   объясняет network consequence лучше, чем geometry diff alone?
6. Как проверить stale/pre-post failure sidecar: какие события должны сделать
   previous approval/package stale и какой outcome считается pass/fail?
7. Какие safety blockers имеют absolute veto независимо от aggregate metrics:
   unresolved association delta, dirty trace path, invalid subnetwork, missing
   evidence, stale approval, unexpected trace impact?
8. Как отличить полезный `blocked post` от лишнего false-block, который просто
   тормозит workflow?
9. Какие signals покажут, что package дублирует native Conflicts view и не
   сокращает путь к решению?
10. Какие данные нужно сохранять для каждого run: seed/checksum, package id,
    risk tier, blockers, trace/subnetwork freshness, decision, audit object,
    time-to-decision, manual checks?

## Should-Вопросы

11. Нужен ли manual baseline для Release 2 отдельно от Release 1: `ArcGIS native
    + SOP + expert handoff` на том же transformer terminal scenario?
12. Сколько synthetic runs достаточно для developer confidence до реального
    интервью: один scripted demo, 10 повторов fixture, 30 benchmark runs или
    другой threshold?
13. Какие гипотезы самые рискованные: computed evidence realism, risk tier
    calibration, stale detection, role trust, field evidence scope, performance,
    false-safe UI language?
14. Какие критерии заставят сменить курс: package не объясняет consequence за
    1-2 минуты, пользователь все равно открывает внешний GIS, hard blockers не
    воспроизводятся, audit не помогает repeat review?

## Nice-Вопросы

15. Какие future validation вопросы вынести к реальным `Editor`/`Reviewer`
    после developer demo: понятность risk tier, достаточность evidence, доверие
    к blocker verdict, приемлемость sample review для `Normal`, нужность
    specialist escalation?

## Чек-Лист Встречи

- Начать с caveat: Release 2 package пока доказывается на developer demo, не на
  production/user validation.
- Разделить metrics для developer confidence и metrics для будущей user
  validation.
- Для каждой метрики назвать источник данных: UI event, audit object,
  package telemetry, manual observation или post-run notes.
- Проверить, что false-safe verdict важнее красивого happy path.
- Зафиксировать pass/fail criteria для canonical scenario и stale sidecar.
- Отдельно записать signals, при которых package считается лишним экраном.
- В конце согласовать, какие answers станут RAW source для `/ingest`, а какие
  останутся open follow-up.

## Wiki-Ноды После Ответов

- [[../concepts/metrics]] - добавить Release 2 draft metrics только после
  ответов или RAW source.
- [[../decisions/risk_assumption_log]] - уточнить assumptions и risks Release 2
  по false-safe, stale detection, evidence realism и duplicate workflow.
- [[../decisions/followups/index]] - добавить follow-up'ы для experiments,
  baseline, user validation и implementation contract.
- [[../solution/roadmap]] - уточнить next experiment/validation step, если
  ответы меняют порядок действий.
- [[../decisions/release_2_conflict_explanation]] - уточнить consequences, если
  метрики меняют package boundary или claims.

## Follow-up После Встречи

- Положить ответы или заметки в `RAW_inputs/meetings/`.
- Запустить `/ingest` для нового RAW source.
- Не обновлять accepted metrics без источника с ответами.
- Если появятся benchmark или experiment design, решить, где хранить reports:
  `docs/benchmarks/` или отдельный `docs/release_1/` artifact.
- Не формулировать external claims о снижении unsafe post/review time до real
  validation с представителями ролей.

## Связи

- [[2026-06-20-geometry-association-conflict-f4]]
- [[2026-06-22-geometry-association-conflict-f5]]
- [[2026-06-23-geometry-association-conflict-f6]]
- [[../decisions/release_2_conflict_explanation]]
- [[../concepts/metrics]]
- [[../decisions/risk_assumption_log]]
- [[../decisions/followups/index]]
- [[../solution/roadmap]]
