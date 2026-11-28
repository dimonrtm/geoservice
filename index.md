---
title: Индекс Знаний GeoService
type: index
status: active
created: 2026-05-30
updated: 2026-11-27
source: null
tags: [knowledge, index, geoservice]
---

# Индекс Знаний GeoService

Это точка входа в project knowledge wiki GeoService.

## Проект

- Название: GeoService
- Репозиторий: `C:\Repositories\geoservice`
- Стадия: идея / прототип
- Кратко: GeoService хранит геообъекты в PostGIS, отдает их через FastAPI и отображает/редактирует карты через Vue и MapLibre.

## Области Знаний

- [[RAW_inputs/index]] - сырые источники и исходные материалы проекта.
- [[Wiki/index]] - канонические доменные сущности, concepts, actors, commands, events, policies, specifications, conflicts, questions и registry tables.
- [[DDD_Wiki/index]] - DDD-модель: domains, subdomains, bounded contexts, context map, aggregates, invariants, use cases, integration patterns и model health.
- [[Code_wiki/index]] - техническая wiki для архитектуры, разработки, deployment и состояния проекта.
- [[memory/project-state]] - живое состояние проекта.
- [[memory/llm-wiki-method]] - методика ведения атомарных LLM-wiki нод.
- [[Общие_принципы/index]] — методика discovery и планирования.
- [[docs/knowledge-pipeline/README]] — порядок работы с источниками и wiki.
- [[docs/agent-memory/README]] - компактная инженерная память Codex.


## Текущее состояние

27.11.2026 доменная модель начата заново. Единственный источник — [обзор редактора инженерной сети](RAW_inputs/documents/UtilityGisEditor.md). [[DDD_Wiki/domains/geoservice|Граница модели]] · [[DDD_Wiki/use_cases/_info|Четыре рабочих процесса]] · [[DDD_Wiki/model_health|Что определено в модели]].

## Открытые вопросы

[[Wiki/_registry/questions|Очередь доменных вопросов]] · [[Wiki/_registry/conflicts|Реестр конфликтов]] · [[memory/project-state|Задачи проекта и следующий шаг]].

## Разработка и обработка источников

[План спринта 3 и ручная приёмка](docs/sprint_3/sprint-3-office-publication.md) · [Очередь разработки редактора](docs/planning/network-editor-backlog.md) · [[Code_wiki/index|Архитектура и техническое состояние]] · [[docs/knowledge-pipeline/README|Процедура ingest]] · [[RAW_inputs/index|Журнал источников]].
