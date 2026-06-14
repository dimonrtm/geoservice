---
title: Доверенное Исследование Conflict Routing Для Utility GIS Editor
type: chat
status: active
created: 2026-06-14
updated: 2026-06-14
source: RAW_inputs/meetings/utility_gis_editor_geometry_association_conflict_answers.md
tags: [trusted-source, research, utility-gis-editor, conflict-resolution, risk-routing, next-release]
---

# Доверенное Исследование Conflict Routing Для Utility GIS Editor

## Контекст Источника

Источник содержит подготовленное доменное исследование `Utility GIS editor` по
`geometry/association conflict` и risk-tiered routing. Пользователь явно
установил его выше assistant-led workshop по уровню доверия.

Источник является каноническим design/research input для следующего релиза.
Он не является транскриптом прямого интервью с реальным пользователем и не
меняет текущий Release 1.

## Поддержанные Тезисы

- Риск конфликта нужно определять по сетевому последствию, а не только по типу
  записи в БД.
- Для решения нужны `Base / Mine / Default`, geometry diff, association diff,
  validation, trace impact, work order/evidence и audit.
- `Critical` должен блокировать `post`, запрещать auto-resolve и требовать
  повторного подтверждения после изменения данных.
- Сетевыми признаками риска являются connectivity/topology change, trace
  change, affected service, network rule violation, error dirty areas и
  update-delete сетевого объекта.
- Профильный специалист отвечает за инженерную корректность, Data Owner - за
  authoritative state, а техническое право выполнить `post` не равно праву
  принять спорное инженерное решение.
- Подтверждения должны становиться stale после изменения geometry,
  associations, network attributes или `Default`.

## Предлагаемая Карточка Конфликта

Источник предлагает сохранять и показывать:

- conflict type и risk tier;
- `Base / Mine / Default`;
- geometry и association diff;
- validation, dirty areas и trace before/after;
- affected subnetworks/customers/devices;
- work order и field evidence;
- ответственных, причины решений, timestamps и историю эскалации;
- факт invalidation старого approval.

## Решение Расхождений С Workshop

Источник заменяет менее доверенные правила assistant-led workshop:

- первым ответственным предлагает автора edit version, а workshop - автора
  изменения, уже попавшего в `Default`;
- далее сам источник считает авторство слабым критерием и рекомендует
  ответственность за affected network area, тип изменения и risk tier;
- для `High` источник отдает решение `Reviewer` после предложения `Editor`,
  тогда как workshop направляет эскалацию профильному специалисту через
  2 рабочих часа;
- для безопасного `Normal` источник допускает `post` с audit и sample review;
- для `Simple` источник предпочитает отсутствие эскалации вместо срока
  2 рабочих дня.

Каноническая planned модель обновлена в
[[../decisions/conflict_resolution_routing]]. Конфликт закрыт в
[[../decisions/conflicts/2026-06-14-next-release-conflict-routing-responsibility]].

## Ограничения Доказательности

- Источник принят владельцем проекта как доверенный design/research input, но
  не как external user evidence.
- Упомянутый исходник `Ф2(5).md` отсутствует в `RAW_inputs/`.
- Ссылки на Esri documentation перечислены в RAW source, но отдельно в рамках
  этого ingest не проверялись.
- Переносимость модели на реальный процесс требует проверки с реальными
  `Editor` и `Reviewer`.

## Follow-up

- Использовать `FU-2026-06-14-001` для внешней проверки канонической planned
  модели с реальными участниками.
- Текущий Release 1 не менять.
- В live-сессии проверить применимость назначения по affected network area,
  `Normal` sample review, отсутствие эскалации `Simple` и emergency path.

## Связи

- [[../decisions/conflict_resolution_routing]]
- [[../decisions/risk_assumption_log]]
- [[../decisions/followups/index]]
- [[2026-06-14-geometry-association-conflict-resolution-workshop]]
