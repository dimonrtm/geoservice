---
title: Risk-Tiered Routing Для Следующего Релиза
type: decision
status: planned
created: 2026-06-14
updated: 2026-06-14
source: "RAW_inputs/meetings/utility_gis_editor_geometry_association_conflict_answers.md; user clarification on source trust, 2026-06-14"
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

## Решение

В следующем релизе использовать risk-tiered routing:

- `Simple`: `Editor` решает самостоятельно при отсутствии network impact,
  clean validation и неизменившемся trace; обязательная эскалация не нужна.
- `Normal`: `Editor` решает с audit note; допускается sample review, если
  validation clean, endpoints/associations/trace не изменились.
- `High`: `Editor` предлагает решение, `Reviewer` принимает решение после
  проверки diff, validation, trace и evidence; SLA до 2 рабочих часов.
- `Critical`: `Editor`, `Reviewer` и профильный специалист участвуют в
  совместном решении; профильный специалист подключается сразу, включая
  дежурный канал для аварийной коррекции.
- При сохраняющемся разногласии окончательное решение принимает владелец
  authoritative data.
- `post` блокируется до получения всех требуемых подтверждений.
- Любое изменение согласованных данных аннулирует подтверждения.
- Назначение ответственного определяется affected network area, типом изменения,
  компетенцией и risk tier. Авторство является вспомогательным сигналом, а не
  главным правилом routing.

`Critical` означает нарушение connectivity/topology, изменение trace, потерю
питания/обслуживания или нарушение обязательного network rule.

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
- Модель принята как planned design следующего релиза на основании доверенного
  research source; реальная применимость требует user validation.
- Текущий Release 1 и его `Reviewer approval` contract остаются без изменений.

## Связи

- [[../chats/2026-06-14-utility-gis-editor-conflict-routing-synthetic-research]]
- [[../chats/2026-06-14-geometry-association-conflict-resolution-workshop]]
- [[conflicts/2026-06-14-next-release-conflict-routing-responsibility]]
- [[../solution/USM]]
- [[risk_assumption_log]]
- [[followups/index]]
