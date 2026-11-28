---
title: "Сущности"
type: index
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/UtilityGisEditor.md"
tags: [domain-knowledge, utility-gis]
confidence: n/a
related: [Wiki/entities/network_project, Wiki/entities/network_feature, Wiki/entities/network_association, Wiki/entities/edit_version, Wiki/entities/edit_event, Wiki/entities/work_order, Wiki/entities/field_observation, Wiki/entities/inspection, Wiki/entities/asset_attachment, Wiki/entities/integration_job]
---

# Сущности

- [[Wiki/entities/network_project|Проект ГИС, слой и тип актива]]. Находят проект, набор пространственных данных и инженерный тип объекта.
- [[Wiki/entities/network_feature|Актив инженерной сети]]. Связывают геометрию, инженерные свойства и историю с физическим объектом.
- [[Wiki/entities/network_association|Узлы и рёбра сети]]. Устанавливают, между какими узлами проходит ребро и как сеть связана через них.
- [[Wiki/entities/edit_version|Рабочая версия сети]]. Готовят и проверяют изменения до публикации.
- [[Wiki/entities/edit_event|Запись действия в истории версии]]. Прослеживают действие пользователя в конкретной версии.
- [[Wiki/entities/work_order|Наряд и позиции работ]]. Связывают задание с активами и учитывают подтверждённый объём восстановления.
- [[Wiki/entities/field_observation|Полевое наблюдение]]. Передают замер по наряду до опознания актива и сохраняют основание привязки.
- [[Wiki/entities/inspection|Осмотр актива и обследованный участок]]. Прослеживают результат обследования и исходный охват при последующих изменениях сети.
- [[Wiki/entities/asset_attachment|Вложение и подтверждаемое им сведение]]. Сопоставляют документ или фото с конкретным утверждением об активе.
- [[Wiki/entities/integration_job|Задание обмена с внешней системой]]. Определяют проект и внешнюю систему для отдельного обмена.

[Исходная диаграмма](../../RAW_inputs/documents/UtilityGisEditor.md#бизнес-модели-и-метрики-успеха) · [Принятые уточнения по полевым сведениям](../../RAW_inputs/documents/2026-11-27-field-information-model-analysis.md#что-добавилось-к-начальной-модели)
