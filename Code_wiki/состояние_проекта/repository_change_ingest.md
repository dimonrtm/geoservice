---
title: Repository Change Ingest
type: state
status: active
created: 2026-05-30
updated: 2026-05-31
source: "git status/diff, 2026-05-30; 2026-05-31"
tags: [repository-change, code-wiki, ingest]
---

# Repository Change Ingest

Журнал значимых изменений репозитория, которые агент фиксирует через `/ingest repository-change` после полного завершения реализации плана или крупной задачи.

Pre-commit не запускает и не проверяет этот процесс. Ответственность за запись лежит на агенте.

## Записи

### 2026-05-31 - `/discover --phase Ф1`: исследовательские цели

**Источник:** ответы пользователя на `/discover --phase Ф1`, `git status --short`, `git diff --stat`.

**Кратко:** зафиксировано, что GeoService является исследовательским pet-проектом для изучения алгоритмов совместного редактирования геометрии и проверки AI-first разработки сложной геоинформационной системы. Внешняя пользовательская боль пока не подтверждена.

**Затронутые области:**

- `Vision_wiki/chats/2026-05-31-phase-f1-why-now.md` - сводка ответов Ф1.
- `Vision_wiki/concepts/about_project.md`, `product_vision_board.md`, `lean_canvas.md` - продуктовый контекст и гипотезы.
- `Vision_wiki/decisions/risk_assumption_log.md`, `followups/index.md` - риски, assumptions и следующие вопросы.
- `Vision_wiki/index.md`, `memory/project-state.md`, `docs/agent-memory/` - индексы, live state и долговременная память.

**Что помнить дальше:**

- Не приписывать GeoService подтвержденную внешнюю пользовательскую боль до Ф2-Ф3.
- Следующая фаза: Ф2 пользователи и боль.
- Критерий первого релиза "все типа работает" нужно заменить на проверяемый demo-script и acceptance criteria.

**Проверка:** `python scripts/lint-wiki.py --root .` через bundled Python - `Wiki lint passed.`; `python -m unittest discover -s scripts\tests` - 8 tests OK; `python scripts/check-memory-needed.py --check` - passed; `git diff --check` - без ошибок.

### 2026-05-31 - Первичный `/discover` и уточнение Release 1

**Источник:** ответы пользователя на первичную анкету `/discover`, `git status --short`, `git diff --stat`.

**Кратко:** зафиксирован стартовый discovery-контекст GeoService: это pet-проект на стадии идея / прототип, владельцем решений является разработчик Попов Дмитрий. Пользователь подтвердил актуальность `RAW_inputs/documents/спринт 1.odt` и уточнил, что документ описывает план первого релиза, а не спринта.

**Затронутые области:**

- `Vision_wiki/chats/2026-05-31-initial-discover.md`, `Vision_wiki/concepts/about_project.md`, `Vision_wiki/entities/stakeholders/dmitry_popov.md` - базовый discovery-контекст.
- `Vision_wiki/chats/2026-05-30-release-1-document.md`, `Vision_wiki/concepts/first_release_mvp.md`, `Vision_wiki/solution/` - продуктовая терминология Release 1.
- `Code_wiki/архитектура/api_contract_first_release_requirements.md` - desired API contract первого релиза.
- `RAW_inputs/index.md`, `Vision_wiki/index.md`, `Code_wiki/index.md`, `memory/project-state.md`, `docs/agent-memory/` - индексы, live state и долговременная память.

**Что помнить дальше:**

- Имя RAW-файла `RAW_inputs/documents/спринт 1.odt` не меняется: исходные материалы остаются неизменяемыми.
- Следующие discovery-фазы: Ф1 проблема и why-now, Ф2 пользователи и боль, Ф3 альтернативы и контекст использования.
- Точный тип продукта пока не определен и не должен угадываться до прохождения Ф1-Ф3.

**Проверка:** `python scripts/lint-wiki.py --root .` через bundled Python - `Wiki lint passed.`; `python -m unittest discover -s scripts\tests` - 8 tests OK; `python scripts/check-memory-needed.py --check` - passed; `git diff --check` - без ошибок; поиск stale renamed-node references в активной wiki - совпадений нет.

### 2026-05-30 - Project knowledge wiki pipeline

**Источник:** `git status --short`, `git diff --stat`, результаты проверок 2026-05-30.

**Кратко:** в репозиторий GeoService перенесена шаблонная структура project knowledge wiki и ручной pipeline `/discover`, `/ingest`, `/sync-vision`, `/lint-wiki` без привязки к donor-проекту `C:\Repositories\ai-po-template-experiments`. Wiki ведётся на русском языке, при этом пути, команды, API, идентификаторы и имена файлов не переводятся.

**Затронутые области:**

- `RAW_inputs/`, `Vision_wiki/`, `Code_wiki/`, `memory/`, `Общие_принципы/` - структура базы знаний, шаблоны и индексы.
- `.agents/skills/source-command-*` - repo-local инструкции для ручных команд `/discover`, `/ingest`, `/sync-vision`, `/lint-wiki`.
- `.obsidian/` - конфигурация Obsidian graph для wiki.
- `docs/knowledge-pipeline/README.md`, `AGENTS.md`, `README.md`, `CONTRIBUTING.md` - правила работы с pipeline.
- `docs/agent-memory/` - память о правилах: планы на русском, обязательная запись важных решений, корректный режим `/discover`, полнота skill-системы, agent-driven `repository-change ingest`.
- `scripts/lint-wiki.py`, `scripts/check-memory-needed.py` и `scripts/tests/` - проверки wiki и обязательности memory updates.

**Важное решение:** `repository-change ingest` не выполняется Python-скриптом, не запускается pre-commit и не проверяется pre-commit hook. После полного завершения реализации плана или крупной задачи агент должен сам вызвать `/ingest repository-change` через skill `source-command-ingest` перед финальным отчётом пользователю. Не вызывать после каждого мелкого шага.

**Удалено как устаревшее:** `scripts/repository_change_ingest.py`, `scripts/prepare_commit.cmd`, `scripts/tests/test_repository_change_ingest.py`, local pre-commit hook `repository-change-ingest-guard`.

**Риски и что помнить дальше:**

- В старом файле плана `docs/superpowers/plans/2026-05-30-project-knowledge-wiki-pipeline.md` остались исторические шаги про Python/pre-commit, но в начале файла добавлена актуализация, которая их supersede'ит.
- Donor-репозиторий `C:\Repositories\ai-po-template-experiments` остаётся только read-only reference; туда нельзя вносить правки и нельзя переносить project-specific факты.
- После `/ingest` old documentation можно исправлять только по конфликтам, которые уже есть в `Vision_wiki/decisions/followups/index.md`, связаны с `Code_wiki` и разрешимы из новых знаний. Код, конфигурация, миграции и тесты требуют отдельной implementation task.

**Проверка:** `python -m unittest discover -s scripts\tests` - 8 tests OK; `python scripts\lint-wiki.py --root .` - `Wiki lint passed.`; `python scripts\check-memory-needed.py --check` - passed; `git diff --check` - без ошибок.

### 2026-05-30 - Аудит полноты source-command skills

**Источник:** повторная сверка `.agents/skills/source-command-*` с `C:\Repositories\ai-po-template-experiments`, проверка supporting-файлов и актуальных инструкций 2026-05-30.

**Кратко:** в GeoService присутствуют все четыре repo-local skills из reference-подхода: `/discover`, `/ingest`, `/sync-vision`, `/lint-wiki`. Для них созданы нужные wiki-директории, шаблоны, solution-артефакты, методические файлы, Obsidian config, linter и memory-check. Проверено, что skills не ссылаются на отсутствующие helper-файлы.

**Что важно помнить:**

- Reference-репозиторий содержит `scripts/ingest-raw.sh`, `.claude/commands/` и `.claude/agents/`, но текущие Codex skills на них не ссылаются. Это Claude Code-specific окружение, а не обязательная зависимость для `.agents/skills`.
- Изменения в самом репозитории попадают в базу знаний через agent-driven `/ingest repository-change` после полного завершения плана или крупной задачи. Это не git hook и не фоновый daemon: если изменения сделаны человеком без агента, нужно вручную попросить агента выполнить `/ingest repository-change` или запустить соответствующий workflow.
- Единственный исправленный найденный недочет: `docs/agent-memory/file-map.md` больше не называет `.pre-commit-config.yaml` частью wiki automation, потому что repository-change ingest отвязан от pre-commit.

### 2026-05-30 - Добавлен `/ingest repository-snapshot`

**Источник:** запрос пользователя о том, как добавлять в базу знаний уже существующие неизмененные данные репозитория.

**Кратко:** добавлен режим `/ingest repository-snapshot` для первичной или периодической инвентаризации текущего состояния репозитория. Он дополняет `/ingest repository-change`: snapshot работает с уже существующей кодовой базой, change работает с завершенными изменениями через `git status`/`git diff`.

**Затронутые области:**

- `.agents/skills/source-command-ingest/SKILL.md` - добавлен алгоритм `repository-snapshot`.
- `docs/knowledge-pipeline/README.md`, `AGENTS.md`, `README.md` - описано, когда вызывать snapshot.
- `Code_wiki/состояние_проекта/repository_snapshot.md` - создан журнал snapshot'ов.
- `Code_wiki/index.md`, `Code_wiki/состояние_проекта/_info.md` - добавлены ссылки на журналы snapshot/change.
- `memory/project-state.md` и `docs/agent-memory/file-map.md` - обновлены навигационные и state-записи.
- `docs/agent-memory/decisions/2026-05-30-repository-snapshot-ingest.md` - сохранено durable решение.

**Что помнить дальше:** `/ingest repository-snapshot` не индексирует весь код дословно и не меняет код/конфигурацию/миграции/тесты. Он создает технические wiki-ноды о текущей архитектуре, dev setup, сборке, deployment, API, моделях, тестах, правилах и рисках.

**Проверка:** `python scripts/lint-wiki.py --root .` - passed; `python -m unittest discover -s scripts\tests` - 8 tests OK; `python scripts/check-memory-needed.py --check` - passed; `git diff --check` - без ошибок.

### 2026-05-30 - Batch-режим `/ingest` без параметров для RAW_inputs

**Источник:** запрос пользователя: `/ingest` без параметров должен обрабатывать все новые `RAW_inputs` по очереди, если их немного; если файлов много или есть неоднозначность, нужно показать список и попросить подтверждение.

**Кратко:** обновлено поведение `/ingest` без параметров. Теперь агент ищет новые или измененные RAW-файлы, которых еще нет в обработанных source-записях wiki/state. Если найдено 1-5 однозначных кандидатов, они обрабатываются по очереди в одном запуске `/ingest`. Если кандидатов больше 5 или есть неоднозначность, агент сначала показывает список и просит подтверждение.

**Затронутые области:**

- `.agents/skills/source-command-ingest/SKILL.md` - уточнен шаг определения объекта ingest.
- `docs/knowledge-pipeline/README.md` - добавлен раздел `/ingest` без параметров.
- `AGENTS.md` - добавлена краткая инструкция для будущих агентов.
- `docs/agent-memory/file-map.md` - добавлена навигационная запись для batch RAW ingest.
- `docs/agent-memory/decisions/2026-05-30-raw-inputs-batch-ingest.md` - сохранено durable решение.

**Что помнить дальше:** если новых RAW-кандидатов нет, `/ingest` без параметров ничего не меняет и сообщает, что ingest не выполнен. Он может предложить явный путь, `/ingest repository-snapshot` или `/ingest repository-change`, но не должен создавать пустые wiki-правки.

**Проверка:** `python scripts/lint-wiki.py --root .` - passed; `python -m unittest discover -s scripts\tests` - 8 tests OK; `python scripts/check-memory-needed.py --check` - passed; `git diff --check` - без ошибок.
