---
title: Съёмка, трассировка и редакторская версия в материалах Melbourne Water и Esri
type: source-summary
status: active
created: 2026-11-24
updated: 2026-11-24
source: "RAW_inputs/docs/241126.txt"
tags: [utility-gis, field-observation, trace, edit-version]
---

# Съёмка, трассировка и редакторская версия в материалах Melbourne Water и Esri

[Текстовая подборка](../../RAW_inputs/docs/241126.txt) содержит русские фрагменты трёх публикаций. Английские оригиналы соответствуют позициям 6–8 в [реестре источников](../../docs/sources/utility-gis-editor-use-case.md).

| Часть исходника | Что описывает автор | Что это даёт GeoService |
| --- | --- | --- |
| Строки 1–113, Melbourne Water | В §§7.9 и 7.20 различаются исполнительные привязки, исходные измеренные координаты и размещение в ГИС относительно кадастровой основы. [Руководство оператора](https://www.melbournewater.com.au/building-and-works/developer-guides-and-resources/standards-and-specifications/surveying). | Подтверждает действующее правило указывать назначение геометрии и происхождение измерения. |
| Строки 115–255, Esri | При остановке внутри трубы итог по полным длинам записей меняется в зависимости от включения пограничной трубы. Для проверки фактически пройденной части предусмотрен результат с частичной геометрией. [Barriers, раздел Function barriers](https://doc.esri.com/en/arcgis-pro/latest/help/data/utility-network/barriers.html). | Уточнён разбор количественного утверждения в пакете. Проверяющему нужны место остановки и способ учёта последней трубы. [[Wiki/concepts/network_representation_and_operational_state#Длина при остановке внутри линии]], [[DDD_Wiki/use_cases/utility_editor_workflow]]. |
| Строки 256–326, Esri | Учебный шаблон создаёт версию для задания, отправляет изменения без конфликтов в Default и передаёт конфликты на разбор. [Сценарий Workflow Manager](https://www.esri.com/arcgis-blog/products/web-editor/data-management/orchestrating-utility-network-editing-workflows-with-arcgis-workflow-manager-and-arcgis-web-editor). | Иллюстрирует связь наряда с рабочей версией. Выбор GeoService о содержательном одобрении и вычислении допуска определяется [[Wiki/policies/reviewer_post_policy]]. |

Область решения условной организации — интерпретация результата при review. Обязательность трассировки определяется предметом проверки. Различие с учебным шаблоном Esri объясняется политикой GeoService.
