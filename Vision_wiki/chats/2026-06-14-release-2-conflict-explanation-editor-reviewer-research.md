---
title: Исследование Release 2 Conflict Explanation Для Editor И Reviewer
type: chat
status: active
created: 2026-06-14
updated: 2026-06-14
source: RAW_inputs/meetings/release2_conflict_explanation_editor_reviewer_answers.md
tags: [trusted-source, research, release-2, conflict-explanation, editor, reviewer]
---

# Исследование Release 2 Conflict Explanation Для Editor И Reviewer

## Контекст Источника

Источник содержит подготовленные ответы от имени `Utility GIS editor` и
`Reviewer` на live-вопросы о `Conflict explanation` для Release 2. Ответы
синтезированы на основе проектного research и доменной проверки
`ArcGIS Enterprise / Utility Network`.

Файл принят как доверенный design/research input, но не является транскриптом
интервью с реальными представителями ролей. Указанные внешние ссылки в рамках
этого ingest отдельно не перепроверялись.

## Общая Модель

Обе роли считают `Base / Mine / Default` недостаточным объяснением. Карточка
конфликта должна связывать:

- geometry diff и association diff;
- validation, dirty areas и network errors;
- trace before/after и affected service/subnetwork;
- work order, field evidence, автора и время изменений;
- risk tier с человекочитаемой причиной;
- proposed resolution, альтернативы и post blockers;
- audit, stale approval и повторный review после изменения данных.

Первый экран отвечает на три вопроса: что произошло, чем это опасно для сети и
что делать дальше. Таблицы атрибутов, raw logs, JSON trace и полный audit
скрываются в деталях.

## Editor

- `Editor` может самостоятельно разрешать локальные `Simple/Normal` случаи,
  когда associations, endpoints, trace, service и subnetwork не меняются,
  validation clean, а work order однозначно подтверждает решение.
- Association change, неожиданный trace impact, update-delete, error dirty area
  или противоречивое evidence требуют review, manual edit либо профильного
  специалиста.
- Recommendation остается подсказкой, а не решением. При неполных validation,
  trace или evidence система не должна выглядеть уверенной.
- Любое изменение geometry, association, network attribute, terminal
  configuration или `Default` делает explanation и approval устаревшими.

## Reviewer

- `Reviewer` проверяет не выбор автора сам по себе, а доказанность безопасного
  authoritative state: соответствие work order/evidence, validation, trace и
  affected service.
- Для `High/Critical` обязательны explanation, evidence и audit; для
  `Critical` дополнительно нужны профильный специалист, explicit post approval
  и при аварийном post correction/rollback plan.
- `Reviewer` может изменить простой non-network resolution, но не должен
  становиться скрытым Editor для geometry + association или trace-impact cases.
- Пакетный review допустим для однотипных `Simple/Normal` случаев без network
  impact. Association, trace, service, safety и `High/Critical` проверяются
  по одному.

## Риск И Доверие

Источник предлагает минимум `High` при association diff или trace change и
`Critical` при affected service/customers, safety/isolation impact, network
rule violation либо subnetwork error. Это расходится с существующим planned
routing, где любое изменение trace уже определено как `Critical`.

Расхождение зафиксировано в
[[../decisions/conflicts/2026-06-14-trace-risk-tier-boundary]] и не разрешено
автоматически.

Главные причины потери доверия: скрытые dirty areas или trace impact,
необъясненный risk tier, recommendation без evidence, неверный affected service
и approval, который не становится stale после изменения данных.

## Follow-up

- Проверить модель с реальными `Editor` и `Reviewer`.
- До реализации согласовать точную границу `High/Critical` для trace change.
- Не менять текущий Release 1: источник относится только к Release 2.

## Связи

- [[../decisions/release_2_conflict_explanation]]
- [[../decisions/conflict_resolution_routing]]
- [[../decisions/risk_assumption_log]]
- [[../decisions/followups/index]]
