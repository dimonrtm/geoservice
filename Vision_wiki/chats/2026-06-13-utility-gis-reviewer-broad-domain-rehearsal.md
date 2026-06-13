---
title: Расширенная Доменная Репетиция Utility GIS Reviewer
type: chat
status: active
created: 2026-06-13
updated: 2026-06-13
source: RAW_inputs/meetings/utility_gis_reviewer_broad_domain_answers.md
tags: [synthetic, reviewer, broad-domain, review-package, network-model, design-evidence]
---

# Расширенная Доменная Репетиция Utility GIS Reviewer

## Статус Источника

`RAW_inputs/meetings/utility_gis_reviewer_broad_domain_answers.md` содержит
расширенные смоделированные ответы от имени `Reviewer`, а не транскрипт
реального интервью. Внешние ссылки формируют source-derived domain context, но
не считаются перепроверенными этим ingest.

## Новые Доменныe Уточнения

- Reviewer является контрольным слоем между field reality, engineering
  documents, GIS network model и operational systems.
- Проверка должна разделять geometry, attributes и logical
  connectivity/associations.
- Автоматический QA/QC является фильтром, но не заменяет инженерное суждение.
- Для connectivity changes нужен набор контрольных trace-сценариев.
- Review package должен связывать diff, validation, topology, trace,
  documents, photos, conflicts, comments и audit.
- Risk-based routing может требовать domain specialist или senior reviewer.
- Для критичных изменений publisher responsibility может быть отделена от
  reviewer decision.

## Критерий Решения

Хороший review отвечает не только на вопрос «есть ли формальные ошибки», но и
на вопрос «безопасно ли публиковать это состояние как authoritative».

Решение требует:

- понятного physical и logical diff;
- подтверждения field/as-built evidence;
- отсутствия unresolved conflicts и critical validation issues;
- актуальных topology и trace results;
- закрытых review comments;
- неизмененного change set после review;
- понятного downstream impact.

## Главная Боль

Review превращается в ручную реконструкцию реальности: что построили, что
планировали, что внес editor, что подтверждают документы и какое состояние
увидят downstream consumers.

## Конфликты С Текущим Design

Источник усиливает уже открытый `FU-2026-06-13-002`:

- общая очередь может быть недостаточна для risk/domain-specific review;
- reviewer может только разрешать публикацию, а `post` выполняет отдельный
  publisher;
- low-risk changes могут использовать иной separation-of-duties policy.

До external validation строгий Release 1 contract не меняется.

## Границы Подтверждения

- Multi-utility applicability остается гипотезой.
- Реальные review checklist, routing и publisher roles не подтверждены.
- Source URLs требуют отдельной live-проверки перед публичными claims.

## Связи

- [[2026-06-13-utility-gis-reviewer-synthetic-interview-rehearsal]]
- [[../entities/personas/utility_gis_reviewer]]
- [[../concepts/utility_gis_editing_domain]]
- [[../concepts/jtbd]]
- [[../decisions/risk_assumption_log]]
- [[../decisions/followups/index]]
- [[../solution/USM]]
