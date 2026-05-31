# Project Knowledge Wiki Pipeline

Date: 2026-05-30
Type: session
Tags: wiki, knowledge-pipeline, repository-change-ingest, obsidian
Related files:

- `index.md`
- `RAW_inputs/`
- `Vision_wiki/`
- `Code_wiki/`
- `memory/`
- `Общие_принципы/`
- `.obsidian/`
- `.agents/skills/`
- `docs/knowledge-pipeline/README.md`
- `scripts/lint-wiki.py`
- `scripts/check-memory-needed.py`
- `.pre-commit-config.yaml`

## Summary

Добавлен PO-style project knowledge wiki pipeline для GeoService без привязки к donor-проекту. Wiki ведется на русском языке, donor-репозиторий `C:\Repositories\ai-po-template-experiments` остается read-only reference и не должен редактироваться.

## Context

Пользователь хотел перенести шаблонный pipeline создания базы знаний: ручные `/sync-vision`, `/discover`, `/ingest`, `/lint-wiki`; Obsidian graph; сбор знаний не только из `RAW_inputs`, но и из значимых изменений репозитория. Изначально обсуждался запуск `repository-change ingest` перед pre-commit, но это правило заменено: после полного завершения реализации плана или крупной задачи агент вызывает `/ingest repository-change` перед финальным отчётом пользователю.

## Actions

- 2026-05-30: Создана wiki-структура `RAW_inputs/`, `Vision_wiki/`, `Code_wiki/`, `memory/`, `Общие_принципы/` и корневой `index.md`.
- 2026-05-30: Добавлены шаблоны для Vision/Code wiki, manual runbook, repo-local command docs и Obsidian graph config.
- 2026-05-30: Добавлен `scripts/lint-wiki.py` для проверки frontmatter, wikilinks, пустых нод и обязательных `source`.
- 2026-05-30: Ранее добавленные `scripts/repository_change_ingest.py`, `scripts/prepare_commit.cmd` и pre-commit guard удалены. Repository-change ingest теперь выполняется агентом через skill `/ingest repository-change` после полного завершения реализации плана или крупной задачи.
- 2026-05-30: Добавлен `scripts/check-memory-needed.py`, чтобы durable plan/spec/rule changes не проходили без `docs/agent-memory/`.

## Verification

В этой сессии использовался bundled Python, потому что `python` в PATH резолвился в Windows Store shim; у пользователя установлен Python через Anaconda, поэтому обычные команды в документации оставлены как `python ...`.

Проверено:

- `python -m unittest discover -s scripts\tests` через bundled Python: tests OK.
- `python scripts\lint-wiki.py --root .` через bundled Python: `Wiki lint passed.`
- `python scripts\check-memory-needed.py --check` через bundled Python: `Memory update check passed.`
- `.obsidian/*.json` успешно читаются как JSON.
- `rg "Polus|Geoportal|Геопортал|Полюс"` по перенесенным файлам: совпадений нет.

Donor repository `C:\Repositories\ai-po-template-experiments` при проверке `git status --short` был не clean, но в рамках этой реализации туда не вносились правки и ничего в donor-дереве не откатывалось.

## Retrieval Hints

knowledge pipeline, wiki, Obsidian graph, repository-change ingest, agent calls ingest, lint-wiki, check-memory-needed, RAW_inputs, Vision_wiki, Code_wiki
