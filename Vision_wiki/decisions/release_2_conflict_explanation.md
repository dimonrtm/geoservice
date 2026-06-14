---
title: Release 2 Conflict Explanation
type: decision
status: planned
created: 2026-06-14
updated: 2026-06-14
source: RAW_inputs/meetings/release2_conflict_explanation_editor_reviewer_answers.md
tags: [decision, release-2, conflict-explanation, editor, reviewer, utility-network]
---

# Release 2 Conflict Explanation

## Контекст

Сравнение `Base / Mine / Default` объясняет расхождение версий, но не доказывает
безопасность состояния инженерной сети. Release 2 должен объяснять geometry и
association conflict через сетевое последствие и evidence для решения.

Текущий Release 1 не меняется.

## Решение

Conflict explanation строится как consequence-first карточка.

Обязательный первый уровень:

- человекочитаемое описание причины и сетевого последствия;
- risk tier и факты, которые его определили;
- affected service, customers/devices и subnetwork;
- proposed resolution и следующий безопасный шаг;
- явные blockers для approve и `post`.

Обязательный evidence level:

- `Base / Mine / Default`;
- geometry diff и association diff;
- validation result, dirty areas и network errors;
- trace before/after с added/removed elements;
- work order, field evidence, автор, время и причина изменения;
- решение `Editor`, решение `Reviewer` и подтверждение специалиста, если
  требуется.

Обязательные workflow rules:

- recommendation не является автоматическим решением;
- `High/Critical` нельзя автоматически approve или downgrade;
- unresolved association diff, stale approval, неполная validation, неожиданный
  trace impact и network errors блокируют `post`;
- изменение geometry, association, network attribute, terminal configuration
  или `Default` аннулирует explanation и approval;
- повторный review показывает delta после прошлого approval и повторяет
  validation/trace;
- audit сохраняет рассмотренные альтернативы, risk before/after, evidence,
  решения ролей, stale events и итог `post`.

## Ролевой Контракт

- `Editor` отвечает за предложение resolution, его причину, evidence и
  подготовку безопасного change package.
- `Reviewer` проверяет соответствие work order/evidence, сетевое последствие и
  post gate; для сложных сетевых изменений возвращает на Manual edit, а не
  исправляет их скрыто.
- Профильный специалист подтверждает domain-specific safety для `Critical`.
- Владелец authoritative data сохраняет финальное полномочие по спорному
  authoritative state согласно planned routing.

## Неразрешенное Расхождение

Источник относит association diff и trace change минимум к `High`, повышая до
`Critical` при service, safety, network rule или subnetwork impact. Нода
[[conflict_resolution_routing]] сейчас определяет любое изменение trace как
`Critical`.

До решения [[conflicts/2026-06-14-trace-risk-tier-boundary]] точная автоматическая
классификация risk tier не считается утвержденным implementation contract.

## Последствия

- UX должен раскрывать детали постепенно и не начинаться с полной таблицы
  атрибутов.
- Batch review ограничивается однотипными `Simple/Normal` случаями без network
  impact.
- Queue sorting учитывает `Critical`, SLA, affected service, trace impact,
  `High`, work order priority и domain/area.
- Реальная применимость остается design-гипотезой до проверки с участниками
  обеих ролей.

## Связи

- [[../chats/2026-06-14-release-2-conflict-explanation-editor-reviewer-research]]
- [[conflict_resolution_routing]]
- [[conflicts/2026-06-14-trace-risk-tier-boundary]]
- [[risk_assumption_log]]
- [[followups/index]]
