---
title: Geometry/Association Conflict Why-Now Для Release 2
type: session
status: active
created: 2026-06-17
updated: 2026-06-17
source: RAW_inputs/meetings/geometry_association_conflict_f1.md
tags: [discovery, release-2, geometry-association-conflict, utility-network, synthetic-research]
---

# Geometry/Association Conflict Why-Now Для Release 2

## Контекст

`RAW_inputs/meetings/geometry_association_conflict_f1.md` - research/design
input по Release 2 для `geometry/association conflict` в `Utility GIS editor`.
Источник написан как архитектурная интерпретация enterprise GIS и utility
network workflow. Это не прямое интервью с реальными `Editor`/`Reviewer` и не
готовая продуктовая спецификация.

Источник уточняет, почему после Release 1 нужен отдельный Release 2 слой
объяснения: когда reconcile/post loop уже существует, узким местом становится
не обнаружение diff, а понимание, меняет ли конфликт только картинку или
authoritative network behavior.

## Главные Тезисы

- `Editor` видит, что данные отличаются, но не может быстро понять, безопасно
  ли отличие для поведения сети.
- `Base / Mine / Default`, field diff и geometry diff показывают feature
  representation, но не объясняют consequence для network topology.
- Сетевые последствия `geometry/association conflict` могут затрагивать
  connectivity associations, containment semantics, structural attachment и
  locatability, trace behavior и subnetwork state.
- Если конфликт не объяснен через network consequence, `Editor` уходит во
  внешние проверки: trace, topology/dirty areas, дополнительные карты,
  screenshots, notes и устное подтверждение.
- Release 2 должен переводить feature conflict в объясненный network consequence
  до `post`.

Короткая формулировка причины Release 2: `Editor` должен перестать гадать,
меняет ли конфликт только картинку или меняет саму сеть.

## Уточнение Risk Tier

- `Normal`: representation-level conflict без изменения сетевой семантики после
  validation; нет изменения association type, terminal/connectivity semantics,
  новых error dirty areas, control trace не меняется, subnetwork state не
  становится inconsistent за пределами expected edit envelope.
- `High`: меняется важная сетевая интерпретация, но еще не
  safety-/authoritative-state semantics критического operational decision;
  примеры - изменение connectivity association, containment/attachment
  hierarchy с влиянием на locatability/visibility/trace inclusion, bounded delta
  в control trace, dirty areas, требующие validate/update subnetwork.
- `Critical`: не любой trace delta, а trace delta или association/terminal/path
  change, который меняет service/subnetwork/safety semantics или authoritative
  operational state: controllers, barriers, isolation, flow direction,
  downstream assets, switching/outage/safety decisions.

Более дорогая ошибка - пропустить реальный network impact, а не
переэскалировать безопасный conflict.

## Пример

Показательный пример - редактирование подключения трансформатора или service
device, где geometry почти не меняется, но connectivity association меняется
существенно. На карте это выглядит как небольшой map diff, но по смыслу меняет
authoritative network behavior.

## Caveats И Follow-up

Источник явно требует не превращать synthetic/design evidence в product claims
без реальной validation. До проверки с реальными `Editor` и `Reviewer` нельзя
утверждать, что:

- `Editor` понимает последствие без открытия внешней GIS;
- risk tiering снижает review friction;
- `High/Critical` routing совпадает с экспертными решениями;
- consequence-first explanation предотвращает unsafe post;
- безопасные конфликты можно уверенно переводить в audit/sample review.

Остается открытым `FU-2026-06-14-001`: проверить planned модель Release 2 с
реальными участниками ролей.

## Связи

- [[../decisions/conflict_resolution_routing]]
- [[../decisions/release_2_conflict_explanation]]
- [[../decisions/risk_assumption_log]]
- [[../decisions/followups/index]]
