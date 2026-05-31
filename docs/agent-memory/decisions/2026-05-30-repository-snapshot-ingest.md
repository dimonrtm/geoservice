# Repository Snapshot Ingest

Date: 2026-05-30
Type: decision
Tags: wiki, ingest, repository-snapshot, code-wiki
Related files:

- `.agents/skills/source-command-ingest/SKILL.md`
- `docs/knowledge-pipeline/README.md`
- `Code_wiki/состояние_проекта/repository_snapshot.md`
- `memory/project-state.md`

## Summary

Добавлен режим `/ingest repository-snapshot` для первичного или периодического добавления в `Code_wiki` знаний из уже существующего неизмененного состояния репозитория.

## Context

`/ingest repository-change` фиксирует изменения через `git status` и `git diff`, но не покрывает уже существующую кодовую базу. Пользователь уточнил, что знания должны попадать в базу не только из новых изменений, но и из текущего состояния репозитория. Для этого нужен отдельный режим snapshot, чтобы не смешивать обзор текущей архитектуры с diff-based workflow.

## Actions

- 2026-05-30: В `.agents/skills/source-command-ingest/SKILL.md` добавлен режим `/ingest repository-snapshot`.
- 2026-05-30: В `docs/knowledge-pipeline/README.md`, `AGENTS.md` и `README.md` добавлено различие между `repository-snapshot` и `repository-change`.
- 2026-05-30: Создан журнал `Code_wiki/состояние_проекта/repository_snapshot.md`.
- 2026-05-30: Обновлены `memory/project-state.md` и `docs/agent-memory/file-map.md`.

## Verification

Проверить `python scripts/lint-wiki.py --root .`, `python -m unittest discover -s scripts\tests`, `python scripts/check-memory-needed.py --check`, `git diff --check`.

## Retrieval Hints

repository-snapshot ingest, existing repository knowledge, initial Code_wiki inventory, source-command-ingest, неизмененная кодовая база
