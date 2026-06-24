---
title: Release 2 Conflict Explanation
type: decision
status: planned
created: 2026-06-14
updated: 2026-06-23
source: "RAW_inputs/meetings/release2_conflict_explanation_editor_reviewer_answers.md; RAW_inputs/meetings/Reviwer Decision.md; RAW_inputs/meetings/geometry_association_conflict_f1.md; RAW_inputs/meetings/geometry_association_conflict_f2.md; RAW_inputs/meetings/geometry_association_conflict_f4.md; RAW_inputs/meetings/geometry_association_conflict_f5.md; RAW_inputs/meetings/geometry_association_conflict_f6.md; RAW_inputs/meetings/geometry_association_conflict_f7.md; RAW_inputs/meetings/geometry_association_conflict_f8.md"
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

Ф2 research/design input уточняет, что primary pain несет `Editor`: без
GeoService он собирает consequence вручную из Differences/Conflicts view,
association tools, dirty areas, validation, trace, subnetwork checks, work
order, field evidence, screenshots и notes.

Ф4 research/design input задает demo scope: canonical scenario - конфликт
вокруг `medium-voltage line / midspan tap / high-side terminal of transformer`,
где terminal-aware connectivity association делает сетевое последствие видимым
лучше, чем чистый geometry conflict.

Ф5 research/design input уточняет rollout: первое demo остается internal
developer demo, появляется после reconcile и до review/post как decision
package, а не отдельный dashboard. Главный value signal - меньше внешних
проверок и быстреее уверенное go/no-go решение; audit quality важен как второй
эффект, а снижение unsafe/stale post risk остается гипотезой до live
validation.

Ф6 research/design input уточняет implementation contract: первый demo должен
иметь read-only package, вычисляемое core evidence, stale rules, hard blockers,
минимальный audit object, внешний package API и internal orchestration boundary.

Ф7 research/design input уточняет измерительный контракт: developer demo
доказывает не product adoption, а `contract readiness pass rate` при нулевом
`false-safe` на hard-block scenarios; speed и external-check reduction остаются
secondary demo indicators до реальных `Editor`/`Reviewer`.

Ф8 closeout фиксирует Release 2 как pre-post decision-support/control layer
вокруг `reconcile -> consequence package -> review -> post`, а не как новый
conflict resolution engine. Implementation contract v0.1 должен заморозить
states, package schema, blocker semantics, stale triggers, minimal audit object,
acceptance gates и non-goals; human layer остается отдельной validation-задачей.

Текущий Release 1 не меняется.

## Решение

Conflict explanation строится как consequence-first карточка.

Ф8 уточняет центральный scope: первичное решение Release 2 - `approval of
change package as a pre-post gate`. `Editor` разрешает конфликт в native edit
workflow, а GeoService собирает consequence package и помогает принять human
decision, можно ли допускать пакет дальше. Routing/escalation является outcome,
а не центральной сущностью первого контракта.

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

Ф8 вводит более явную пару состояний:

- `approve package` - reviewer согласен с change package и объяснением
  сетевого последствия;
- `can post` - у пакета нет hard blockers, approval не stale, target/default
  state не ушел вперед после reconcile/approval.

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
- subnetwork status и явный флаг, если trace unreliable из-за dirty/invalid
  topology или subnetwork state;
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

## Ф4 Demo Scope

Первое Release 2 demo должно доказывать не собственный conflict editor, а
consequence-first decision support поверх native conflict workflow.

MVP boundary:

- read-only `conflict package`;
- routing recommendation;
- persistent audit object;
- no write-back replacement UI;
- no own topology engine;
- no full resolve/post workflow parity.

Rollout boundary:

- встроенный step после reconcile и до review/post;
- один canonical transformer terminal case как основной demo;
- stale/pre-post failure sidecar как обязательный negative case;
- no separate dashboard, batch review queue или SLA orchestration в первом
  rollout;
- no live ERP/EAM/OMS/ADMS integration, full mobile/offline stack или
  production-grade external GIS replacement.

Первый `conflict package` содержит:

- `Current / Target / Common Ancestor` или эквивалентные `Mine / Default /
  Base` representations;
- geometry diff;
- association delta;
- dirty areas и validation status;
- trace before/after или явный `trace not trustworthy`;
- subnetwork status;
- work order и field evidence references.

Safe next steps:

- self-resolve, если representation diff не меняет network consequence,
  validation clean, trace эквивалентен и subnetwork status стабилен;
- send to Reviewer, если network consequence bounded, объясним и требует
  package approval;
- escalate to specialist, если меняется terminal path, affected service,
  subnetwork boundary/semantics, rule validity или требуется профильное знание;
- block post, если basis недостоверен: dirty/invalid topology, invalid
  subnetwork, stale approval, new `Default` edits after reconcile или missing
  required evidence.

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

- `Normal` demo case: geometry линии меняется, association delta отсутствует,
  validation clean, trace before/after эквивалентен, subnetwork status не
  меняется; next step - self-resolve.
- Безопасный `High`: ограниченный geometry/attribute diff, clean validation,
  trace без subnetwork/controller impact; `Reviewer` принимает финальное
  package approval, а `post` возможен только если `Default` не изменился.
- Geometry почти не изменилась, но connectivity association трансформатора или
  service device меняется существенно: визуально это небольшой map diff, но по
  смыслу возможное изменение authoritative network behavior, trace,
  subnetwork membership и downstream interpretation.
- `Editor` может self-resolve только если conflict локальный, validation clean,
  нет rule errors, terminal/subnetwork effect и неожиданных trace changes; при
  competing representations или association/attribute logic нужен `Reviewer`.
- `Critical`: association или terminal/path change меняет upstream/downstream
  behavior или dirty/invalid subnetwork; без dual approval и clean subnetwork
  state `post` невозможен.
- Stale approval: после approval изменился `Default` или пакет; approval
  помечается stale, показывается delta-since-approval и обновленный package
  summary, `post` заблокирован до repeat review.
- Ф4 failure case: validate after reconcile, новые `Default` edits или
  untrustworthy trace/subnetwork делают прежнее reviewer decision stale;
  система блокирует `post` и требует пересборку decision package.

## Ф6 Implementation Contract

Первый package обязан содержать:

- `Base / Mine / Default`;
- geometry diff;
- association delta;
- dirty areas и validation/network errors;
- trace evidence для affected path, если package заявляет network consequence;
- subnetwork status, если конфликт затрагивает controller, feeder, tier
  boundary или subnetwork semantics;
- work order и field evidence как contextual evidence.

State machine:

- `draft package`;
- `ready for review`;
- `approved`;
- `stale`;
- `blocked post`;
- `escalated`;
- `repeated review`.

Package/approval становится stale после topology-relevant changes named
version, нового reconcile, изменения `Default`, validate after reconcile,
update subnetwork или изменения risk-relevant evidence: trace path, blockers,
subnetwork status, error set, association delta.

Ф6 уточняет hard blockers:

- unresolved conflicts или re-reconcile required перед `post`;
- error dirty areas / network errors в affected scope;
- dirty areas на claimed trace path;
- dirty/invalid affected subnetwork;
- unresolved association delta, влияющий на connectivity, containment,
  structural attachment или locatability.

Минимальный внешний API первого demo:

- `GET package summary`;
- `GET package details`;
- `POST recompute package`;
- `POST reviewer decision`;
- `GET audit record`;
- `GET package status` или push updates;
- optional `POST pre-post check`.

Реальные reconcile/replace/post actions остаются вне первого demo или за
stub/native workflow. Ценность Release 2 - объяснить сетевое последствие и
отфильтровать false-safe decisions, а не дублировать native conflict editor.

## Ф7 Metrics And Guardrails

North Star для Release 2 package: помочь квалифицированному человеку быстро
принять reviewable go/no-go решение по сетевому конфликту и сохранить, почему
это решение было принято, не скрывая hard blockers и не обещая
production-safe `post` без свежей проверки.

Primary developer-demo metric:

- `contract readiness pass rate` по canonical scenario и sidecar variants.

Secondary metrics:

- `package build success`;
- `evidence completeness`;
- `blocker detection`;
- `stale detection`;
- `audit completeness`;
- `time-to-decision` и `external-check opens` только как internal demo
  indicators.

Absolute counter-metric:

- `false-safe verdict count = 0`; один false-safe на dirty trace path, invalid
  subnetwork, unresolved association delta, stale package/approval или missing
  evidence проваливает demo независимо от aggregate metrics.

Package считается дублирующим native Conflicts view, если он повторяет только
`Current / Target / Common Ancestor`, не объясняет consequence, не дает clear
next step, не создает durable audit object или заставляет reviewer сразу
открывать внешний GIS/trace/expert handoff.

## Ф8 Implementation Contract Closeout

К implementation contract v0.1 готовы:

- scope как pre-post decision-support layer;
- handoff после reconcile и package build;
- minimal package schema: `Base / Mine / Default`, geometry diff, association
  delta, dirty areas, validation/topology status, trace consistency/freshness,
  subnetwork status при затронутой subnetwork semantics, work order/change
  request id, explanatory comments/history и field evidence для High/Critical
  или неочевидного rationale;
- separation `approve package` / `can post`;
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

До real `Editor`/`Reviewer` validation остаются гипотезами:

- точная calibration `Normal / High / Critical`;
- authority matrix для High/Critical;
- sample review policy для `Normal`;
- field evidence sufficiency thresholds;
- UX repeat review и `delta since previous approval`;
- language of trust.

Implementation contract реально блокируют: владелец финального решения для
`Critical`, evidence matrix по tier, exact stale events, MVP boundary между
read-only decision support и action buttons, а также гарантированно доступные
demo/runtime integrations для work order, trace/subnetwork data и evidence.

Первый implementation contract лучше делать как ADR-style Markdown contract с
machine-readable YAML/JSON appendices: scope, actors, states, events, decision
semantics, blockers, stale rules, non-goals и acceptance gates в основном
документе; package schema, audit schema, API/events, fixture manifest, P95
targets и observability fields - в приложениях.

## Последствия

- UX должен раскрывать детали постепенно и не начинаться с полной таблицы
  атрибутов.
- Implementation contract должен описать state machine, API/events, audit
  schema и demo fixtures для consequence package.
- Support package для developer demo должен включать фиксированный сценарий,
  fixtures, troubleshooting по dirty/stale/invalid subnetwork, calibration
  notes по risk tiers, audit examples, known limitations и negative fixture с
  blocked `post`.
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
- До user validation допустимый claim ограничен формулировкой: demo показывает
  consequence-first package для reviewable go/no-go decision и воспроизводимого
  stale/blocker handling на synthetic utility-network cases.
- После Ф8 допустимый developer-demo claim формулируется еще уже: `В developer
  demo Release 2 собирает consequence package для utility-network конфликта,
  делает видимыми hard blockers и помогает сформировать более обоснованное
  go/no-go решение перед post на synthetic scenario.`
- Для первого Ф4 demo не вводить `Simple` как safe default: сначала нужно
  доказать отсутствие network consequence. `Simple` остается planned routing
  tier для будущей validation.
- Первый implementation contract не должен строить новый topology engine,
  достигать full ArcGIS parity, делать full in-product conflict editing UI,
  batch review queue/SLA routing, production-grade on-prem hardening или
  authoritative-safe post claims без real validation.

## Связи

- [[../chats/2026-06-14-release-2-conflict-explanation-editor-reviewer-research]]
- [[../chats/2026-06-16-release-2-reviewer-decision]]
- [[../chats/2026-06-17-geometry-association-conflict-f1]]
- [[../chats/2026-06-18-geometry-association-conflict-f2]]
- [[../chats/2026-06-20-geometry-association-conflict-f4]]
- [[../chats/2026-06-22-geometry-association-conflict-f5]]
- [[../chats/2026-06-23-geometry-association-conflict-f6]]
- [[../chats/2026-06-23-geometry-association-conflict-f7]]
- [[../chats/2026-06-23-geometry-association-conflict-f8]]
- [[conflict_resolution_routing]]
- [[conflicts/2026-06-14-trace-risk-tier-boundary]]
- [[risk_assumption_log]]
- [[followups/index]]
