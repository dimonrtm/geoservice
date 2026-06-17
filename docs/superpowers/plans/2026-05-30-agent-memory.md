# План Реализации Памяти Агентов

> **Для агентных исполнителей:** ОБЯЗАТЕЛЬНЫЙ SUB-SKILL: используйте `superpowers:subagent-driven-development` (рекомендуется) или `superpowers:executing-plans`, чтобы выполнять этот план по задачам. Шаги используют чекбоксы (`- [ ]`) для отслеживания прогресса.

**Цель:** создать repo-local, Git-versioned Markdown-память, которая помогает агентам восстанавливать релевантный контекст, находить связанные файлы и записывать долгосрочно полезные итоги после значимой работы.

**Архитектура:** система памяти строится как документация: короткий корневой `AGENTS.md` направляет агента в `docs/agent-memory/protocol.md`, а `docs/agent-memory/file-map.md` даёт экономный по токенам поиск “тема -> файлы”. Долговременные записи лежат как Markdown-файлы в папках `sessions/`, `decisions/`, `patterns/`, `bugfixes/`; retrieval выполняется через точечные `rg`-поиски без CLI, базы данных, JSONL-индекса или embeddings.

**Технологии:** Markdown, Git, `rg`, PowerShell для локальной проверки.

---

## Проверка Области

Этот план реализует одну подсистему: Markdown-based workflow долговременной памяти агентов. Он не добавляет CLI, JSONL-индекс, generated index, базу данных, embeddings, CI job или package dependency.

Существующее удаление `docs/codex-agent-long-term-memory-plan.md` намеренно находится вне этого плана. Не восстанавливать этот файл и не включать его в коммит memory-системы, если пользователь явно не попросит.

## Структура Файлов

- Создать `AGENTS.md`: короткая корневая точка входа для агентов.
- Создать `docs/agent-memory/README.md`: человекочитаемый обзор области памяти.
- Создать `docs/agent-memory/protocol.md`: главный workflow чтения, записи, приватности и проверок.
- Создать `docs/agent-memory/file-map.md`: компактная карта “topic/tag -> files”.
- Создать `docs/agent-memory/sessions/.gitkeep`: удерживает папку `sessions` в Git.
- Создать `docs/agent-memory/decisions/.gitkeep`: удерживает папку `decisions` в Git.
- Создать `docs/agent-memory/patterns/.gitkeep`: удерживает папку `patterns` в Git.
- Создать `docs/agent-memory/bugfixes/.gitkeep`: удерживает папку `bugfixes` в Git.
- Создать `docs/agent-memory/decisions/2026-05-30-agent-memory-operating-rules.md`: seed decision memory с утверждёнными правилами.
- Создать `docs/agent-memory/sessions/2026-05-30-agent-memory-mvp.md`: итоговая session memory после проверки внедрения.
- Изменить `README.md`: добавить ссылку на документацию agent-memory.

## Задачи Реализации

### Задача 1: Создать Входную Точку И Папки

**Файлы:**

- Создать: `AGENTS.md`
- Создать: `docs/agent-memory/sessions/.gitkeep`
- Создать: `docs/agent-memory/decisions/.gitkeep`
- Создать: `docs/agent-memory/patterns/.gitkeep`
- Создать: `docs/agent-memory/bugfixes/.gitkeep`

- [ ] **Шаг 1: Создать папки**

Выполнить:

```powershell
New-Item -ItemType Directory -Force docs\agent-memory\sessions | Out-Null
New-Item -ItemType Directory -Force docs\agent-memory\decisions | Out-Null
New-Item -ItemType Directory -Force docs\agent-memory\patterns | Out-Null
New-Item -ItemType Directory -Force docs\agent-memory\bugfixes | Out-Null
```

Ожидаемый результат: команда завершается с кодом `0`.

- [ ] **Шаг 2: Создать `.gitkeep` файлы**

Выполнить:

```powershell
New-Item -ItemType File -Force docs\agent-memory\sessions\.gitkeep | Out-Null
New-Item -ItemType File -Force docs\agent-memory\decisions\.gitkeep | Out-Null
New-Item -ItemType File -Force docs\agent-memory\patterns\.gitkeep | Out-Null
New-Item -ItemType File -Force docs\agent-memory\bugfixes\.gitkeep | Out-Null
```

Ожидаемый результат: команда завершается с кодом `0`.

- [ ] **Шаг 3: Создать `AGENTS.md`**

Записать точное содержимое:

```markdown
# Agent Instructions

Before working in this repository:

1. Read `docs/agent-memory/protocol.md`.
2. Search `docs/agent-memory/file-map.md` and memory entries for context related to the user's request.
3. Read only the memory entries that are relevant to the request.
4. After significant work, add or update a memory entry.

Significant work means context that will still help in a week: decisions, bug root causes, non-obvious file relationships, important commands, or stable project patterns. Do not store secrets, full chats, temporary logs, or unverified guesses.
```

- [ ] **Шаг 4: Проверить входную точку и папки**

Выполнить:

```powershell
Test-Path AGENTS.md
Test-Path docs\agent-memory\sessions\.gitkeep
Test-Path docs\agent-memory\decisions\.gitkeep
Test-Path docs\agent-memory\patterns\.gitkeep
Test-Path docs\agent-memory\bugfixes\.gitkeep
```

Ожидаемый вывод:

```text
True
True
True
True
True
```

### Задача 2: Написать Протокол Памяти

**Файлы:**

- Создать: `docs/agent-memory/protocol.md`

- [ ] **Шаг 1: Создать `protocol.md`**

Записать точное содержимое:

```markdown
# Agent Memory Protocol

This repository uses local Markdown files as long-term memory for agents. The memory is part of the Git repository and must stay readable by humans.

## Start Of Work

At the start of a new chat or task:

1. Read `AGENTS.md`.
2. Read this protocol.
3. Extract 3-8 search terms from the user's request: feature names, errors, domains, technologies, file names, or module names.
4. Search the memory area with `rg`.
5. Prefer `docs/agent-memory/file-map.md` for fast topic-to-file lookup.
6. Read only memory entries that are relevant to the current request.
7. Continue normal repository exploration with `rg`.

Example searches:

```powershell
rg -n "realtime|websocket|typecheck" docs/agent-memory
rg -n "auth|login|jwt" docs/agent-memory/file-map.md docs/agent-memory
```

Do not load every memory entry and do not read recent entries without a reason.

## What To Store

Store durable context that will still help in a week:

- architectural and product decisions;
- bug symptoms, root cause, fix, and verification;
- non-obvious relationships between files;
- important commands for running, checking, or debugging the project;
- stable implementation patterns already used in this repository;
- project constraints that affect future work.

Do not store:

- full chat transcripts;
- temporary reasoning or discarded scratch work;
- small mechanical actions with no durable value;
- secrets, tokens, passwords, API keys, `.env` values, or personal data;
- build output, noisy logs, or unverified guesses.

## When To Write Memory

After significant work, add or update a memory entry yourself. Significant work means the result is likely to help the next agent understand what happened, why it matters, and which files are involved.

Use these folders:

- `docs/agent-memory/sessions/` for summaries of significant completed work;
- `docs/agent-memory/decisions/` for architectural and product decisions;
- `docs/agent-memory/patterns/` for repeated implementation rules;
- `docs/agent-memory/bugfixes/` for bug root causes and fixes.

Use filenames in this format:

```text
YYYY-MM-DD-short-ascii-slug.md
```

Examples:

```text
2026-05-30-agent-memory-operating-rules.md
2026-05-30-realtime-typecheck-fix.md
```

## Entry Template

```markdown
# Short Title

Date: YYYY-MM-DD
Type: session | decision | pattern | bugfix
Tags: frontend, realtime, websocket
Related files:

- `apps/frontend/src/example.ts`

## Summary

Коротко, что должен помнить следующий агент.

## Context

Почему это важно и когда применять.

## Actions

- YYYY-MM-DD: Что было сделано и результат.

## Verification

Команды проверки и итог. Если не проверялось, явно указать почему.

## Retrieval Hints

Слова и фразы, по которым эту запись должен найти будущий агент.
```

Human-facing fields should use the main language of the chat, usually Russian in this repository. Do not translate paths, commands, APIs, identifiers, or type names.

## File Map

Update `docs/agent-memory/file-map.md` when work creates or changes a durable topic-to-file relationship.

Keep entries compact:

```markdown
- map realtime websocket: `apps/frontend/src/composables/map/useLayerRealtime.ts`, `apps/frontend/src/contracts/realtime.ts`
```

The file map is not a history log. It is a quick navigation aid.

## Superseding Memory

Do not delete old memory entries only because they became outdated. If a new entry replaces an old one, add this metadata line to the old entry:

```markdown
Superseded by: docs/agent-memory/<folder>/<new-entry>.md
```

Delete a memory entry only when it was accidental, contains a secret, or is clearly harmful.

## Manual Check Before Finishing

Before finishing work that changed memory, check:

- the entry is in the correct folder;
- the filename matches `YYYY-MM-DD-short-ascii-slug.md`;
- all required sections are present;
- `Related files` exist or are explicitly described as planned files;
- `file-map.md` is updated when durable file relationships changed;
- the entry contains no secrets, full chats, noisy logs, or unverified guesses;
- the entry is useful beyond the current chat.
```

- [ ] **Шаг 2: Проверить, что протокол ищется**

Выполнить:

```powershell
rg -n "Start Of Work|What To Store|Entry Template|Manual Check" docs\agent-memory\protocol.md
```

Ожидаемый результат: вывод содержит все четыре заголовка.

### Задача 3: Создать Компактную Карту Файлов

**Файлы:**

- Создать: `docs/agent-memory/file-map.md`

- [ ] **Шаг 1: Создать `file-map.md`**

Записать точное содержимое:

```markdown
# File Map

Compact topic-to-file map for agent retrieval. Keep entries short and update only when durable relationships change.

## Agent Memory

- agent memory protocol workflow: `AGENTS.md`, `docs/agent-memory/protocol.md`
- agent memory quick file lookup: `docs/agent-memory/file-map.md`
- agent memory design spec: `docs/superpowers/specs/2026-05-30-agent-memory-design.md`

## Project Documentation

- product requirements planning: `docs/requirements/geoservice-prd-v1.md`, `docs/requirements/geoservice-requirements.md`, `docs/requirements/action-plan.md`
- legacy generic sprint 1 plans: `docs/release_1/sprint_1/legacy-generic-plan/sprint-1-plan.md`, `docs/release_1/sprint_1/legacy-generic-plan/day-8-plan.md`
- project overview: `README.md`, `docs/project-description.md`

## Backend

- FastAPI app entry lifecycle: `apps/backend/app/main.py`, `apps/backend/app/api/lifespan.py`
- backend settings configuration: `apps/backend/app/core/settings.py`
- auth login users jwt: `apps/backend/app/api/auth.py`, `apps/backend/app/services/auth_service.py`, `apps/backend/app/repositories/user_repository.py`, `apps/backend/app/models/user.py`
- demo user seed: `apps/backend/app/seed_demo_users.py`, `apps/backend/app/services/demo_user_seed_service.py`
- layers API service repository: `apps/backend/app/api/layers.py`, `apps/backend/app/services/layer_service.py`, `apps/backend/app/repositories/layer_repository.py`, `apps/backend/app/models/layer.py`
- feature CRUD storage: `apps/backend/app/services/feature_service.py`, `apps/backend/app/domain/feature_registry.py`, `apps/backend/app/models/feature_point.py`, `apps/backend/app/models/feature_polygon.py`
- websocket layer realtime auth: `apps/backend/app/api/ws_layers.py`, `apps/backend/app/api/websocket_auth.py`, `apps/backend/app/services/realtime_connection_manager.py`
- realtime feature publishing: `apps/backend/app/services/feature_realtime_publisher.py`
- backend tests auth realtime features: `apps/backend/app/tests/test_auth_service.py`, `apps/backend/app/tests/test_websocket_auth.py`, `apps/backend/app/tests/test_ws_layers.py`, `apps/backend/app/tests/test_feature_service.py`

## Frontend

- Vue app entry: `apps/frontend/src/main.ts`, `apps/frontend/src/App.vue`, `apps/frontend/src/pinia.ts`
- auth login state API: `apps/frontend/src/stores/auth.ts`, `apps/frontend/src/api/auth.ts`, `apps/frontend/src/components/LoginScreen.vue`
- map page composition: `apps/frontend/src/components/MapPageView.vue`, `apps/frontend/src/components/MapView.vue`
- map instance style layers: `apps/frontend/src/composables/map/useMapInstance.ts`, `apps/frontend/src/composables/map/mapStyle.ts`, `apps/frontend/src/map/maplibrelayers.ts`
- layer selection loading cache: `apps/frontend/src/composables/map/useLayerSelection.ts`, `apps/frontend/src/composables/map/useFeatureLoading.ts`, `apps/frontend/src/composables/map/useFeatureTileCache.ts`
- frontend realtime websocket: `apps/frontend/src/composables/map/useLayerRealtime.ts`, `apps/frontend/src/contracts/realtime.ts`, `apps/frontend/src/contracts/map-cache.ts`
- polygon editing: `apps/frontend/src/composables/map/usePolygonEditing.ts`, `apps/frontend/src/map/polygon-editing.ts`, `apps/frontend/src/stores/edit.ts`
- frontend API contracts: `apps/frontend/src/contracts/api.ts`, `apps/frontend/src/contracts/geojson.ts`, `apps/frontend/src/api/http.ts`, `apps/frontend/src/api/layers.ts`
- frontend tests realtime auth editing: `apps/frontend/src/composables/map/useLayerRealtime.test.ts`, `apps/frontend/src/stores/auth.test.ts`, `apps/frontend/src/stores/edit.test.ts`

## Infra

- docker compose local dev: `infra/docker-compose.yml`, `infra/docker-compose.override.yml`, `infra/dev-up.cmd`, `scripts/dev.cmd`
- postgis init: `infra/docker/postgis/init/01-postgis.sql`
```

- [ ] **Шаг 2: Проверить, что указанные файлы существуют**

Выполнить:

```powershell
rg -o '`([^`]+)`' docs\agent-memory\file-map.md | ForEach-Object { $_.Trim('`') } | Where-Object { -not (Test-Path $_) }
```

Ожидаемый результат: нет вывода.

- [ ] **Шаг 3: Проверить retrieval по `file-map.md`**

Выполнить:

```powershell
rg -n "frontend realtime websocket|auth login state API|feature CRUD storage" docs\agent-memory\file-map.md
```

Ожидаемый результат: вывод содержит по одной строке для каждой темы.

### Задача 4: Создать Человекочитаемый README

**Файлы:**

- Создать: `docs/agent-memory/README.md`

- [ ] **Шаг 1: Создать `README.md`**

Записать точное содержимое:

```markdown
# Agent Memory

This directory stores long-term memory for agents working in the GeoService repository.

The memory is local to this repository, versioned in Git, and written as Markdown. It is intentionally simple: no CLI, no JSONL index, no database, no embeddings, and no external service.

## Files

- `protocol.md` - authoritative workflow for reading and writing memory.
- `file-map.md` - compact topic-to-file map for fast retrieval.
- `sessions/` - summaries of significant completed work.
- `decisions/` - architectural and product decisions.
- `patterns/` - repeated implementation rules.
- `bugfixes/` - bug symptoms, root causes, fixes, and verification.

## Agent Start

Agents should start with:

```powershell
rg -n "<request terms>" docs/agent-memory
```

Read `protocol.md` first, then use `file-map.md` and relevant memory entries. Do not load every entry without a reason.

## Writing Memory

After significant work, add a Markdown entry using the template in `protocol.md`. Significant work means context that will still be useful in a week.

Do not store secrets, full chats, noisy logs, or unverified guesses.
```

- [ ] **Шаг 2: Проверить, что README указывает на протокол и карту файлов**

Выполнить:

```powershell
rg -n "protocol.md|file-map.md|no CLI|no JSONL|no database|no embeddings" docs\agent-memory\README.md
```

Ожидаемый результат: вывод содержит все искомые фразы.

### Задача 5: Добавить Seed Decision Memory

**Файлы:**

- Создать: `docs/agent-memory/decisions/2026-05-30-agent-memory-operating-rules.md`

- [ ] **Шаг 1: Создать seed decision-запись**

Записать точное содержимое:

```markdown
# Правила Работы Долговременной Памяти Агентов

Date: 2026-05-30
Type: decision
Tags: agent-memory, workflow, markdown, retrieval, git
Related files:

- `AGENTS.md`
- `docs/agent-memory/protocol.md`
- `docs/agent-memory/file-map.md`
- `docs/superpowers/specs/2026-05-30-agent-memory-design.md`

## Summary

Память агентов в GeoService хранится строго внутри репозитория как Markdown и версионируется через Git. Новый чат читает минимальный протокол, делает поиск по запросу пользователя и не загружает всю память без причины.

## Context

Пользователь выбрал новый дизайн с нуля: без восстановления старого плана, без CLI, JSONL, базы данных, embeddings и внешних зависимостей. Записи добавляются агентом самостоятельно после значимой работы, если контекст будет полезен через неделю.

## Actions

- 2026-05-30: Зафиксировано, что память должна быть repo-local и Git-versioned.
- 2026-05-30: Выбран ручной Markdown-формат записей.
- 2026-05-30: Выбран компактный `file-map.md` как самый экономный по токенам способ находить связанные файлы.
- 2026-05-30: Выбрана структура `sessions/`, `decisions/`, `patterns/`, `bugfixes/`.

## Verification

Проверяется smoke-поиском после внедрения:

```powershell
rg -n "repo-local|Markdown|file-map|значимой работы" docs/agent-memory
```

Ожидается, что поиск находит эту запись и протокол памяти.

## Retrieval Hints

agent memory, долговременная память, repo-local, markdown memory, file-map, significant work, значимая работа, протокол памяти, новый чат, Git-versioned memory
```

- [ ] **Шаг 2: Проверить, что seed memory находится поиском**

Выполнить:

```powershell
rg -n "repo-local|Markdown|file-map|значимой работы" docs\agent-memory
```

Ожидаемый результат: вывод включает `docs/agent-memory/decisions/2026-05-30-agent-memory-operating-rules.md`.

### Задача 6: Добавить Ссылку На Agent Memory В Корневой README

**Файлы:**

- Изменить: `README.md`

- [ ] **Шаг 1: Добавить agent memory в список документации**

В разделе `## Документация` добавить этот пункт после `project-description.md`:

```markdown
- [agent-memory](docs/agent-memory/README.md)
```

Итоговый список должен включать:

```markdown
- [project-description.md](C:/Repositories/geoservice/docs/project-description.md)
- [agent-memory](docs/agent-memory/README.md)
- [action-plan.md](C:/Repositories/geoservice/docs/requirements/action-plan.md)
- [requirements-compliance-audit.md](C:/Repositories/geoservice/docs/requirements/requirements-compliance-audit.md)
- [sprint-1-plan.md](C:/Repositories/geoservice/docs/release_1/sprint_1/legacy-generic-plan/sprint-1-plan.md)
```

- [ ] **Шаг 2: Проверить ссылку в корневом README**

Выполнить:

```powershell
rg -n "agent-memory" README.md
```

Ожидаемый результат: вывод содержит новый пункт документации.

### Задача 7: Запустить Smoke-Проверки Retrieval

**Файлы:**

- Читать: `AGENTS.md`
- Читать: `docs/agent-memory/protocol.md`
- Читать: `docs/agent-memory/file-map.md`
- Читать: `docs/agent-memory/decisions/2026-05-30-agent-memory-operating-rules.md`

- [ ] **Шаг 1: Проверить, что стартовый workflow обнаруживается**

Выполнить:

```powershell
rg -n "protocol.md|file-map.md|significant work|значим" AGENTS.md docs\agent-memory
```

Ожидаемый результат: вывод включает `AGENTS.md`, `docs/agent-memory/protocol.md` и `docs/agent-memory/decisions/2026-05-30-agent-memory-operating-rules.md`.

- [ ] **Шаг 2: Проверить task-oriented lookup файлов**

Выполнить:

```powershell
rg -n "frontend realtime websocket|websocket layer realtime auth|polygon editing|docker compose local dev" docs\agent-memory\file-map.md
```

Ожидаемый результат: вывод включает четыре строки из `docs/agent-memory/file-map.md`.

- [ ] **Шаг 3: Проверить, что память не вводит исключённые MVP-механизмы**

Выполнить:

```powershell
rg -n "no CLI|no JSONL|no database|no embeddings|external service" AGENTS.md docs\agent-memory
```

Ожидаемый результат: совпадения встречаются только в пояснениях формата “не используется”; не должно быть инструкций создавать или запускать эти механизмы.

### Задача 8: Добавить Итоговую Session Memory По Внедрению

**Файлы:**

- Создать: `docs/agent-memory/sessions/2026-05-30-agent-memory-mvp.md`

- [ ] **Шаг 1: Создать session memory-запись**

Записать точное содержимое после успешного выполнения Задач 1-7:

```markdown
# Agent Memory MVP

Date: 2026-05-30
Type: session
Tags: agent-memory, markdown, documentation, retrieval, workflow
Related files:

- `AGENTS.md`
- `docs/agent-memory/README.md`
- `docs/agent-memory/protocol.md`
- `docs/agent-memory/file-map.md`
- `docs/agent-memory/decisions/2026-05-30-agent-memory-operating-rules.md`
- `README.md`

## Summary

В репозитории внедрена Markdown-память агентов: короткий `AGENTS.md`, общий протокол, компактный `file-map.md`, папки для записей и первая decision-запись с правилами работы памяти.

## Context

Память нужна, чтобы новые чаты быстро восстанавливали релевантный контекст по запросу пользователя, находили связанные файлы и сохраняли только долгосрочно полезные итоги после значимой работы.

## Actions

- 2026-05-30: Добавлен корневой `AGENTS.md` как входная инструкция для агентов.
- 2026-05-30: Добавлен `docs/agent-memory/protocol.md` с правилами чтения, записи, приватности и ручной проверки.
- 2026-05-30: Добавлен `docs/agent-memory/file-map.md` для быстрого поиска файлов по темам.
- 2026-05-30: Добавлена seed decision-запись о правилах памяти.
- 2026-05-30: README получил ссылку на `docs/agent-memory/README.md`.

## Verification

Smoke-проверки:

```powershell
rg -n "protocol.md|file-map.md|significant work|значим" AGENTS.md docs/agent-memory
rg -n "frontend realtime websocket|websocket layer realtime auth|polygon editing|docker compose local dev" docs/agent-memory/file-map.md
rg -n "agent-memory" README.md
```

Ожидаемый результат: поиск находит стартовый протокол, карту файлов, seed decision и ссылку из README.

## Retrieval Hints

agent memory MVP, память агентов, AGENTS.md, protocol.md, file-map.md, markdown memory, retrieval workflow, значимая работа, новый чат
```

- [ ] **Шаг 2: Проверить, что session memory находится поиском**

Выполнить:

```powershell
rg -n "agent memory MVP|память агентов|retrieval workflow|значимая работа" docs\agent-memory
```

Ожидаемый результат: вывод включает `docs/agent-memory/sessions/2026-05-30-agent-memory-mvp.md`.

### Задача 9: Финальное Ревью И Передача Пользователю

**Файлы:**

- Проверить: все файлы, созданные или изменённые в Задачах 1-8.

- [ ] **Шаг 1: Проверить статус рабочей копии**

Выполнить:

```powershell
git status --short
```

Ожидаемый результат: вывод включает новые файлы agent-memory. Также он может включать уже существующее удаление `docs/codex-agent-long-term-memory-plan.md`; не откатывать и не добавлять это удаление в индекс, если пользователь не попросит.

- [ ] **Шаг 2: Проверить diff памяти**

Выполнить:

```powershell
git diff -- AGENTS.md README.md docs\agent-memory
```

Ожидаемый результат: diff показывает только корневые инструкции агента, ссылку в README и Markdown-файлы памяти.

- [ ] **Шаг 3: Сделать commit checkpoint после подтверждения пользователя**

Если пользователь хочет коммит для memory MVP, выполнить:

```powershell
git add AGENTS.md README.md docs\agent-memory
git commit -m "docs: add agent memory workflow"
```

Ожидаемый результат: коммит проходит успешно и не включает несвязанные staged или unstaged изменения. Если `git status --short` показывает несвязанные staged changes перед коммитом, сначала спросить пользователя.

## Self-Review Плана

- Покрытие спецификации: Задачи 1-8 реализуют `AGENTS.md`, `protocol.md`, `file-map.md`, разделение папок, ручные Markdown-записи, запись после значимой работы, отсутствие CLI/JSONL/database/embeddings, privacy rules и smoke-проверки retrieval.
- Placeholder scan: план не содержит red-flag markers и не содержит неопределённых шагов “добавить тесты позже”.
- Проверка согласованности: все пути соответствуют утверждённой структуре из `docs/superpowers/specs/2026-05-30-agent-memory-design.md`; старый `docs/codex-agent-long-term-memory-plan.md` остаётся вне плана.
