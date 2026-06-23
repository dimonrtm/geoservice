---
title: Geometry/Association Conflict Ограничения И NFR Checklist
type: chat
status: planned
created: 2026-06-23
updated: 2026-06-23
source: "user request to /discover --context geometry/association conflict --phase Ф6, 2026-06-23"
tags: [discovery, phase-f6, release-2, geometry-association-conflict, nfr, implementation-contract]
---

# Geometry/Association Conflict Ограничения И NFR Checklist

## Цель Ф6

Подготовить встречу/рабочий проход по ограничениям и NFR для Release 2
`geometry/association conflict` перед `implementation contract`.

Ф6 должна превратить Ф4-Ф5 scope в проверяемые рамки для developer demo:
какие данные, state machine, API/events, audit, stale rules, observability,
performance и support package обязательны, а что остается outside scope.

## Контекст Встречи

- Контекст: Release 2 `geometry/association conflict`.
- Фаза: Ф6, ограничения и NFR.
- Предполагаемый участник: `разработчик demo` как decision maker, first user и
  budget owner внутреннего demo.
- Длительность по умолчанию: 45-60 минут.
- Нужное знание: достаточно ли constraints, NFR и implementation boundaries,
  чтобы начать `implementation contract` без расширения scope.
- Материалы: Ф1-Ф5 ноды `geometry/association conflict`,
  [[../decisions/release_2_conflict_explanation]],
  [[../decisions/conflict_resolution_routing]],
  [[../solution/nfr]], [[../decisions/constraints]] и
  [[../solution/architecture_vision]].

## Must-Вопросы

1. Какая минимальная demo-среда обязательна для Release 2: только local Docker
   Compose на reference hardware или нужен отдельный browser/backend profile?
2. Какие части `conflict package` обязательны для первого demo: `Base / Mine /
   Default`, geometry diff, association delta, dirty areas, validation, trace,
   subnetwork status, work order, field evidence?
3. Какие evidence можно имитировать fixture-данными, а какие должны быть
   вычислены из текущей модели данных?
4. Какие состояния обязательны в state machine: draft package, ready for
   review, approved, stale, blocked post, escalated, repeated review?
5. Какие события должны инвалидировать package или approval: изменение
   `Default`, новый reconcile, изменение geometry, association, network
   attribute, terminal path, validation result, trace/subnetwork status?
6. Какие жесткие `post` blockers должны попасть в implementation contract и
   быть показаны в demo?
7. Какой минимальный audit object нужен для Ф6: package hash, evidence snapshot,
   risk before/after, considered alternatives, decision maker, stale events,
   final safe next step?
8. Какие API/events обязательны для первого demo, а какие можно оставить как
   internal service calls без публичного contract?
9. Какие P95 targets применимы к Release 2 package: загрузка package, построение
   risk tier, открытие evidence details, stale invalidation, сохранение audit?
10. Какие observability signals нужны именно для debugging consequence package:
    correlation ID, package build log, validation/trace timing, reason codes,
    UI error state?

## Should-Вопросы

11. Достаточно ли одного canonical transformer terminal scenario и одного
    stale/pre-post failure sidecar, или нужны отдельные `Normal`, `High`,
    `Critical` fixtures в первом implementation contract?
12. Какие данные support package должен включать: demo script, expected
    outcomes, troubleshooting по dirty/stale/invalid subnetwork, calibration
    notes, known limitations, audit examples?
13. Какие security/access constraints нужны сверх текущих `Editor`/`Reviewer`:
    может ли `Editor` видеть весь evidence, кто видит audit, кто может override
    stale/blocker?
14. Что считать неприемлемым false-safe результатом в developer demo, даже если
    UI и happy path работают?

## Nice-Вопросы

15. Какие ограничения нужно сразу записать как future ADR candidates:
    production topology engine, live external GIS integration, batch review
    queue, SLA orchestration, object storage для evidence, on-prem/security
    hardening?

## Чек-Лист Встречи

- Начать с напоминания: Release 2 не заменяет native conflict editor и не
  расширяет текущий Release 1.
- Держать фокус на constraints для `implementation contract`, а не на UI
  wishlist.
- Для каждого NFR спросить: измеряется ли это в developer demo или остается
  future production concern.
- Отделять computed evidence от fixture/reference evidence.
- Зафиксировать blockers как machine-readable reasons, а не только текстовые
  warnings.
- Проверить, что stale/failure sidecar обязательнее красивого happy path.
- В конце проговорить accepted constraints, unresolved constraints и next
  artifact.

## Wiki-Ноды После Ответов

- [[../solution/nfr]] - добавить Release 2 draft NFR только после ответов или
  RAW source.
- [[../decisions/constraints]] - уточнить Release 2 implementation/demo
  constraints.
- [[../solution/architecture_vision]] - обновить Release 2 architecture
  boundary, если появятся новые обязательные компоненты или non-goals.
- [[../decisions/release_2_conflict_explanation]] - уточнить implementation
  consequences, если ответы меняют state machine, audit или blockers.
- [[../decisions/risk_assumption_log]] - добавить или уточнить риски false-safe,
  stale invalidation и fixture realism.
- [[../decisions/followups/index]] - добавить follow-up'ы для спорных NFR,
  benchmark или external validation.

## Follow-up После Встречи

- Положить ответы или заметки в `RAW_inputs/meetings/`.
- Запустить `/ingest` для нового RAW source.
- Не обновлять accepted NFR без источника с ответами.
- Проверить, нужен ли отдельный `implementation contract` документ в
  `docs/release_1/` или новая Vision/Code wiki нода.
- Если появятся новые technical contracts для API/events/audit, после
  реализации оценить необходимость `/ingest repository-change`.

## Связи

- [[2026-06-17-geometry-association-conflict-f1]]
- [[2026-06-18-geometry-association-conflict-f2]]
- [[2026-06-19-geometry-association-conflict-f3]]
- [[2026-06-20-geometry-association-conflict-f4]]
- [[2026-06-22-geometry-association-conflict-f5]]
- [[../decisions/release_2_conflict_explanation]]
- [[../decisions/conflict_resolution_routing]]
- [[../solution/nfr]]
- [[../decisions/constraints]]
- [[../solution/architecture_vision]]
- [[../decisions/followups/index]]
