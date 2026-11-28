---
title: "Как изменение попадает в официальную модель сети"
type: concept
status: active
created: 2026-11-27
updated: 2026-11-27
source: "RAW_inputs/documents/UtilityGisEditor.md"
tags: [domain-knowledge, utility-gis]
confidence: inferred
related: [Wiki/entities/edit_version, Wiki/policies/publication, Wiki/entities/edit_event, Wiki/entities/integration_job, DDD_Wiki/use_cases/_info]
---

# Как изменение попадает в официальную модель сети

Работа начинается с заявки на изменение или [[Wiki/entities/work_order|наряда]]. Редактор получает [[Wiki/entities/edit_version|рабочую версию сети]], меняет геометрию, атрибуты и связи. Основанием для изменения могут служить офисное задание, [[Wiki/entities/field_observation|результат выезда]] или [[Wiki/concepts/design_revision|исполнительные сведения после строительства]].

Перед [[Wiki/policies/publication|публикацией]] изменения проверяют по правилам и топологии. Ошибка или конфликт возвращает работу к исправлению и повторной проверке. Проверенный результат проходит рассмотрение и утверждение. Опубликованный результат передают мобильным клиентам и [[Wiki/external_systems/external_gis_stack|смежным системам]]. [[Wiki/entities/edit_event|История версии]] позволяет установить, кто работал с ней, а [[Wiki/entities/integration_job|задание обмена]] указывает, с какой системой организована передача.

[UtilityGisEditor.md · Базовые и продвинутые workflows](../../RAW_inputs/documents/UtilityGisEditor.md#базовые-и-продвинутые-workflows)
