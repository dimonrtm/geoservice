---
title: Release 2 Conflict Explanation
type: decision
status: planned
created: 2026-06-14
updated: 2026-06-17
source: "RAW_inputs/meetings/release2_conflict_explanation_editor_reviewer_answers.md; RAW_inputs/meetings/Reviwer Decision.md; RAW_inputs/meetings/geometry_association_conflict_f1.md"
tags: [decision, release-2, conflict-explanation, editor, reviewer, utility-network]
---

# Release 2 Conflict Explanation

## Контекст

Сравнение `Base / Mine / Default` объясняет расхождение версий, но не доказывает
безопасность состояния инженерной сети. Release 2 должен объяснять geometry и
association conflict через сетевое последствие и evidence для решения.

F1 research/design input уточняет границу: `Base / Mine / Default`, field diff и
geometry diff показывают feature representation, но не отвечают сами по себе,
изменились ли connectivity, containment, attachment/locatability, trace behavior
или subnetwork state.

Текущий Release 1 не меняется.

## Решение

Conflict explanation строится как consequence-first карточка.

`Reviewer decision` для Release 2 трактуется как approval of change package for
post readiness. `Reviewer` принимает решение по пакету изменения, а не только по
одному conflict resolution item. Conflict resolution остается подшагом внутри
reconcile/post workflow, routing/escalation - исключительным путем, а `post`
gate - отдельной технической проверкой против текущего `Default`.

Approval и `post authorization` разделяются:

- `approve package` подтверждает, что пакет содержательно корректен и
  безопасен по имеющимся evidence;
- `post authorized` подтверждает, что пакет все еще можно публиковать в
  `Default` сейчас, после актуального reconcile и технических gates;
- если между approval и `post` изменился `Default` или topology-relevant часть
  пакета, approval становится stale и требует repeat review.

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

- `Reviewer` получает пакет после `Editor proposal`, reconcile against current
  `Default` и pre-review gate: validation/topology, trace или subnetwork impact
  и Differences view;
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

Жесткие `post` blockers:

- невыполненный reconcile или изменение `Default` после reconcile;
- unreviewed conflicts;
- dirty areas в зоне предполагаемого сетевого эффекта;
- error dirty areas, network errors или invalid topology state;
- dirty/invalid subnetwork в affected contour;
- unresolved association diff с влиянием на connectivity, containment или
  structural attachment;
- unexpected trace impact без согласованного rationale;
- missing evidence для field facts, safety-related changes или service-impacting
  corrections.

## Ролевой Контракт

- `Editor` отвечает за предложение resolution, его причину, evidence и
  подготовку безопасного change package.
- `Reviewer` проверяет соответствие work order/evidence, сетевое последствие и
  post gate; для сложных сетевых изменений возвращает на Manual edit или
  эскалирует, а не исправляет их скрыто.
- Для `Normal` без network impact допустим audit + sample review без
  индивидуального reviewer approval.
- Для `High` `Reviewer` принимает финальное решение по содержанию пакета, а не
  только подтверждает proposal `Editor`.
- Для `Critical` нужен dual control: `Reviewer` + профильный специалист или
  utility-network admin.
- Владелец authoritative data / version administrator equivalent сохраняет
  финальное право publication в `Default` и право решения при разногласии.

## Разрешение Trace Boundary

`RAW_inputs/meetings/Reviwer Decision.md` уточняет, что trace change не должен
автоматически становиться `Critical`. `Critical` возникает, когда trace delta
меняет authoritative network behavior: affected service, subnetwork,
controllers, safety isolation, traversability/barriers, rule-dependent
connectivity или operational outputs.

Trace delta без service/subnetwork/safety semantics и без
rule/terminal/controller impact может оставаться `High`.

## Acceptance Examples

- Безопасный `High`: ограниченный geometry/attribute diff, clean validation,
  trace без subnetwork/controller impact; `Reviewer` принимает финальное
  package approval, а `post` возможен только если `Default` не изменился.
- Geometry почти не изменилась, но connectivity association трансформатора или
  service device меняется существенно: визуально это небольшой map diff, но по
  смыслу возможное изменение authoritative network behavior, trace,
  subnetwork membership и downstream interpretation.
- `Critical`: association или terminal/path change меняет upstream/downstream
  behavior или dirty/invalid subnetwork; без dual approval и clean subnetwork
  state `post` невозможен.
- Stale approval: после approval изменился `Default` или пакет; approval
  помечается stale, показывается delta-since-approval и обновленный package
  summary, `post` заблокирован до repeat review.

## Последствия

- UX должен раскрывать детали постепенно и не начинаться с полной таблицы
  атрибутов.
- Batch review ограничивается однотипными `Simple/Normal` случаями без network
  impact.
- Queue sorting учитывает `Critical`, SLA, affected service, trace impact,
  `High`, work order priority и domain/area.
- Реальная применимость остается design-гипотезой до проверки с участниками
  обеих ролей; новый источник является design/architecture input, а не direct
  user interview.
- До user validation нельзя формулировать как доказанные claims, что
  consequence-first explanation предотвращает unsafe post, снижает review
  friction, устраняет открытие внешней GIS или позволяет безопасно переводить
  `Normal` в audit/sample review.

## Связи

- [[../chats/2026-06-14-release-2-conflict-explanation-editor-reviewer-research]]
- [[../chats/2026-06-16-release-2-reviewer-decision]]
- [[../chats/2026-06-17-geometry-association-conflict-f1]]
- [[conflict_resolution_routing]]
- [[conflicts/2026-06-14-trace-risk-tier-boundary]]
- [[risk_assumption_log]]
- [[followups/index]]
