---
title: Индекс Знаний GeoService
type: index
status: active
created: 2026-05-30
updated: 2026-06-13
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
- 2026-06-04: Выполнен `/sync-vision`; подтверждены актуальность индексов после Ф3, отсутствие новых необработанных RAW inputs, 7 открытых follow-up'ов, отсутствие stale-нод и ожидаемый lint-конфликт `FU-2026-06-01-004`.
- 2026-06-04: `/discover --phase Ф4` зафиксировал demo-scope: focused conflict/review layer для `Utility GIS editor`, primary scenario `geometry/association conflict`, роли `Editor`/`Reviewer`, synthetic utility dataset и explicit non-goals.
- 2026-06-05: Обработан RAW source `RAW_inputs/documents/utility_gis_editor_walking_skeleton_and_dataset.md`; уточнены end-to-end walking skeleton, desired technical skeleton и конкретный dataset `synthetic_utility_feeder_01`.
- 2026-06-05: Выполнен `/sync-vision`; индексы актуальны после latest ingest, новых необработанных RAW inputs нет, открытых follow-up'ов 4, stale-нод не обнаружено.
- 2026-06-05: `/discover --phase Ф5` зафиксировал local Docker Compose rollout для developer demo: decision maker - владелец pet-проекта, ценность - `learning value`, главный rollout-риск - непонятный UI conflict review.
- 2026-06-06: Выполнен `/sync-vision`; индексы синхронизированы после Ф5 и repository-change ingest, новых необработанных RAW inputs нет, открытых follow-up'ов 6, stale-нод не обнаружено.
- 2026-06-06: `/discover --phase Ф6` зафиксировал NFR local demo: Chrome, reference hardware с 16 GB RAM, startup/reset за несколько минут, JWT, separation of duties, audit persistence и минимальную observability.
- 2026-06-06: Обработан RAW source `RAW_inputs/documents/utility_gis_editor_target_times.md`; добавлены draft P95 acceptance targets и performance benchmark follow-up.
- 2026-06-07: Обработан RAW source `RAW_inputs/documents/utility_gis_editor_domain_dictionary.md`; добавлены канонический словарь `Utility GIS editing`, source summary и desired technical vocabulary без расширения demo-scope.
- 2026-06-07: Выполнен `/sync-vision`; индексы актуальны после Ф6 и двух RAW ingest, необработанных RAW inputs и stale-нод нет, открыты 7 follow-up'ов.
- 2026-06-07: `/discover --phase Ф7` зафиксировал `Safe Authoritative Post Rate >=95%` на 200 work orders, safety blockers, manual baseline, 30 benchmark runs и порядок минимальных экспериментов.
- 2026-06-11: Выполнен `/sync-vision`; индексы актуальны после Ф7 и repository-change ingest, новых необработанных RAW inputs и stale-нод нет, открыты 9 follow-up'ов.
- 2026-06-11: `/discover --phase Ф8` пересобрал Release 1 вокруг полного `Utility GIS editor` workflow; старый generic GIS сохранен только как технический foundation.
- 2026-06-11: Подготовлены code compliance matrix и план реализации нового Release 1 на 7 двухнедельных спринтов.
- 2026-06-12: Спринт 1 разложен на 14 календарных дней; контракты Дня 1 зафиксировали acceptance AC-01..AC-07, доменную модель, API и вертикальный backlog S1-01..S1-10 в `docs/sprint_1`.
- 2026-06-12: Выполнен `/sync-vision`; индексы и [[memory/project-state]] синхронизированы после Ф8 и планирования Спринта 1, новых RAW inputs и stale-нод нет, открыты 10 follow-up'ов.
- 2026-06-12: Обработана синтетическая репетиция интервью `Utility GIS editor`; primary persona и JTBD приняты для design, добавлен акцент на единый evidence context, внешний user validation отложен.
- 2026-06-13: Реализованы роли `Editor`/`Reviewer`, DB-backed active-user auth, structured auth errors, demo seed и reviewer shell Дня 2 Спринта 1; связанные ноды [[Code_wiki/index]] синхронизированы через `/ingest repository-change`.
- 2026-06-13: Agent memory и knowledge pipeline переведены на gate устойчивого знания, компактный реестр изменений `Code_wiki` и read-only memory audit.
- 2026-06-13: Выполнен `/sync-vision`; необработанных RAW inputs и stale-нод нет, открыты 10 follow-up'ов, ожидаемый lint-конфликт остаётся на 12 неизменяемых RAW Markdown files.

## Открытые Вопросы

- Новый Release 1 разбит на 7 двухнедельных спринтов; роли и seed Дня 2 завершены, следующий scope Спринта 1 - utility schema, assigned work orders, edit version и frontend shell.
- Для `Utility GIS editor` нужно реализовать полный путь work order -> edit version -> validation -> reconcile -> conflict resolution -> review -> post -> audit на `synthetic_utility_feeder_01`.
- Нужно восстановить доступные URL для non-Esri vendor-specific утверждений из research по collaborative editing.
- Нужно согласовать `lint-wiki.py` с правилом неизменяемости RAW Markdown.
- Нужно подготовить local demo support package: README, seed/reset/`full-clean` scripts, demo сценарий, troubleshooting, observability minimum и `import GeoJSON`.
- Нужно проверить draft P95 targets на `synthetic_utility_feeder_01` в Chrome на reference hardware.
- Нужно снять manual baseline на 10-20 work orders и провести product evaluation на 200 started work orders с 7-дневным correction window.
- Технические пробелы repository snapshot зафиксированы в [[Code_wiki/состояние_проекта/repository_snapshot]].
- Очередь follow-up'ов: [[Vision_wiki/decisions/followups/index]].

## Ручной Pipeline

- Утро: запустить `/sync-vision`, прочитать `memory/project-state.md`, проверить новые файлы в `RAW_inputs/`, затем запустить `/ingest` для новых RAW inputs.
- Перед встречей: запустить `/discover --context "планирование спринта" --phase "F2"` и подготовить чек-лист из 10-15 вопросов.
- После встречи: положить транскрипт в `RAW_inputs/meetings/`, запустить `/ingest`, обновить wiki-ноды, конфликты, follow-up'ы и project state.
- Раз в неделю: запустить `/lint-wiki`, затем `/sync-vision`, затем проверить отчет о здоровье wiki.

## Repository Ingest

`/ingest repository-snapshot` фиксирует уже существующее состояние репозитория в `Code_wiki` без привязки к `git diff`.

`/ingest repository-change` запускается только когда завершённая работа содержит
новое устойчивое техническое знание для `Code_wiki`. Завершение плана, commit
или успешные тесты сами по себе не являются триггерами. Pre-commit не запускает
и не проверяет repository-change ingest.
