---
title: Geometry/Association Conflict Решение И Scope
type: session
status: active
created: 2026-06-20
updated: 2026-06-20
source: RAW_inputs/meetings/geometry_association_conflict_f4.md
tags: [discovery, phase-f4, release-2, geometry-association-conflict, demo-scope, synthetic-research]
---

# Geometry/Association Conflict Решение И Scope

## Контекст

`RAW_inputs/meetings/geometry_association_conflict_f4.md` - research/design
input по Ф4 для Release 2 `geometry/association conflict`. Источник задает
минимальный demo scope: показать не красивый diff, а способность за 1-2 минуты
объяснить, меняет ли conflict authoritative network behavior, и предложить
безопасный следующий шаг.

Источник написан как архитектурная интерпретация utility GIS, branch
versioning, associations, dirty areas, validation, trace и subnetwork state.
Это не direct user interview и не vendor due diligence. Внешние ссылки и
vendor/platform claims из RAW требуют отдельной проверки перед публичным
использованием.

## Главные Тезисы

- Canonical scenario для первого demo - `medium-voltage line / midspan tap /
  high-side terminal of transformer`: конфликт вокруг terminal-aware
  connectivity association, где обычный Differences/Conflicts view показывает
  representation diff, но не доказывает влияние на trace, subnetwork и safe
  post.
- Release 2 должен накладывать consequence package поверх native conflict
  workflow, а не заменять native conflict resolution.
- Первый `conflict package` должен собрать `Mine / Default / Common Ancestor`,
  geometry diff, association delta, dirty areas, validation status,
  trace before/after или явный `trace not trustworthy`, subnetwork status, work
  order и field evidence.
- За 1-2 минуты пользователь должен понять: меняется ли только representation
  или authoritative network behavior, можно ли доверять основанию решения, и
  какой next step безопасен.
- Ф4 MVP boundary: read-only decision support + routing + audit object.
  Write-back actions вроде native conflict replacement, собственный topology
  engine и полноценный resolve/post workflow не входят в первое demo.
- Для первого Ф4 demo достаточно `Normal / High / Critical`; `Simple` лучше
  не вводить как safe default, пока не доказано отсутствие network consequence.
- Лучший failure case - stale decision после изменения basis: новые изменения
  в `Default`, validate after reconcile, changed topology-relevant package или
  trace/subnetwork becoming untrustworthy.

## Walking Skeleton

1. Reconcile обнаруживает `geometry/association conflict`.
2. Система загружает `Current / Target / Common Ancestor`.
3. Пакет добавляет association delta.
4. Пакет добавляет dirty area и validation status.
5. Пакет добавляет trace before/after и subnetwork status.
6. Система строит consequence summary и risk tier.
7. UI предлагает safe next step: self-resolve, send to Reviewer, escalate to
   specialist или block post.
8. Решение или блокировка сохраняются как audit object, независимый от native
   conflict history.

## Acceptance Examples

- `Normal`: geometry линии меняется, association delta отсутствует, validation
  clean, trace before/after эквивалентен, subnetwork status не меняется;
  next step - self-resolve.
- `High`: меняется tap/terminal association вокруг трансформатора, trace
  меняется локально, но без downstream safety/service boundary effect; next
  step - send to Reviewer с готовым evidence package.
- `Critical/failure`: после review basis устарела из-за новых default edits,
  validate after reconcile или invalid trace/subnetwork; next step - stale,
  block post и пересборка decision package.

## Follow-up

- Проверить с реальными `Editor` и `Reviewer`, достаточно ли им association
  delta + trace summary + dirty/validation status без открытия внешней GIS.
- Проверить, считают ли они transformer-terminal scenario репрезентативным.
- Не формулировать внешние claims о снижении unsafe posts, устранении внешней
  GIS или сокращении review time до live validation.
- До implementation contract превратить scope в state machine, API/events,
  audit schema и demo fixtures.

## Связи

- [[../decisions/release_2_conflict_explanation]]
- [[../decisions/conflict_resolution_routing]]
- [[../solution/USM]]
- [[../solution/roadmap]]
- [[../solution/architecture_vision]]
- [[../decisions/risk_assumption_log]]
- [[../decisions/followups/index]]
