---
title: "Как редактор принимает полевые сведения"
type: policy
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/2026-11-27-field-information-answers.md"
tags: [domain-knowledge, field-work, utility-gis]
confidence: inferred
related: [Wiki/policies/publication, Wiki/concepts/network_data, DDD_Wiki/use_cases/field_office_sync, DDD_Wiki/use_cases/as_built_workflow, DDD_Wiki/use_cases/outage_workflow, DDD_Wiki/use_cases/utility_editor_workflow]
---

# Как редактор принимает полевые сведения

Правило условной организации выбрано через `expert_repson` для [исходного процесса работы с сетью](../../RAW_inputs/documents/UtilityGisEditor.md#базовые-и-продвинутые-workflows). Для каждого изменения редактор устанавливает, какой объект обследован, когда и каким способом получены сведения, какой участок они охватывают и какое именно свойство подтверждают.

## Rule

- Идентификация предшествует правке карточки. Наблюдение с неясной принадлежностью можно принять по наряду и уточнить позднее. При расхождении координат одного объекта редактор сравнивает основания обеих правок и документирует выбор. [NET-01](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-01) · [NET-07](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-07).
- Геометрия и подключение проверяются по отдельности. Для общего узла нужны сведения об обеих соединённых трубах. Установка задвижки на сохранившейся трубе меняет рёбра, а прошлый осмотр сохраняет привязку к прежнему физическому объекту и обследованной части. [NET-04](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-04) · [NET-05](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-05).
- Физическое наличие, дефект и доступность для работы имеют разные основания. Для изменения эксплуатационного состояния редактор устанавливает характер, время и границу ограничения по подтверждению эксплуатации или фактического отключения. Финансовое списание сохраняется как основание для сверки. [NET-08](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-08) · [NET-16](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-16).
- Съёмка устанавливает построенный объём. Подтверждённая врезка устанавливает связь, а ввод в работу определяет участие в оперативной трассировке. Для заключения о соответствии проекту требуется применимая к работам редакция. Спор о позднем распоряжении сохраняется отдельно от факта строительства. [NET-09](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-09) · [NET-10](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-10) · [NET-11, частичный ответ](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-11).
- Диспетчер применяет подтверждённое положение устройства на момент расчёта. При неизвестном положении отмечает возможный охват. Фактический возврат услуги подтверждается по охваченным частям отдельно от расчёта и отметки о завершении ремонта. [NET-12](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-12) · [NET-13](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-13) · [NET-03](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-03).

## Decision Outcome

Офис может принять один пакет и использовать его части по-разному. Например, измеренный участок после проверок и утверждения появляется на карте, проектная врезка остаётся неподтверждённой, а участок до ввода исключён из трассировки действующей сети. Неразрешённый конфликт в публикуемом объёме возвращает соответствующую правку на проверку. [[Wiki/policies/publication|Условия публикации изменения сети]].

[Происхождение решений и внешние свидетельства](../../RAW_inputs/documents/2026-11-27-field-information-answers.md) · [Сопоставление с начальной моделью](../../RAW_inputs/documents/2026-11-27-field-information-model-analysis.md).

Для разбора отдельного случая редактор проверяет [[Wiki/specifications/observation_identifies_asset|привязку наблюдения]], [[Wiki/value_objects/evidence_extent|охват свидетельства]] и [[Wiki/specifications/operational_restriction_evidenced|основание ограничения]]. В оперативном задании диспетчер применяет [[Wiki/policies/operational_trace|правило выбора положения устройств и расчётного охвата]].
