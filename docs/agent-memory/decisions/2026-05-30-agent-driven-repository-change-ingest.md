# Agent-Driven Repository Change Ingest

Date: 2026-05-30
Type: decision
Superseded by: `docs/agent-memory/decisions/2026-05-30-agent-memory-operating-rules.md`
Tags: wiki, ingest, task-completion, pre-commit
Related files:

- `.agents/skills/source-command-ingest/SKILL.md`
- `.pre-commit-config.yaml`
- `Code_wiki/состояние_проекта/repository_change_ingest.md`
- `docs/knowledge-pipeline/README.md`
- `AGENTS.md`

## Summary

Историческое решение отвязало repository-change ingest от Python-скрипта,
pre-commit и commit. Его триггер по завершению плана или крупной задачи
superseded: теперь `/ingest repository-change` вызывается только при наличии
нового устойчивого технического знания для `Code_wiki`; выбор нод и их
создание или обновление выполняет сам ingest.

## Context

Пользователь уточнил, что не нужен pre-commit guard и не нужен отдельный Python automatic writer. Нужно, чтобы агент вызывал skill `/ingest` после полного завершения реализации плана или крупной задачи, а pre-commit вообще не участвовал в knowledge pipeline.

## Actions

- 2026-05-30: Удалены `scripts/repository_change_ingest.py`, `scripts/tests/test_repository_change_ingest.py`, `scripts/prepare_commit.cmd`.
- 2026-05-30: Из `.pre-commit-config.yaml` удален local hook `repository-change-ingest-guard`.
- 2026-05-30: В `.agents/skills/source-command-ingest/SKILL.md` добавлен режим `/ingest repository-change`.
- 2026-05-30: Создан пустой журнал `Code_wiki/состояние_проекта/repository_change_ingest.md`.
- 2026-05-30: Обновлены `AGENTS.md`, `docs/knowledge-pipeline/README.md`, `README.md`, `CONTRIBUTING.md`, `scripts/README.md` и file-map.
- 2026-06-13: Task-completion trigger заменён двухусловным gate, журнал
  переведён в компактный реестр изменений нод `Code_wiki`.

## Verification

Проверить `python -m unittest discover -s scripts\tests`, `python scripts/lint-wiki.py --root .`, `python scripts/check-memory-needed.py --check`, `git diff --check`.

## Retrieval Hints

repository-change ingest, pre-commit guard removed, agent calls ingest, task completion workflow, source-command-ingest
