---
title: Utility GIS Editor Target Times
type: session
status: draft
created: 2026-06-06
updated: 2026-06-06
source: RAW_inputs/documents/utility_gis_editor_target_times.md
tags: [performance, nfr, utility-gis-editor, acceptance-criteria]
---

# Utility GIS Editor Target Times

## Контекст

Источник предлагает измеримые SLO и acceptance thresholds для пользовательского контура `Utility GIS editor` на малом synthetic utility dataset. Пороги являются рабочими целями для demo и должны быть подтверждены benchmark на reference hardware из Ф6.

## P95 Acceptance Targets

| Операция | P95 |
|---|---:|
| Map load до пригодного к работе AOI | <= 5 сек |
| Переход к объекту / AOI | <= 2 сек |
| Сохранение одного edit | <= 2 сек |
| Сохранение 5-20 edits | <= 5 сек |
| Validation рабочего AOI | <= 15 сек |
| Reconcile без конфликтов | <= 10 сек |
| Reconcile до списка конфликтов | <= 20 сек |
| Открытие conflict diff | <= 5 сек |
| Post в `Default` | <= 15 сек |
| Отказ post при stale `Default` | <= 5 сек |

## Семантика Измерений

- Map считается пригодной к работе, когда виден AOI и основные utility-объекты, объект можно выбрать, а secondary layers могут продолжать lazy loading.
- Save подтверждает запись в working version и не маскирует отсутствие validation/reconcile/post.
- Reconcile с конфликтами измеряется до появления списка конфликтов, а не до их ручного разрешения.
- Stale post должен быстро завершиться контролируемой ошибкой, объяснить изменение `Default`, потребовать повторный reconcile и сохранить edits пользователя.
- Безопасность authoritative state важнее минимальной задержки: операции должны быть предсказуемыми, объяснимыми и не допускать silent overwrite.

## Статус

Пороги приняты как draft acceptance targets из RAW source. Их нужно проверить на `synthetic_utility_feeder_01`, Chrome и reference hardware Asus TUF Gaming 2022, AMD Ryzen 7 5000 series, 16 GB RAM.

## Связи

- [[../solution/nfr]]
- [[2026-06-06-phase-f6-constraints-and-nfr]]
- [[2026-06-05-utility-gis-editor-walking-skeleton-and-dataset]]
- [[../decisions/risk_assumption_log]]
- [[../decisions/followups/index]]
