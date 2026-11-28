---
title: "Актив инженерной сети"
type: entity
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/UtilityGisEditor.md"
tags: [domain-knowledge, utility-gis]
confidence: inferred
related: [Wiki/entities/network_project, Wiki/entities/network_association, Wiki/entities/work_order, Wiki/entities/inspection, Wiki/entities/asset_attachment, DDD_Wiki/aggregates/network_asset]
---

# Актив инженерной сети

Кабель, труба, опора и задвижка — примеры активов (`ASSET` в исходной диаграмме). Тип актива определяет инженерный смысл объекта. Геометрия и технические атрибуты позволяют редактору описать его положение и свойства. Вложения и результаты осмотров связывают запись с тем, что обнаружено на месте.

В примере диаграммы актив принадлежит [[Wiki/entities/network_project|слою проекта ГИС и имеет инженерный тип]]. Его участие в графе представлено [[Wiki/entities/network_association|узлом или ребром]], а участие в [[Wiki/entities/work_order|наряде]] — позицией работ. [[Wiki/entities/asset_attachment|Вложения]] сохраняют материалы об активе, [[Wiki/entities/inspection|осмотры]] — результаты обследования с их датой и охватом. Детальный справочник типов для конкретной отрасли в документе не выбран.

[UtilityGisEditor.md · Данные, форматы и интеграции](../../RAW_inputs/documents/UtilityGisEditor.md#данные-форматы-и-интеграции)

При установке задвижки на сохранившейся трубе идентичность трубы и исходный охват осмотра сохраняются. Дефект, физическое присутствие и доступность в эксплуатации устанавливают по отдельным свидетельствам. Для найденного списанного насоса редактор сохраняет сведения о присутствии и выясняет факт и характер отключения. [NET-05](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-05) · [NET-08](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-08) · [NET-16](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-16).

Принятую границу для изменения сведений об одном физическом активе описывает [[DDD_Wiki/aggregates/network_asset|агрегат сетевого актива]].
