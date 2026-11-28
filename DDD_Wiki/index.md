---
title: "Доменная модель редактора инженерных сетей"
type: index
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/UtilityGisEditor.md"
tags: [domain-knowledge, utility-gis]
confidence: n/a
related: [Wiki/index, DDD_Wiki/use_cases/_info, DDD_Wiki/model_health]
---

# Доменная модель редактора инженерных сетей

Для оператора сети важно знать, где расположен актив, как он связан с другими объектами и какие изменения уже утверждены. Здесь собраны предметные границы и четыре процесса из единственного исходного документа.

## Сценарии

- [[DDD_Wiki/use_cases/utility_editor_workflow|Подготовить и опубликовать изменение сети]]
- [[DDD_Wiki/use_cases/field_office_sync|Передать полевые изменения в офис]]
- [[DDD_Wiki/use_cases/outage_workflow|Определить охват отключения и учесть восстановление]]
- [[DDD_Wiki/use_cases/as_built_workflow|Учесть фактически построенную сеть]]

## Границы и правила

- [[DDD_Wiki/domains/geoservice|Ведение авторитетной модели инженерной сети]]
- [[DDD_Wiki/subdomains/utility_authoritative_editing|Области ответственности при работе с сетью]]
- [[DDD_Wiki/context_map/geoservice_context_map|Как связаны сеть, полевые работы и обмен]]
- [[DDD_Wiki/aggregates/_info|Агрегаты GeoService, их корни и инварианты]]
- [[DDD_Wiki/invariants/field_evidence_scope|Какие изменения допустимы по полевому свидетельству]]
- [[DDD_Wiki/state_machines/_info|Состояния рабочей версии, полевых и эксплуатационных данных]]
- [[DDD_Wiki/integration_patterns/asset_status_reconciliation|Как сопоставляют входящий статус с состоянием сети]]
- [[Wiki/policies/publication|Условия публикации изменения сети]]
- [[Wiki/policies/field_information|Как полевые сведения меняют запись актива и расчёт по сети]]
- [[Wiki/concepts/network_data|Данные инженерной сети и их связи]]

[[DDD_Wiki/model_health|Полнота модели]] · [[DDD_Wiki/use_cases/candidates/_info|Основания принятия сценариев]] · [[Wiki/_registry/questions|Открытые вопросы]] · [[Wiki/index|Словарь и реестры]].

[UtilityGisEditor.md](../RAW_inputs/documents/UtilityGisEditor.md)
