---
title: Решения условной организации по 15 вопросам Utility GIS editor
type: session
status: active
created: 2026-10-13
updated: 2026-10-13
source: RAW_inputs/research_results/2026-10-13-utility-gis-editor-simulated-organization-decisions.md
tags: [simulated-organization, discovery, ingest]
---

# Решения условной организации по 15 вопросам Utility GIS editor

## Контекст

Пользователь поручил пересмотреть ответы через `02_expert_oldman_ufa` и самостоятельно принять решения за условную организацию. Это синтетический экспертный источник, не интервью. Рабочие правила приняты в рамках данного делегирования; active означает решение модели, не завершённую реализацию.

## Ключевые решения

| Ответы | Решение | Каноническая нода |
| --- | --- | --- |
| 1–4 | Один безопасный цикл/5 минут; реакция 15 минут, классификация 60; явная передача; durable outcome отдельно от current | [[Wiki/policies/recovery_case_resolution_policy]] |
| 5–8 | Функциональные обязанности агента, dependency scope, immutable baseline, доказательное разрешение; новый контекст без автоматического переноса | [[Wiki/policies/geometry_quality_escalation_policy]], [[DDD_Wiki/use_cases/interrupted_edit_work_recovery]] |
| 9–12 | SIM-UGIS-POS-001 v1.0: 0,50 м, max(e+u), u<=0,10; отдельный аналитический эталон, полный охват, событийная переоценка | [[Wiki/specifications/simulated_line_positional_acceptance]], [[Wiki/policies/positional_accuracy_acceptance_policy]] |
| 13 | Основание в задании; исключения объясняются до review, без нового Save hard guard | [[Wiki/policies/edit_change_justification_policy]] |
| 14–15 | SIM-UGIS-RET-001 v1.0: история/архив registry 10 лет после закрытия версии, карточки 3 года после закрытия, debug 30 дней; удержания и зависимости | [[Wiki/policies/change_history_retention_policy]] |

Сроки действуют как проектный выбор; 5/15/60 минут отсчитываются в активном учебном сценарии. Внешние источники подтверждают технические основания, не наши числа. SIM-EVID-001 — аналитическая синтетическая линия, не L-003 и не полевой замер. Существующий first-save остаётся UNVERIFIED; аналитический pass сам по себе не снимает downstream gates.

## Источники

Пять первичных документов повторно проверены: AWS idempotency, Esri dirty areas, QFieldCloud Jobs, NIST AU-3/AU-11 и PostGIS ST_Distance. Прямые URL и границы использования находятся в [[RAW_inputs/research_results/2026-10-13-utility-gis-editor-simulated-organization-decisions]].

## Конфликты и follow-up

[[Wiki/conflicts/2026-10-13-real-organization-vs-simulated-decisions]] разрешает прежнее ожидание реального предприятия. FU-2026-10-11-003 и три follow-up принятия от 2026-10-13 закрыты для модели. FU-2026-10-13-004 сохраняет реализацию evaluator, recovery/restart, хранения и доступа как отдельную работу. Код и текущая fixture не меняются. Прежние источники не переписаны.

## Проверка модели

В RAW заданы девять сценариев. Аналитический pass 0,35 м и fail 0,65 м воспроизводимы; это не тестирование приложения. Недостаток evidence должен давать unverified. Два старых вопроса metadata/fixture остаются очередью сверки с существующим кодом, а не запросами к несуществующей организации.
