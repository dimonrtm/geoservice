---
title: Индекс Знаний GeoService
type: index
status: active
created: 2026-05-30
updated: 2026-06-03
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
- [[Vision_wiki/index]] - продуктовые знания, решения, конфликты, follow-up'ы и заметки встреч.
- [[Code_wiki/index]] - техническая wiki для архитектуры, разработки, deployment и состояния проекта.
- [[memory/project-state]] - живое состояние проекта.
- [[memory/llm-wiki-method]] - методика ведения атомарных LLM-wiki нод.
- [[docs/agent-memory/README]] - компактная инженерная память Codex.

## Свежие Изменения

- 2026-05-30: Создана стартовая project knowledge wiki и ручной pipeline `/discover`, `/ingest`, `/sync-vision`, `/lint-wiki`.
- 2026-05-30: Выполнен `/ingest repository-snapshot`; техническая карта текущего репозитория добавлена в [[Code_wiki/index]].
- 2026-05-30: Выполнен `/sync-vision`; индексы и [[memory/project-state]] синхронизированы после repository snapshot.
- 2026-05-30: Обработан RAW source `RAW_inputs/documents/спринт 1.odt`; заполнены Release 1 solution-ноды и desired API contract.
- 2026-05-31: Первый `/discover` и фаза Ф1 уточнили pet-project контекст, исследовательскую мотивацию и отсутствие подтвержденной внешней пользовательской боли.
- 2026-06-01: Выполнен `/sync-vision`; корневой индекс и [[memory/project-state]] синхронизированы после Release 1 ingest и Ф1 discovery.
- 2026-06-01: Обработан research RAW source `RAW_inputs/documents/Ф2.md`; добавлены модели collaborative editing, пользовательские архетипы и карта альтернатив для подготовки Ф2-Ф3.
- 2026-06-02: Выполнен `/sync-vision`; корневой индекс и [[memory/project-state]] синхронизированы после ingest исследования Ф2.
- 2026-06-02: `/discover --phase Ф2` сузил исследование до двух модельных authoritative editing сценариев: `Utility GIS editor` и кадастровый инженер.
- 2026-06-02: Выполнен повторный `/sync-vision`; индексы и [[memory/project-state]] синхронизированы после discovery Ф2.
- 2026-06-02: Второй проход `/discover --phase Ф2` выбрал `Utility GIS editor` как primary research-persona; кадастровый сценарий отложен.
- 2026-06-03: Выполнен `/sync-vision`; подтверждены отсутствие новых RAW inputs, 8 открытых follow-up'ов, отсутствие stale-нод и ожидаемый lint-конфликт `FU-2026-06-01-004`.
- 2026-06-03: Обработан RAW source `RAW_inputs/documents/03.06.2026deep-research-report.md`; Ф3 сравнила альтернативы для `Utility GIS editor`, baseline - `ArcGIS Enterprise + Utility Network`, niche GeoService - conflict/review explainability.

## Открытые Вопросы

- Для `Utility GIS editor` нужно проверить модельные боли на synthetic utility dataset: главный сценарий `geometry/association conflict` с dirty areas, network consequence, reviewer decision и authoritative post.
- На Ф4 нужно решить, остается ли GeoService focused conflict/review layer или проверяет более широкий branch/versioning workflow.
- Нужно восстановить доступные URL для non-Esri vendor-specific утверждений из research по collaborative editing.
- Нужно превратить критерий первого релиза "все типа работает" в проверяемый demo-script и acceptance criteria.
- Нужно уточнить приоритет результата: demo, portfolio, применение в реальной работе или основа будущего продукта.
- Нужно согласовать `lint-wiki.py` с правилом неизменяемости RAW Markdown.
- Технические пробелы repository snapshot зафиксированы в [[Code_wiki/состояние_проекта/repository_snapshot]].
- Очередь follow-up'ов: [[Vision_wiki/decisions/followups/index]].

## Ручной Pipeline

- Утро: запустить `/sync-vision`, прочитать `memory/project-state.md`, проверить новые файлы в `RAW_inputs/`, затем запустить `/ingest` для новых RAW inputs.
- Перед встречей: запустить `/discover --context "планирование спринта" --phase "F2"` и подготовить чек-лист из 10-15 вопросов.
- После встречи: положить транскрипт в `RAW_inputs/meetings/`, запустить `/ingest`, обновить wiki-ноды, конфликты, follow-up'ы и project state.
- Раз в неделю: запустить `/lint-wiki`, затем `/sync-vision`, затем проверить отчет о здоровье wiki.

## Repository Ingest

`/ingest repository-snapshot` фиксирует уже существующее состояние репозитория в `Code_wiki` без привязки к `git diff`.

После полного завершения implementation plan или крупной задачи агент вызывает `/ingest repository-change` перед финальным отчетом пользователю. Pre-commit не запускает и не проверяет repository-change ingest.
