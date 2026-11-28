---
title: "Данные инженерной сети и их связи"
type: concept
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/UtilityGisEditor.md"
tags: [domain-knowledge, utility-gis]
confidence: inferred
related: [Wiki/entities/network_project, Wiki/entities/network_feature, Wiki/entities/network_association, Wiki/entities/edit_version, Wiki/entities/work_order, Wiki/entities/inspection, Wiki/entities/asset_attachment]
---

# Данные инженерной сети и их связи

| Группа данных | Что связано и зачем |
| --- | --- |
| Пространственные активы | [Проект ГИС объединяет слои](../entities/network_project.md). В слое хранятся [активы](../entities/network_feature.md) заданных инженерных типов. Геометрия указывает, где находится объект. |
| Сетевая топология | Актив может представлять [узел или ребро](../entities/network_association.md). Ребро соединяет начальный и конечный узлы. Направление, режим, отключающие устройства и допустимые связи нужны для определения охвата работ. |
| Эксплуатационные данные | Актив связан с [осмотрами](../entities/inspection.md) и [позициями наряда](../entities/work_order.md). Инцидент, отключение и состояние работ задают эксплуатационный контекст. |
| Документальные данные | С активом соотносятся [вложения](../entities/asset_attachment.md), в том числе фотографии, паспорта, чертежи и акты. Они позволяют сопоставить запись на карте с полевым или исполнительным материалом. |

В ER-диаграмме источника [[Wiki/actors/organization_and_access|организация объединяет пользователей и владеет проектами, пользователю назначена роль]]. Проект содержит [[Wiki/entities/edit_version|версии сети]]. [[Wiki/entities/edit_event|Запись действия]] указывает версию и пользователя. Проект также инициирует [[Wiki/entities/integration_job|задание обмена]] с внешней системой. [Исходная ER-диаграмма](../../RAW_inputs/documents/UtilityGisEditor.md#бизнес-модели-и-метрики-успеха).

[UtilityGisEditor.md · Данные, форматы и интеграции](../../RAW_inputs/documents/UtilityGisEditor.md#данные-форматы-и-интеграции)

## Как связаны наблюдение, актив и состояние сети

До опознания [[Wiki/entities/field_observation|наблюдение]] связано с нарядом и возможными активами. После опознания его используют в пределах обследованного участка и установленного свойства. Геометрия, физическое соединение и ввод построенного участка могут иметь разные основания. В оперативном расчёте дополнительно учитывают положение устройств на нужный момент. [NET-07](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-07) · [NET-09](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-09) · [NET-10](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-10) · [NET-13](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-13).
