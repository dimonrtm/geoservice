---
title: "Запись действия в истории версии"
type: entity
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/UtilityGisEditor.md"
tags: [domain-knowledge, utility-gis, audit]
confidence: inferred
related: [Wiki/entities/edit_version, Wiki/actors/organization_and_access, Wiki/entities/integration_job]
---

# Запись действия в истории версии

В концептуальной диаграмме `EDIT_EVENT` связывает выполненное действие с [[Wiki/actors/organization_and_access|пользователем]] и [[Wiki/entities/edit_version|версией сети]]. У пользователя может быть несколько действий в разных версиях, у версии — история действий нескольких пользователей. По отдельной записи можно установить, кто работал с данной версией. [Концептуальная диаграмма](../../RAW_inputs/documents/UtilityGisEditor.md#бизнес-модели-и-метрики-успеха).

В офисном процессе это позволяет проследить подготовку изменения и вернуться к истории при разборе расхождения. Запись редактирования описывает работу с данными. Утверждение и публикация имеют собственные условия. Например, запись о нанесении построенного участка указывает, кто работал с версией, а для допуска участка к эксплуатационной трассировке требуется подтверждённый ввод и установленные рабочие подключения. [Офисный процесс](../../RAW_inputs/documents/UtilityGisEditor.md#базовые-и-продвинутые-workflows) · [Решение GeoService по NET-10](../../RAW_inputs/documents/2026-11-27-field-information-answers.md#net-10).

Исходный документ предусматривает аудит и обратимую историю. Состав полей записи, перечень регистрируемых операций и сроки хранения в нём не заданы. [[DDD_Wiki/bounded_contexts/integration_exchange|Обмен и аудит]]. [Требования к истории и доступу](../../RAW_inputs/documents/UtilityGisEditor.md#производительность-безопасность-ux-desktopmobileoffline).
