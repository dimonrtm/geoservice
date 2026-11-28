---
title: "Редакция проекта строительства и фактическая съёмка"
type: concept
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/UtilityGisEditor.md"
tags: [domain-knowledge, utility-gis, as-built]
confidence: inferred
related: [Wiki/entities/network_project, Wiki/entities/edit_version, Wiki/entities/asset_attachment, Wiki/specifications/project_revision_applicable, DDD_Wiki/use_cases/as_built_workflow]
---

# Редакция проекта строительства и фактическая съёмка

Проектировщик передаёт подрядчику согласованную трассу. После строительства поле возвращает фактическую съёмку. Редактор использует эти материалы для двух разных выводов. Съёмка показывает, где построен участок, а выданная редакция чертежа и утверждённые изменения позволяют оценить его соответствие проекту. [[Wiki/entities/edit_version|Рабочая версия сети]] содержит правки ГИС, подготовленные для проверки и публикации. Её место в [[Wiki/entities/network_project|проекте ГИС]] определено исходной ER-диаграммой. [Проектирование и as-built](../../RAW_inputs/documents/UtilityGisEditor.md#базовые-и-продвинутые-workflows) · [Концептуальная диаграмма](../../RAW_inputs/documents/UtilityGisEditor.md#бизнес-модели-и-метрики-успеха).

По решению GeoService редактор сохраняет для участка съёмку, выданную для работ редакцию и ссылку на согласованное изменение. Для оценки соответствия применяется последнее утверждённое изменение, которое явно охватывает эту часть и выполненные работы. Например, если распоряжение меняет трассу только за пределами уложенного участка, то факт выпуска нового листа не меняет основание сверки уложенной части. Это условный пример применения правила. [NET-11](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-11) · [Условие применимости редакции](../specifications/project_revision_applicable.md).

Если область действия позднего распоряжения спорна, измеренную геометрию сохраняют, а заключение о соответствии оставляют открытым. Кто вправе разрешить такой ретроспективный спор, остаётся вопросом NET-11. Отдельно проверяют [[Wiki/specifications/surveyed_part_publishable|возможность публикации измеренной части]] и её рабочее подключение. [Решение и граница вывода по NET-11](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-11) · [NET-09](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-09).
