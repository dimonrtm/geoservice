---
title: "Учесть эксплуатационное ограничение актива"
type: command
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/2026-11-27-field-information-answers.md"
tags: [domain-knowledge, utility-gis, field-evidence]
confidence: inferred
related: [DDD_Wiki/aggregates/network_asset, Wiki/specifications/operational_restriction_evidenced, Wiki/domain_events/operational_restriction_established]
---

# Учесть эксплуатационное ограничение актива

## Actor

ГИС-редактор, получивший подтверждение от эксплуатации или проверяющий фактическое отключение.

## Target

Доступность опознанного актива или его части в [[DDD_Wiki/aggregates/network_asset|записи актива]].

## Preconditions

Установлены затронутая часть, характер ограничения, дата или время и источник.

## Outcome

Редактор учитывает установленное ограничение, отказ, временное отключение или постоянный вывод в пределах установленного действия. По одному осмотру редактор записывает дефект и передаёт его эксплуатации. При списании найденного насоса регистрирует расхождение. Постоянное исключение допустимо при подтверждённом выводе либо проверенном фактическом отключении с известными характером и датой. При неизвестном характере отключения доступность остаётся неопределённой. Физическая запись и история насоса сохраняются, пока он находится на месте. [[Wiki/specifications/operational_restriction_evidenced|Проверка основания ограничения]].

Решения условной организации через `expert_repson`. [NET-08](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-08) · [NET-16](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-16) · [Офисная, полевая и оперативная работа с сетью](../../RAW_inputs/documents/UtilityGisEditor.md#базовые-и-продвинутые-workflows).
