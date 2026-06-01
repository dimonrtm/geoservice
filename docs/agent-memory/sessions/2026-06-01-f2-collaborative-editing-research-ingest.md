# F2 Collaborative Editing Research Ingest

Date: 2026-06-01
Type: session
Tags: wiki, ingest, discovery, phase-f2, phase-f3, collaborative-editing
Related files:

- `RAW_inputs/documents/Ф2.md`
- `Vision_wiki/chats/2026-06-01-phase-f2-collaborative-editing-research.md`
- `Vision_wiki/concepts/collaborative_editing_models.md`
- `Vision_wiki/entities/personas/collaborative_editing_archetypes.md`
- `Vision_wiki/entities/competitors/collaborative_editing_alternatives.md`
- `Vision_wiki/decisions/followups/index.md`
- `memory/project-state.md`

## Summary

Обработан research-файл `RAW_inputs/documents/Ф2.md`. Он содержит сравнительный обзор collaborative editing в веб-ГИС, четыре модели взаимодействия, семь модельных архетипов и карту альтернатив для подготовки Ф2-Ф3.

## Context

Источник не является ответами реального пользователя GeoService. Архетипы, оценки частоты и product-рекомендации сохранены как research/hypothesis. Citation-маркеры вида `turn10view7` непрозрачны вне исходной research-сессии, поэтому vendor-specific утверждения требуют доступных URL перед независимой проверкой.

## Actions

- 2026-06-01: Созданы summary источника, нода моделей collaborative editing, нода архетипов и research-карта альтернатив.
- 2026-06-01: Добавлены follow-up'ы: выбрать primary scenario, восстановить доступные ссылки, не расширять Release 1 автоматически до Ф4.
- 2026-06-01: Обновлены `RAW_inputs/index.md`, `Vision_wiki/index.md`, `memory/project-state.md` и `docs/agent-memory/file-map.md`.
- 2026-06-01: Зафиксирован `FU-2026-06-01-004`: `lint-wiki.py` включает Markdown-файлы из `RAW_inputs/` и требует frontmatter, но `/ingest` запрещает менять RAW source. Исправление оставлено отдельной implementation/docs-задачей.

## Verification

Проверено через bundled Python/runtime:

- `python scripts/lint-wiki.py --root .`: найден один ожидаемый issue `missing_frontmatter` для неизменяемого `RAW_inputs/documents/Ф2.md`; создан `FU-2026-06-01-004`.
- `python scripts/check-memory-needed.py --check`: `Memory update check passed.`
- `python -m unittest discover -s scripts\tests`: `8` tests OK.
- `git diff --check`: без ошибок.

## Retrieval Hints

Ф2 research, Ф3 alternatives, collaborative editing models, archetypes, ArcGIS, Mergin Maps, QFieldCloud, HOT Tasking Manager, MapStore, GeoServer
