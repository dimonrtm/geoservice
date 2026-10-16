---
title: Исследование Utility GIS editor и пограничных случаев восстановления
type: session
status: active
created: 2026-10-16
updated: 2026-10-16
source: RAW_inputs/research_results/2026-10-16-utility-gis-editor-recovery-use-case-research.md
tags: [research, recovery, simulated-organization, ingest]
---

# Исследование Utility GIS editor и пограничных случаев восстановления

Пользователь запросил исследование `UtilityGisEditorRole.md`, ответы на 15 вопросов текущего discovery в манере `02_expert_oldman_ufa`, сохранение и ingest. Источник синтетический; роль эксперта не означает реального интервью. Решения приняты агентом за условную организацию в действующем режиме.

## Что проверено

Семь первичных веб-источников описывают конкретные workflow Esri, QFieldCloud, GISwater, границы sessionStorage и безопасные повторы. В исходном отчёте не восстановлены ссылки `turn…`, не подтверждены доли рынка, частота проблем и отдельные исторические кейсы. Эти утверждения не перенесены в каноническую модель как факты. Точные URL и пределы доказательств находятся в RAW, раздел 2.

## Решения и связи

| Ответы | Уточнение | Каноническое место |
| --- | --- | --- |
| 1–4 | Подтверждение восстановления не равно новому изменению; полномочия текущие; квитанция отдельно от current | [[Wiki/policies/editor_recovery_policy]], [[Wiki/specifications/editing_resumption_allowed]] |
| 5–8 | Один наряд редактируется в одном окне учебной сессии; сравнение local source/candidate/current; поздний ответ исторический | [[Wiki/policies/editor_recovery_policy]], [[Wiki/glossary/editing_result_states]] |
| 9–11 | No-op не выполняет задание автоматически; отсутствие записи не доказывает отказ; передумать не значит отменить отправку | [[Wiki/policies/editor_recovery_policy]], [[Wiki/policies/recovery_case_resolution_policy]] |
| 12–15 | Независимый переход только при сохранности recovery; принудительный выход; актуальность Revert consent; закрытие разбора без возобновления | [[DDD_Wiki/use_cases/interrupted_edit_work_recovery]], [[DDD_Wiki/state_machines/editor_save_recovery]] |

## Расхождения и остаток

Новых blocking domain conflicts нет: правила уточняют действующие ограничения и не вводят распределённую блокировку или автоматический merge. Утверждение прежнего технического summary об отсутствии refresh flow слишком широко: recovery вызывается из store-путей открытия/восстановления workspace. Уточнение связано с уже зарегистрированным FU-2026-10-11-001.

S2-X01 и FU-2026-10-13-004 остаются открытыми: UI, явное продолжение после access block, Revert и сценарная приёмка не доказываются исследованием. Новый RAW содержит матрицу сценариев без заявления об их успешном прогоне. Метрики эффекта — гипотезы; старый RAW неизменен.
