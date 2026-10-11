---
title: Исследование сохранения и восстановления от лица заказчика
type: session
status: needs-review
created: 2026-10-11
updated: 2026-10-11
source: RAW_inputs/research_results/2026-10-11-utility-gis-editor-save-recovery-research.md
tags: [research, source-summary, editing, recovery]
---

# Исследование Сохранения И Восстановления От Лица Заказчика

Последующее решение: пользователь 2026-10-12 принял правила этого исследования; основание — [запись решения](../../docs/sprint_2/2026-10-12-save-recovery-rules-decision.md). Канонические политики переведены в active, конфликт observer/operation разрешён; выполнение оформлено отдельно в S2-X01. Ниже сохранён контекст первоначального ingest и его уровень доказательности. Само исследование не стало реальным интервью; организационные входы остаются открыты.

## Контекст

Пользователь запросил интернет-исследование на основе `UtilityGisEditorRole.md`, ответы на 15 discovery-вопросов с позиции заказчика, сохранение нового RAW и ingest. Источник содержит девять прямых первичных ссылок с датой обращения. Это AI-синтез предложений, не реальное интервью и не утверждение policy организации.

## Трассировка Ответов

| Ответы | Каноническое знание |
| --- | --- |
| 1–2: нулевые сегменты, исходные дефекты | [[Wiki/policies/geometry_quality_escalation_policy]] |
| 3–5: сравнение состояний, no-op, непроверенное качество | [[Wiki/glossary/editing_result_states]], [[Wiki/policies/positional_accuracy_acceptance_policy]] |
| 6–12: навигация, stale, неизвестный исход, поздний ответ, доступ, Revert | [[Wiki/policies/editor_recovery_policy]], [[DDD_Wiki/state_machines/editor_save_recovery]] |
| 13: отсутствие текущих правок не равно проверенному качеству | [[Wiki/glossary/editing_result_states]] |
| 14: specification и ответственность за точность | [[Wiki/policies/positional_accuracy_acceptance_policy]]; реальные документ и допуск не установлены |
| 15: records governance | [[Wiki/policies/change_history_retention_policy]]; конкретный срок не установлен |

## Решения И Уверенность

Принятых заказчиком новых domain decisions этот источник не содержит. Внешние факты относятся к названным продуктам; предложенные правила GeoService перенесены как `needs-review`, confidence medium. Scope первой правки, fixture, numeric tolerance и records срок исследованием не переопределяются.

## Конфликты И Follow-up

- [[Wiki/conflicts/2026-10-11-save-outcome-observer-vs-operation]]: согласовать observer uncertainty и operation state; конфликт открыт.
- `FU-2026-10-11-002`: принять либо уточнить предложения 1–13, включая D5-Q1, восстановление и передачу дефектов.
- `FU-2026-10-11-003`: получить реальные specification, допуск, владельцев ответственности и records policy; дополнение к открытому `FU-2026-07-25-001`.
- Ранее отмеченное отставание `Code_wiki` и model health не исправлялось автоматически; repository-change ingest остаётся отдельной работой.
