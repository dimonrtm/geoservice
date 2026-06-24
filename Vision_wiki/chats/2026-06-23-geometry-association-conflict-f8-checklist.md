---
title: Geometry/Association Conflict Ф8 Closeout Checklist
type: chat
status: planned
created: 2026-06-23
updated: 2026-06-23
source: "user request to /discover --context geometry/association conflict --phase Ф8, 2026-06-23"
tags: [discovery, phase-f8, release-2, geometry-association-conflict, closeout]
---

# Geometry/Association Conflict Ф8 Closeout Checklist

## Цель Ф8

Подготовить closing-проход по Release 2 `geometry/association conflict` после
Ф1-Ф7: проверить, какие решения уже можно считать draft-contract, какие вопросы
остаются открытыми, какие RAW inputs должны появиться перед `/ingest`, и какой
следующий план нужен для `implementation contract` и developer demo.

Ф8 не должна расширять scope Release 2. Ее задача - собрать итоговый пакет
знаний и отделить ready-to-implement decisions от гипотез, которые требуют
реальной validation.

## Контекст Встречи

- Контекст: Release 2 `geometry/association conflict`.
- Фаза: Ф8, closeout и подготовка следующего плана.
- Предполагаемый участник: владелец pet-проекта / разработчик demo.
- Длительность по умолчанию: 45-60 минут.
- Нужное знание: что считается достаточным для перехода от discovery к
  implementation contract и measurement harness.
- Материалы: Ф4-Ф7 ноды `geometry/association conflict`,
  [[../decisions/release_2_conflict_explanation]],
  [[../concepts/metrics]], [[../decisions/risk_assumption_log]],
  [[../solution/roadmap]], [[../decisions/followups/index]].

## Must-Вопросы

1. Какие решения по Release 2 package уже считаем готовыми для
   implementation contract: canonical transformer terminal scenario, read-only
   package, state machine, API/events, hard blockers, audit schema, metrics или
   что-то еще?
2. Какие решения остаются только design-гипотезами до реальных
   `Editor`/`Reviewer`: primary user, risk tier calibration, sample review для
   `Normal`, specialist escalation, trust к blocker verdict?
3. Какие открытые вопросы должны блокировать implementation contract, а какие
   можно оставить как post-demo validation follow-up?
4. Какие новые RAW inputs должны появиться после этой Ф8: ответы closeout,
   measurement harness draft, implementation contract draft, demo script,
   baseline notes или другое?
5. Есть ли конфликт между текущими Ф4-Ф7 нодами и старой документацией Release
   1 / Release 2, который надо зафиксировать как follow-up, а не править
   сразу?
6. Какие wiki-ноды должны быть обновлены после ответов Ф8: summary chat,
   [[../decisions/release_2_conflict_explanation]], [[../concepts/metrics]],
   [[../solution/roadmap]], [[../decisions/risk_assumption_log]],
   [[../decisions/followups/index]]?
7. Какие 3 следующих шага после Ф8: подготовить implementation contract,
   measurement harness, frozen canonical dataset, developer demo script,
   benchmark/run schema или user validation checklist?
8. Что должно быть явным non-goal для следующего шага: native conflict editor
   replacement, production topology engine, hosted/on-prem rollout,
   ERP/EAM/OMS/ADMS integrations, batch review/SLA queue?
9. Какие acceptance gates должны стоять перед началом реализации: zero
   false-safe pass/fail, computed core evidence, stale/pre-post sidecar,
   audit repeat review, P95 targets, observability?
10. Какая формулировка допустимого claim после developer demo корректна, чтобы
    не обещать production-safe post или реальное снижение review time без
    validation?

## Should-Вопросы

11. Какой формат артефакта удобнее для implementation contract: одна
    decision-нода, отдельный `docs/release_2/` design, ADR candidates в
    `Code_wiki`, или комбинация?
12. Какие данные из Ф7 run schema обязательно должны попасть в audit object, а
    какие остаются telemetry/debug fields?
13. Нужно ли перед implementation contract создать отдельный checklist для
    real `Editor`/`Reviewer` validation, или достаточно расширить
    `FU-2026-06-14-001`?
14. Какие старые follow-up'ы можно закрыть, объединить или оставить как
    long-term, чтобы очередь не мешала следующему плану?

## Nice-Вопросы

15. Какой самый короткий demo narrative должен увидеть человек в первые 2
    минуты: проблема, consequence, blockers, safe next step, audit или
    comparison against native Conflicts view?

## Чек-Лист Встречи

- Начать с краткого резюме Ф4-Ф7: scenario, package boundary, NFR,
  metrics/risks.
- Отделить `ready for implementation contract` от `requires user validation`.
- Проверить, что zero false-safe важнее speed/pretty demo.
- Зафиксировать, какие open questions являются blockers.
- Назвать конкретные RAW artifacts, которые появятся после встречи.
- Не редактировать старые product/technical docs на встрече; конфликты уносить
  в follow-up.
- В конце согласовать 3 следующих шага и owner для каждого шага.

## Wiki-Ноды После Ответов

- `Vision_wiki/chats/YYYY-MM-DD-geometry-association-conflict-f8.md` - summary
  Ф8 closeout после RAW source.
- [[../decisions/release_2_conflict_explanation]] - уточнить final draft
  boundary и допустимые claims, если Ф8 это подтвердит.
- [[../concepts/metrics]] - уточнить, какие Ф7 metrics переходят в
  implementation contract.
- [[../solution/roadmap]] - уточнить next steps: implementation contract,
  measurement harness, canonical dataset, demo script.
- [[../decisions/risk_assumption_log]] - добавить/закрыть assumptions и risks,
  если Ф8 подтверждает их статус.
- [[../decisions/followups/index]] - добавить blockers, post-demo validation и
  conflict/documentation follow-up'ы.
- `memory/project-state.md` - обновить последний `/discover` и live open
  questions.

## Follow-up После Встречи

- Положить ответы Ф8 в `RAW_inputs/meetings/`.
- Запустить `/ingest` для нового RAW source.
- Если появится implementation contract draft, решить: это RAW input для
  Vision_wiki или отдельный design artifact в `docs/release_2/`.
- Если появятся технические ADR candidates, заводить их отдельно и не смешивать
  с `/discover` checklist.
- Не формулировать external claims о снижении unsafe post/review time до real
  validation с представителями ролей.

## Связи

- [[2026-06-20-geometry-association-conflict-f4]]
- [[2026-06-22-geometry-association-conflict-f5]]
- [[2026-06-23-geometry-association-conflict-f6]]
- [[2026-06-23-geometry-association-conflict-f7]]
- [[../decisions/release_2_conflict_explanation]]
- [[../concepts/metrics]]
- [[../decisions/risk_assumption_log]]
- [[../solution/roadmap]]
- [[../decisions/followups/index]]
