---
title: Risk-Tiered Routing Для Следующего Релиза
type: decision
status: planned
created: 2026-06-14
updated: 2026-06-17
source: "RAW_inputs/meetings/utility_gis_editor_geometry_association_conflict_answers.md; user clarification on source trust, 2026-06-14; RAW_inputs/meetings/Reviwer Decision.md; RAW_inputs/meetings/geometry_association_conflict_f1.md"
tags: [decision, next-release, conflict-resolution, routing, risk, editor, reviewer]
---

# Risk-Tiered Routing Для Следующего Релиза

## Контекст

Release 1 требует объяснимого `geometry/association conflict`, но назначает
решение преимущественно `Reviewer`. Доверенный research source следующего
релиза показывает, что единый маршрут для всех конфликтов создаст лишнее
согласование простых случаев и недостаточно учитывает сетевое последствие.

Текущий Release 1 не меняется. Решение ниже является planned scope следующего
релиза.

Новый F1 research/design input уточняет why-now для `geometry/association
conflict`: `Editor` должен понять, меняет ли конфликт только картинку или
authoritative network behavior. Обычный feature diff, `Base / Mine / Default` и
geometry comparison показывают representation, но не дают достаточного ответа
про connectivity, containment, attachment/locatability, trace и subnetwork
state.

## Решение

В следующем релизе использовать risk-tiered routing:

- `Simple`: `Editor` решает самостоятельно при отсутствии network impact,
  clean validation и неизменившемся trace; обязательная эскалация не нужна.
- `Normal`: `Editor` решает с audit note; допускается sample review, если
  conflict остается на уровне representation и не меняет сетевую семантику
  после validation: нет изменения association type, terminal/connectivity
  semantics, новых error dirty areas, control trace не меняется, а subnetwork
  state не становится inconsistent за пределами expected edit envelope.
- `High`: `Editor` предлагает решение, `Reviewer` принимает решение после
  проверки diff, validation, trace и evidence; это финальное решение по
  содержанию пакета, а не простое подтверждение proposal; SLA до 2 рабочих
  часов. `High` включает важные изменения сетевой интерпретации без
  критического operational/safety state: изменение connectivity association,
  containment/attachment hierarchy с влиянием на locatability, visibility или
  trace inclusion, bounded delta в control trace, dirty areas в affected
  segment, требующие validate/update subnetwork.
- `Critical`: `Editor`, `Reviewer` и профильный специалист участвуют в
  совместном решении; профильный специалист или utility-network admin
  подключается сразу, включая дежурный канал для аварийной коррекции.
- При сохраняющемся разногласии окончательное решение принимает владелец
  authoritative data.
- `post` блокируется до получения всех требуемых подтверждений и актуального
  технического gate против текущего `Default`.
- Любое изменение согласованных данных аннулирует подтверждения.
- Назначение ответственного определяется affected network area, типом изменения,
  компетенцией и risk tier. Авторство является вспомогательным сигналом, а не
  главным правилом routing.

`Critical` означает не любой trace delta, а только такое изменение, которое
меняет service/subnetwork/safety semantics или authoritative operational state:
affected service, subnetwork, controllers, barriers, isolation, flow direction,
downstream assets, traversability, rule-dependent connectivity,
switching/outage/safety decisions или другие operational outputs. Trace delta
без service/subnetwork/safety semantics и без rule/terminal/controller impact
может оставаться `High`.

## Альтернативы

| Альтернатива | Почему Не Выбрана |
|---|---|
| Совместное решение для всех конфликтов | Создает очередь и задержки для простых случаев без сетевого последствия |
| Единоличное решение `Reviewer` | Недостаточно учитывает авторство изменения и инженерный контекст |
| Назначение только по авторству | Автором может быть import/script/недоступный пользователь; авторство не гарантирует компетенцию по affected network area |
| Немедленная передача владельцу authoritative data | Перегружает владельца и исключает рабочее согласование ролей |

## Последствия

- Conflict model требует уровня риска, текущего ответственного, срока и истории
  эскалации.
- Conflict view должен показывать geometry/association diff, validation и trace
  impact до решения.
- Все решения требуют причины и сохраняются в audit.
- Workflow должен поддерживать совместное подтверждение и окончательное решение
  владельца authoritative data.
- Роли профильного специалиста и владельца authoritative data требуют
  отдельного implementation contract.
- `Reviewer decision` относится к approval of change package for post readiness;
  `approve package` и `post authorization` остаются разными шагами.
- Stale approval требует repeat review в режиме delta-first with anchored
  baseline.
- Модель принята как planned design следующего релиза на основании доверенного
  research source и нового design/architecture input; реальная применимость
  требует user validation.
- Более дорогая ошибка для routing - пропустить реальный network impact, чем
  переэскалировать безопасный conflict. Сигнал переусложнения: explanation
  дублирует Conflicts view, `High/Critical` не меняет routing или synthetic
  scenarios не сокращают время до уверенного решения.
- Текущий Release 1 и его `Reviewer approval` contract остаются без изменений.

## Связи

- [[../chats/2026-06-14-utility-gis-editor-conflict-routing-synthetic-research]]
- [[../chats/2026-06-16-release-2-reviewer-decision]]
- [[../chats/2026-06-17-geometry-association-conflict-f1]]
- [[../chats/2026-06-14-geometry-association-conflict-resolution-workshop]]
- [[conflicts/2026-06-14-next-release-conflict-routing-responsibility]]
- [[../solution/USM]]
- [[risk_assumption_log]]
- [[followups/index]]
