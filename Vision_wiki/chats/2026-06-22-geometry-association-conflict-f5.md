---
title: Geometry/Association Conflict Бизнес-Модель И Внедрение
type: session
status: active
created: 2026-06-22
updated: 2026-06-22
source: RAW_inputs/meetings/geometry_association_conflict_f5.md
tags: [discovery, phase-f5, release-2, geometry-association-conflict, rollout, implementation-contract]
---

# Geometry/Association Conflict Бизнес-Модель И Внедрение

## Контекст

Ф5 уточняет внедрение и business/rollout-модель для Release 2
`geometry/association conflict` после Ф1-Ф4. В отличие от коммерческого
go-to-market, текущий rollout остается внутренним developer demo: decision
maker, первый пользователь и budget owner совпадают в роли `разработчик demo`.

Источник - research/design input о rollout/value для Release 2, дополненный
короткими ответами владельца проекта. Это не direct user interview с `Editor`,
`Reviewer` или enterprise buyer и не vendor due diligence. Поэтому Ф5 не
создает внешние product claims и не меняет текущий Release 1.

## Ответы Ф5

| Вопрос | Ответ |
|---|---|
| Кто принимает решение, что Release 2 demo достаточно ценен для продолжения? | `разработчик demo` |
| Какая польза должна быть видна без денег? | Сократить внешние проверки и ускорить уверенное go/no-go решение; audit quality важен как второй эффект; снижение unsafe/stale post risk остается гипотезой, а не публичным claim. |
| Кто первый пользователь rollout? | `разработчик demo` |
| Где feature должна появиться в workflow? | Сразу после reconcile и до review/post как decision package, а не как отдельный dashboard. |
| Какие роли нужны для эксплуатации? | `Utility-network admin`/`GIS lead` для rules/version policy, `Reviewer`/QA для risk tier и review decision, владелец authoritative data/version administrator для audit object и final post authority. |
| Какие интеграции обязательны? | Associations, dirty areas, validation, trace/subnetwork, work order context; field evidence достаточно как synthetic attachment/reference в первом demo. |
| Что не входит в первый rollout? | Замена native conflict editor, собственный topology engine, live ERP/EAM/OMS/ADMS integration, полноценный mobile/offline stack, batch review queue и SLA orchestration. |
| Самый дорогой риск внедрения | Ложная уверенность: explanation/risk tier расходится с authoritative topology, trace evidence или stale state. |
| Кто может заблокировать внедрение? | `Utility-network admin`/`GIS lead`, владелец authoritative data/operations, затем IT/security. |
| Support package после запуска | Фиксированный demo script, fixtures, troubleshooting по dirty/stale/invalid subnetwork, calibration notes по risk tiers, audit examples, known limitations и negative fixture с blocked post. |
| Допустимые обещания до real validation | "Собирает conflict context в один decision package", "помогает раньше увидеть blockers перед post", "consequence-first review поверх native GIS workflow". |
| Слишком сильные claims до real validation | "Снижает unsafe posts", "ускоряет review на X%", "заменяет ArcGIS Conflicts view", "гарантирует safety of post". |
| Первый rollout-сценарий | Один canonical transformer terminal case как главный demo и stale/pre-post failure sidecar. |
| Если feature станет commercial/on-prem гипотезой, кто будет budget owner? | `разработчик demo` |
| Что после Ф5 должно стать follow-up'ом для Ф6/Ф7? | `implementation contract` |

## Вывод

Release 2 `geometry/association conflict` остается внутренним demo-инкрементом,
а не коммерческим внедрением. Первый критерий движения дальше - готовность
перевести Ф4 scope в implementation contract: state machine, API/events, audit
schema и demo fixtures для consequence package.

Внедренческая гипотеза сужается до developer validation:

- можно ли собрать canonical transformer terminal case в repeatable fixture;
- можно ли показать один сильный terminal-aware conflict и stale/pre-post
  failure sidecar без внешней enterprise GIS-инфраструктуры;
- можно ли сохранить audit object и объяснить safe next step как часть demo;
- достаточно ли implementation contract, чтобы начать следующий engineering
  step без расширения scope до full native conflict editor.

## Rollout Position

Release 2 должен быть встроенным decision-support step после reconcile и до
review/post. Отдельный dashboard имеет смысл позже, когда появится очередь
конфликтов, SLA и routing operations; первый rollout должен доказать, что
decision package сокращает путь к уверенному решению, а не просто добавляет
новый экран.

GeoService выигрывает у baseline только если в одном пакете отвечает на четыре
вопроса:

- что конфликтует;
- какое сетевое поведение может измениться;
- что сейчас мешает safe post;
- какой следующий шаг безопасен.

Если пользователь в demo все равно открывает внешний GIS, trace tool, notes и
устные согласования в том же объеме, значит добавлен экран, а не сокращен путь
к решению.

## Support Package

Для developer demo нужен support package:

- фиксированный demo-сценарий;
- fixtures с ожидаемым исходом;
- troubleshooting по dirty areas, stale reconcile и invalid subnetwork;
- calibration notes по risk tiers;
- примеры audit objects;
- known limitations;
- negative fixture, где decision package блокирует `post`.

## Не Уточнено

- Первый operational audience вне разработчика не выбран.
- Реальная измеримая польза для `Editor`/`Reviewer` не доказана: fewer external
  checks, time-to-confident-decision, audit quality и unsafe/stale risk reduction
  требуют live validation.
- Commercial/on-prem бюджетная модель не выбрана; budget owner пока
  `разработчик demo`.

## Следующий Артефакт

Подготовить `implementation contract` для Release 2 demo:

- state machine для conflict package, review/stale states и safe next steps;
- API/events для загрузки package, risk tier, decision и stale invalidation;
- audit schema для evidence, alternatives, decisions, stale events и post gate;
- demo fixtures для canonical transformer terminal scenario и вариантов
  `Normal / High / Critical / stale`.

## Связи

- [[2026-06-17-geometry-association-conflict-f1]]
- [[2026-06-18-geometry-association-conflict-f2]]
- [[2026-06-19-geometry-association-conflict-f3]]
- [[2026-06-20-geometry-association-conflict-f4]]
- [[../decisions/release_2_conflict_explanation]]
- [[../decisions/conflict_resolution_routing]]
- [[../solution/roadmap]]
- [[../solution/architecture_vision]]
- [[../decisions/risk_assumption_log]]
- [[../decisions/followups/index]]
