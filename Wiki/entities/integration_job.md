---
title: "Задание обмена с внешней системой"
type: entity
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/UtilityGisEditor.md"
tags: [domain-knowledge, utility-gis, integration]
confidence: inferred
related: [Wiki/entities/network_project, Wiki/external_systems/external_gis_stack, DDD_Wiki/bounded_contexts/integration_exchange]
---

# Задание обмена с внешней системой

В ER-диаграмме `INTEGRATION_JOB` — отдельное задание обмена, инициированное [[Wiki/entities/network_project|проектом ГИС]] и относящееся к конкретной [[Wiki/external_systems/external_gis_stack|внешней системе]]. И у проекта, и у внешней системы может быть несколько таких заданий. По заданию различают, для какого проекта и с каким участником организована передача. Офисный процесс предусматривает передачу опубликованных изменений мобильным клиентам и внешним системам. [Концептуальная диаграмма](../../RAW_inputs/documents/UtilityGisEditor.md#бизнес-модели-и-метрики-успеха) · [Публикация и синхронизация](../../RAW_inputs/documents/UtilityGisEditor.md#базовые-и-продвинутые-workflows).

Принятые правила GeoService различают доставку сведений и их использование. Так, когда учётная система сообщает о списании насоса, редактор получает основание для сверки, а эксплуатационное отключение устанавливает по сведениям эксплуатации. Для сообщения о положении задвижки важно время самого переключения или наблюдения. Порядок доставки сообщений сам по себе не определяет положение устройства при следующем расчёте. [NET-16](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-16) · [NET-13](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-13).

За выбор подтверждённого положения для расчёта отвечает диспетчер. Основание выбора относится к [[DDD_Wiki/aggregates/device_position_history|истории оперативных положений конкретного устройства]].

Документ оставляет формат конкретной поставки, признаки завершения задания и подтверждения приёма открытыми. [[DDD_Wiki/bounded_contexts/integration_exchange|Ответственность за обмен и аудит]].
