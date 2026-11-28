---
title: "Авторитетная сеть"
type: bounded-context
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/UtilityGisEditor.md; RAW_inputs/documents/2026-11-27-field-information-answers.md; RAW_inputs/documents/2026-11-27-field-information-model-analysis.md"
tags: [domain-knowledge, utility-gis]
confidence: inferred
related: [Wiki/entities/edit_version, Wiki/policies/publication, DDD_Wiki/context_map/geoservice_context_map]
---

# Авторитетная сеть

## Ubiquitous Language Boundary

Актив, узел, ребро, рабочая версия, топологическая проверка и публикация описывают состояние инженерной сети. В этой части модели решается, какое изменение можно включить в официальное представление. Для диспетчера те же узлы и рёбра служат исходными данными трассировки.

Предложенная граница соответствует модулю Authoritative Network Editor. На вход поступают заявки, полевые уточнения и результаты строительства. Выход — проверенное изменение сети, доступное её потребителям.

В GeoService редактор отвечает за принятые границы геометрии и установленный стык. Эксплуатация подтверждает ввод конкретной части. Диспетчер рассчитывает действующий путь по этим сведениям и подтверждённому положению устройств на нужный момент. Положение для оперативного расчёта может измениться до публикации правки постоянной схемы. [Участие построенной части в трассировке](../../Wiki/specifications/built_part_traceable.md) · [NET-13](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-13).

[UtilityGisEditor.md · Gap analysis и рекомендации по стратегии продукта](../../RAW_inputs/documents/UtilityGisEditor.md#gap-analysis-и-рекомендации-по-стратегии-продукта)

## За какие решения отвечает контекст

ГИС-редактор ведёт [рабочую версию](../aggregates/network_edit_version.md) и отвечает за обоснование правки геометрии и связей. Результат выдаётся потребителям после проверки, утверждения и публикации выбранного объёма. Право одного участника совмещать утверждение и публикацию остаётся вопросом NET-02. [Жизненный цикл правки](../state_machines/edit_version_publication.md) · [Реестр вопросов](../../Wiki/_registry/questions.md).

В истории [сетевого актива](../aggregates/network_asset.md) идентичность физической трубы сохраняется при делении её ребра задвижкой. Редактору нужны исходный охват осмотра и привязка места дефекта. Подключение изменяет граф по свидетельству о стыке. Ограничение работы требует отдельного подтверждения эксплуатации. [NET-04](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-04) · [NET-05](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-05) · [Эксплуатационная доступность](../state_machines/asset_operational_availability.md).

При оперативном использовании сети диспетчер ведёт [историю положений устройства](../aggregates/device_position_history.md) и выбирает положение на момент расчёта. Если оно неизвестно, передаёт в полевые работы определённую и возможную части расчётного охвата вместе с запросом на уточнение. Граф, расчётный охват и фактическое восстановление услуги служат тремя разными результатами. [Положение на момент расчёта](../state_machines/operational_device_position.md) · [Учёт восстановления](../state_machines/restoration_accounting.md).
