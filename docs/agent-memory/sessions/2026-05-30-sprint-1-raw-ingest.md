# Sprint 1 Raw Ingest

Superseded by: docs/agent-memory/sessions/2026-05-31-initial-discover-release-1-clarification.md

Date: 2026-05-30
Type: session
Tags: wiki, ingest, sprint-1, raw-inputs, requirements
Related files:

- `RAW_inputs/documents/спринт 1.odt`
- `Vision_wiki/chats/2026-05-30-sprint-1-document.md`
- `Vision_wiki/concepts/sprint_1_mvp.md`
- `Vision_wiki/solution/USM.md`
- `Vision_wiki/solution/roadmap.md`
- `Vision_wiki/solution/nfr.md`
- `Vision_wiki/solution/architecture_vision.md`
- `Code_wiki/архитектура/api_contract_sprint_1_requirements.md`

## Summary

Выполнен `/ingest` без параметров для единственного нового RAW source `RAW_inputs/documents/спринт 1.odt`. Документ стал source-of-truth для Sprint 1 MVP: совместное редактирование Feature, bbox loading, роли `Viewer`/`Editor`, optimistic concurrency, WebSocket realtime и SYNC GeoJSON import.

## Context

Перед ingest `memory/project-state.md` считал содержательных RAW inputs равными 0 и solution-ноды были стартовыми draft-заготовками. В `RAW_inputs/documents/` появился ODT-файл с планом и контрактами Sprint 1, поэтому обычный batch ingest обработал его без подтверждения: кандидат был один и тип источника был понятен.

## Actions

- 2026-05-30: Созданы `Vision_wiki/chats/2026-05-30-sprint-1-document.md` и `Vision_wiki/concepts/sprint_1_mvp.md`.
- 2026-05-30: Обновлены `Vision_wiki/solution/USM.md`, `roadmap.md`, `nfr.md`, `architecture_vision.md` из RAW source.
- 2026-05-30: Создана technical requirements нода `Code_wiki/архитектура/api_contract_sprint_1_requirements.md`.
- 2026-05-30: Обновлены `RAW_inputs/index.md`, `Vision_wiki/index.md`, `Code_wiki/index.md`, `Vision_wiki/decisions/followups/index.md` и `memory/project-state.md`.

## Verification

`C:\Users\dimon\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe scripts/lint-wiki.py --root .` -> `Wiki lint passed`.

Стандартная команда `python scripts/lint-wiki.py --root .` в этом Windows shell резолвится в Microsoft Store stub `C:\Users\dimon\AppData\Local\Microsoft\WindowsApps\python.exe`, поэтому для проверки использован bundled Python из Codex runtime.

## Retrieval Hints

Sprint 1 ingest, спринт 1 ODT, RAW_inputs documents sprint, optimistic concurrency, bbox endpoint, GeoJSON import, Viewer Editor, WebSocket realtime, api contract requirements
