---
title: Geometry/Association Conflict Пользователи И Боль
type: session
status: active
created: 2026-06-18
updated: 2026-06-18
source: RAW_inputs/meetings/geometry_association_conflict_f2.md
tags: [discovery, phase-f2, release-2, geometry-association-conflict, utility-network, synthetic-research]
---

# Geometry/Association Conflict Пользователи И Боль

## Контекст

`RAW_inputs/meetings/geometry_association_conflict_f2.md` - research/design
input по Ф2 для Release 2 `geometry/association conflict`. Источник
реконструирует пользователя и боль через mechanics utility network,
branch/named version, reconcile/post, associations, dirty areas, trace и
subnetwork state. Это не direct user interview и не доказанный product claim.

## Главные Тезисы

- Primary user в этом конфликте - `Editor` в именованной версии, который уже
  сделал изменение и должен решить, можно ли безопасно довести change set до
  authoritative state.
- `Reviewer` - вторичный пользователь для сложных случаев и package approval;
  version admin и профильный инженер являются эпизодическими ролями для прав
  публикации, domain escalation или rule/subnetwork ambiguity.
- Боль `Editor`: он видит, что feature изменился, но не получает в одном месте
  ответа, меняет ли конфликт только representation на карте или authoritative
  network behavior.
- Формальный conflict проявляется на reconcile, но риск накапливается раньше:
  при edit/validate появляются dirty areas, rule errors или trace uncertainty.
  Перед `post` риск возвращается, если `Default` изменился после reconcile.
- Текущий обходной путь - ручная сборка контекста из Differences/Conflicts
  view, association tools, diagrams, validation, dirty areas, trace,
  subnetwork checks, work order, field evidence, screenshots, notes и устных
  подтверждений.
- Показательный сценарий - transformer/service device/line association: Mine
  обновляет equipment, geometry, terminal path, containment или structural
  attachment по work order, а Default параллельно меняет связанный device,
  asset type, terminal-relevant attributes или connectivity.

## Пользователь И Момент Боли

Лучший archetype - офисный `Utility GIS editor` / data steward распределительной
utility-сети с практическим знанием layers, asset groups/types, named versions,
reconcile/post, dirty areas и traces. Зона работы обычно ограничена районом,
feeder, pressure zone или другим operational area.

Проблема проходит через несколько состояний:

1. `Editor` впервые чувствует неопределенность при локальной QA после edit и
   validation.
2. Как version conflict проблема становится явной на reconcile.
3. Как governance problem она возникает перед `post`, если `Default` изменился
   после reconcile или approval.

## Боль И Обходной Путь

Geometry diff сам по себе не доказывает безопасность изменения. Для
`geometry/association conflict` последствия живут в connectivity,
containment, structural attachment, terminals, network attributes, trace и
subnetwork state. Associations не воспринимаются как обычные геометрические
объекты, поэтому `Editor` вынужден дополнительно проверять association diff,
dirty areas, validation errors, trace before/after и subnetwork status.

Контекст теряется на стыке пяти вещей:

- work order и field evidence;
- association diff;
- dirty areas и validation/network errors;
- trace/subnetwork consequence;
- reviewer comments, change history и audit.

## Критерий Успеха

Успешный outcome для `Editor` - не просто закрытый conflict, а доказанный safe
post candidate:

- выбрана правильная representation;
- validation и dirty areas находятся в допустимом состоянии;
- association/terminal state согласован с rules;
- trace подтверждает ожидаемую traversability или явно помечен unreliable;
- subnetwork state не становится invalid;
- reviewer/owner authoritative data понимают, что именно approved/post
  authorized;
- audit фиксирует логику решения и evidence.

## Сигналы Routing

- `Editor` может решить сам, если conflict локальный, validation clean, нет
  rule errors, terminal/subnetwork effect и неожиданных trace changes.
- Нужен `Reviewer`, если надо выбрать между competing representations
  named/default или защитить association/attribute logic, которую нельзя
  объяснить одним geometry screenshot.
- Нужен профильный специалист, если меняются service/subnetwork/safety
  semantics, появляется unexpected trace impact, invalid subnetwork, terminal
  ambiguity или требуется административное изменение rule base.

## Caveats

Источник усиливает planned модель Release 2, но не закрывает external
validation. Нельзя утверждать как доказанный факт, что consequence-first
explanation снижает внешние проверки, ускоряет решение или безопасно переводит
`Normal` в audit/sample review до проверки с реальными `Editor` и `Reviewer`.

## Связи

- [[../entities/personas/utility_gis_editor]]
- [[../entities/personas/utility_gis_reviewer]]
- [[../concepts/jtbd]]
- [[../decisions/conflict_resolution_routing]]
- [[../decisions/release_2_conflict_explanation]]
- [[../decisions/risk_assumption_log]]
- [[../decisions/followups/index]]
