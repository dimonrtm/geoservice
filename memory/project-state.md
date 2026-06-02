---
title: Состояние Проекта GeoService
type: state
status: active
created: 2026-05-30
updated: 2026-06-02
source: null
tags: [project-state, geoservice]
---

# Состояние Проекта GeoService

Живое состояние knowledge wiki GeoService.

## Кратко

GeoService - исследовательский pet-проект на стадии идея / прототип. Цель: изучить алгоритмы совместного редактирования геометрии и проверить AI-first разработку сложной геоинформационной системы. Текущий Release 1 draft описывает хранение геоданных, API-доступ, отображение карты и базовое совместное редактирование.

## Состояние Pipeline

- Последний `/discover`: 2026-06-02, фаза Ф2 завершена на уровне research-гипотез; primary research-persona - `Utility GIS editor`, кадастровый сценарий отложен как более сложный для реализации.
- Последний `/ingest`: 2026-06-01, batch RAW ingest `RAW_inputs/documents/Ф2.md`; добавлены research-ноды для подготовки Ф2-Ф3.
- Последний `/sync-vision`: 2026-06-02 18:07 +05:00, синхронизированы индексы и project-state после discovery Ф2.
- Последний `/lint-wiki`: 2026-06-02, найден `missing_frontmatter` для `RAW_inputs/documents/Ф2.md`; RAW source оставлен неизменным по правилу `/ingest`, открытый follow-up `FU-2026-06-01-004` остается актуальным.
- Последний repository-snapshot ingest: 2026-05-30, первичная инвентаризация backend, frontend, API/realtime, data model, Docker/CI и tests.
- Последний repository-change ingest: 2026-06-02, зафиксирован выбор `Utility GIS editor` как primary research-persona, закрытие Ф2 на уровне гипотез и synthetic validation follow-up.

## Изменения С Прошлого `/sync-vision`

- Обработан `RAW_inputs/documents/Ф2.md`: добавлены research-ноды с четырьмя моделями collaborative editing, семью пользовательскими архетипами и картой альтернатив для будущей Ф3.
- Зафиксированы follow-up'ы: выбрать primary scenario, восстановить доступные URL для vendor-specific утверждений и не расширять scope Release 1 автоматически до Ф4.
- Подтвержден unresolved process conflict: `lint-wiki.py` требует YAML frontmatter от неизменяемого RAW Markdown.
- Корневой `index.md` обновлен актуальными изменениями и вопросами после ingest исследования Ф2.
- `/discover --phase Ф2` сузил research до двух модельных persona-кандидатов и provisional JTBD; внешняя пользовательская боль остается гипотезой до валидации.
- Повторный `/sync-vision` подтвердил актуальность индексов, 9 открытых follow-up'ов, отсутствие новых RAW inputs и stale-нод.
- Второй проход `/discover --phase Ф2` выбрал `Utility GIS editor` как primary research-persona, описал work order workflow, reviewer перед post и synthetic validation; все утверждения остаются research-гипотезами.

## Состояние Wiki На 2026-06-02

- Новые RAW inputs: 0 необработанных содержательных файлов; `RAW_inputs/documents/Ф2.md` обработан 2026-06-01 как research для Ф2-Ф3.
- Новые значимые Vision ноды с прошлого `/sync-vision`: 2 concept-ноды, 4 entity-ноды и 2 chat-ноды из ingest исследования Ф2 и `/discover --phase Ф2`.
- Новые значимые Code_wiki ноды с прошлого `/sync-vision`: нет.
- Stale-ноды: не обнаружены.
- Unresolved conflicts: 1 process conflict, зафиксированный в `FU-2026-06-01-004`.
- Открытые follow-up'ы: 8.

## Открытые Вопросы

См. [[../Vision_wiki/decisions/followups/index]].

Ключевые открытые вопросы:

- Нужно отдельным запросом решить, что делать с пустыми/неполными dev/infra helper files, найденными repository snapshot.
- Для `Utility GIS editor` нужно подготовить synthetic utility dataset и проверить topology, `attribute vs attribute`, `geometry/association`, `edit after reconcile`.
- Нужно пройти Ф3: сравнить альтернативы и контекст использования для utility authoritative editing.
- Нужно добавить доступные URL для vendor-specific утверждений из `RAW_inputs/documents/Ф2.md`.
- Нужно отдельной implementation/docs-задачей согласовать `lint-wiki.py` с правилом неизменяемости RAW Markdown.
- Нужно превратить критерий первого релиза "все типа работает" в проверяемый demo-script и acceptance criteria.
