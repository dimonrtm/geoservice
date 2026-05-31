# Agent-Driven Repository Change Ingest

Date: 2026-05-30
Type: decision
Tags: wiki, ingest, task-completion, pre-commit
Related files:

- `.agents/skills/source-command-ingest/SKILL.md`
- `.pre-commit-config.yaml`
- `Code_wiki/состояние_проекта/repository_change_ingest.md`
- `docs/knowledge-pipeline/README.md`
- `AGENTS.md`

## Summary

Repository-change ingest больше не выполняется Python-скриптом и не проверяется pre-commit. После полного завершения реализации плана или крупной задачи агент должен сам вызвать `/ingest repository-change`, используя repo-local skill `source-command-ingest`, перед финальным отчетом пользователю. Триггер не привязан к commit и не должен срабатывать после каждого мелкого шага.

## Context

Пользователь уточнил, что не нужен pre-commit guard и не нужен отдельный Python automatic writer. Нужно, чтобы агент вызывал skill `/ingest` после полного завершения реализации плана или крупной задачи, а pre-commit вообще не участвовал в knowledge pipeline.

## Actions

- 2026-05-30: Удалены `scripts/repository_change_ingest.py`, `scripts/tests/test_repository_change_ingest.py`, `scripts/prepare_commit.cmd`.
- 2026-05-30: Из `.pre-commit-config.yaml` удален local hook `repository-change-ingest-guard`.
- 2026-05-30: В `.agents/skills/source-command-ingest/SKILL.md` добавлен режим `/ingest repository-change`.
- 2026-05-30: Создан пустой журнал `Code_wiki/состояние_проекта/repository_change_ingest.md`.
- 2026-05-30: Обновлены `AGENTS.md`, `docs/knowledge-pipeline/README.md`, `README.md`, `CONTRIBUTING.md`, `scripts/README.md` и file-map.

## Verification

Проверить `python -m unittest discover -s scripts\tests`, `python scripts/lint-wiki.py --root .`, `python scripts/check-memory-needed.py --check`, `git diff --check`.

## Retrieval Hints

repository-change ingest, pre-commit guard removed, agent calls ingest, task completion workflow, source-command-ingest
