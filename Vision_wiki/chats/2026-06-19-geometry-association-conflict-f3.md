---
title: Geometry/Association Conflict Альтернативы И Конкуренция
type: session
status: active
created: 2026-06-19
updated: 2026-06-19
source: RAW_inputs/meetings/geometry_association_conflict_f3.md
tags: [discovery, phase-f3, release-2, geometry-association-conflict, alternatives, synthetic-research]
---

# Geometry/Association Conflict Альтернативы И Конкуренция

## Контекст

`RAW_inputs/meetings/geometry_association_conflict_f3.md` - research/design
input по Ф3 для Release 2 `geometry/association conflict`. Источник уточняет
конкурентный baseline и критерии выбора для слоя принятия уверенного решения
по network consequence. Это не direct user interview и не vendor due
diligence.

## Главные Тезисы

- Release 2 конкурирует не с "другим AI", а с `ArcGIS native workflow + SOP +
  экспертный чат/звонок`.
- Самый опасный incumbent - `ArcGIS Enterprise + Utility Network + branch
  versioning`, потому что он уже находится в authoritative editing loop и
  закрывает technical merge/reconcile/post.
- Второй конкурент - локальный регламент и ручная экспертиза: `Editor`
  собирает consequence из Conflicts/Differences, associations, dirty areas,
  validation, trace, work order, notes и устных подтверждений.
- Третий конкурент - custom internal dashboard поверх существующего GIS/API
  stack; в enterprise-контексте соседние work/design suites вроде Cityworks и
  Bentley могут закрывать work context, queue и governance, но не обязательно
  semantic reviewer decision по conflict.
- Generic self-hosted GIS stack, например NextGIS-like platform, конкурирует
  как governance/API/history foundation, но не доказывает utility-network
  consequence review без отдельной проверки.

## Где Baseline Good Enough

Baseline без GeoService достаточен, если conflict локальный, визуально
понятный и семантически узкий:

- нет изменения network attributes, associations или terminal configuration;
- validation чистая;
- dirty areas/error dirty areas не создают неопределенности;
- trace или subnetwork consequence не требуется для решения;
- сильный `Reviewer`/`GIS lead` и SOP уже поглощают редкие спорные случаи.

## Где Baseline Ломается

Baseline ломается, когда geometry conflict перестает быть только geometry
conflict:

- association diff меняет connectivity, containment или structural attachment;
- dirty areas означают, что карта и network topology расходятся;
- trace interpretation требует ручной сборки нескольких outputs/options;
- approval может стать stale после изменения `Default` или topology-relevant
  части пакета;
- audit и handoff между `Editor`, `Reviewer` и профильным специалистом не
  собраны в единый decision package.

## Критерии Выбора

Для внедрения важнее цены:

1. trust in authoritative state;
2. audit trail и воспроизводимость reviewer decision;
3. deployment/security fit, включая on-prem и права доступа;
4. скорость до уверенного go/no-go решения;
5. снижение внешних проверок и лишних эскалаций.

Ключевые blockers: utility-network admin, data owner, `GIS lead`,
IT/security, compliance и operations.

## Demo Implication

Чтобы не выглядеть оберткой над Conflicts view, GeoService должен показать не
более красивый diff, а более короткий путь к обоснованному решению:

- единый conflict package с Mine/Default, association delta, dirty/error
  status, validation state и consequence summary;
- trace/subnetwork before/after как доказательство network consequence;
- decision/audit object: какие варианты рассмотрены, почему выбран resolution,
  какой risk before/after, кто согласовал и не устарело ли approval;
- измеримые сигналы: меньше внешних trace/check opens, ручных notes,
  screenshots, handoff и времени от reconcile до go/no-go.

## Scope Для Сравнения

Release 2 нужно сравнивать прежде всего с тремя baseline-режимами:

- `ArcGIS-native technical resolution`;
- manual expert regulation;
- custom internal overlay.

Из comparison scope лучше исключать generic web map servers, pure field data
collection apps, broad EAM/work-order suites и full design/digital twin suites,
если они не показывают именно decision support для authoritative
utility-network conflict resolution.

## Follow-up

- Расширить `FU-2026-06-01-002`: перед внешним сравнением проверить официальные
  URL и version scope для Bentley, Cityworks, NextGIS-like/self-hosted platform
  claims, а также уже известных non-Esri alternatives.
- Проверить с реальными `Editor`/`Reviewer`, снижает ли unified evidence
  context количество внешних проверок и time-to-confident-decision.

## Связи

- [[../entities/competitors/collaborative_editing_alternatives]]
- [[../entities/competitors/utility_gis_editor_market_landscape]]
- [[../concepts/product_vision_board]]
- [[../concepts/lean_canvas]]
- [[../decisions/risk_assumption_log]]
- [[../decisions/followups/index]]
