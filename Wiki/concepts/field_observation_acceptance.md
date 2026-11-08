---
title: Принятие полевого свидетельства
type: concept
status: active
created: 2026-10-18
updated: 2026-11-08
source: "RAW_inputs/research_results/2026-10-18-utility-gis-editor-domain-knowledge-analysis.md; RAW_inputs/research_results/2026-10-19-utility-gis-editor-change-basis-research.md; RAW_inputs/research_results/2026-11-08-utility-gis-editor-verification-research.md"
tags: [domain-knowledge, research, simulated-organization]
confidence: high
related: [Wiki/policies/edit_change_justification_policy, Wiki/specifications/saved_line_quality_assessment]
---

# Принятие полевого свидетельства

## Определение

Полевое свидетельство — сведения наблюдения с происхождением, временем, областью и ограничениями. Принятие — решение использовать конкретные утверждения свидетельства в определённом контексте. Оно может охватывать часть материала и не тождественно доставке файла или техническому Save.

## Внешние основания

USX допускает принятие всей съёмки, части либо отказ; `Adopted` относится к организации. Watercare различает site verification и детализацию модели. Это практика конкретных источников, не универсальный стандарт. [D25 — UKPN / USX — Final Report, issue 1.2](https://d1oyzg0jo3ox9g.cloudfront.net/app/uploads/2023/10/USX-UKPN-00007_UtilitySurveyExchange_FinalReport_1_2_FOR_SHARING.pdf) [D05 — Watercare — As-Built 3D Model Specification](https://assets.watercare.co.nz/media/as_built_3d_model_specification_2cef742361.pdf)

## Решение условной организации

В ручной карточке основания различать исходное наблюдение, преобразование, принятое утверждение и оставшиеся сомнения. Указывать объект, область, источник, время, основание решения и ограничения. Сведения о геодезической основе не заменяются видом карты. Свежесть источника не даёт ему автоматического приоритета.

Авторитетность относится к категории сведений: документы, геометрия, учёт и operational history могут иметь разные источники, связанные устойчивым идентификатором. [D03 — Watercare — Asset Information and Data Standard](https://assets.watercare.co.nz/media/ai_asset_information_and_data_standard_november_2020_b0f0de2baa.pdf) [D19 — Sydney Water — WAC plans submission checklist](https://www.sydneywater.com.au/content/dam/sydneywater/documents/wsc-documents/submission-requirements-for-wac-plans-checklist.pdf)

Пример: подтверждённая глубина в точке вскрытия не подтверждает весь изгиб трубы. Ручная правка после GNSS сохраняет источник, но требует переоценки применимости его accuracy к результату. Ни provenance, ни валидность файла сами по себе не удостоверяют истинность.

## Границы

Это уточнение содержания существующей карточки и оценки, не новый aggregate, статус API или роль. Будущий lifecycle наблюдения остаётся гипотезой; общие обязанности уже заданы в [[Wiki/policies/edit_change_justification_policy]] и [[Wiki/specifications/saved_line_quality_assessment]]. Исправление сомнительного baseline — [[Wiki/policies/geometry_quality_escalation_policy]].

## Происхождение и пересмотр принятия

[[Wiki/concepts/evidence_dependency]] уточняет зависимость копий и область независимости. [[Wiki/concepts/change_basis_lifecycle]] отделяет время наблюдения, редакцию основания и историю решений. Принятие части материала фиксируется по точному фрагменту, свойству и участку; непроверенное отличается от отклонённого. Новые правила не объявляют весь файл принятым.

## Метод и охват утверждения — 2026-11-08

Свидетельство уточняется по проверяемому свойству: наличие объекта, XY, высота, материал и связность не получают общий verified автоматически. Метод, источник/редакция, время и охват относятся к конкретному утверждению. Визуальная проверка и инструментальное обследование дают различные основания; имя метода само не доказывает достаточность для цели.

Ручная матрица охвата связывает объекты/участки, свойства, наблюдаемое состояние и выполненные проверки. AOI задания, survey extent и область проверки различаются. «Не проверено», «проверено и не соответствует», «не найдено в выдаче» и обоснованная неприменимость не смешиваются; отсутствие записи не удостоверяет отсутствие физического объекта.

Внешние основания: Watercare R59, Water Corporation R60, Ohio DNR R61, Philadelphia R65 и Giswater R78 в [[RAW_inputs/research_results/2026-11-08-utility-gis-editor-verification-research]]. Это уточнение принятой модели условной организации, не новая классификация API. Численные допуски владельцев не перенесены в GeoService.
