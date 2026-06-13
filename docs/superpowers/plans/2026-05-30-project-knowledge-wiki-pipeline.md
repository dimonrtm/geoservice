# План Реализации Project Knowledge Wiki Pipeline

> **Актуализация 2026-05-30:** разделы этого плана про Python-скрипт `scripts/repository_change_ingest.py`, `scripts/prepare_commit.cmd` и pre-commit guard устарели. Актуальное правило: после полного завершения реализации плана или крупной задачи агент вызывает `/ingest repository-change` через repo-local skill `source-command-ingest` перед финальным отчётом пользователю. Pre-commit не запускает и не проверяет repository-change ingest.

> **Для агентских исполнителей:** ОБЯЗАТЕЛЬНЫЙ ПОДНАВЫК: используйте `superpowers:subagent-driven-development` (рекомендуется) или `superpowers:executing-plans`, чтобы выполнять этот план по задачам. Шаги используют чекбоксы (`- [ ]`) для отслеживания прогресса.

**Цель:** Создать в GeoService структуру project knowledge wiki, ручные процедуры `/discover`, `/ingest`, `/sync-vision`, `/lint-wiki`, автоматический `repository-change ingest` и проверки, не изменяя `C:\Repositories\ai-po-template-experiments`.

**Архитектура:** В корне GeoService добавляется PO-style wiki рядом с существующей `docs/agent-memory/`. Ручные workflow описываются в Markdown runbook и repo-local skill-документации. Автоматический `repository-change ingest` реализуется детерминированным Python-скриптом, запускается подготовительным шагом перед pre-commit и пишет только knowledge-документацию; pre-commit содержит только guard-проверку.

**Стек:** Markdown, Python standard library, Git, существующий `.pre-commit-config.yaml`, PowerShell-команды для проверки.

**Язык Wiki:** Все человекочитаемые wiki-ноды, индексы, runbook'и, state-файлы и follow-up'ы ведутся на русском языке. Пути, команды, имена файлов, API, типы, идентификаторы, названия пакетов и код не переводятся.

---

## Структура Файлов

- Создать `index.md`: корневая точка входа в knowledge wiki GeoService.
- Изменить `AGENTS.md`: добавить инструкции для `docs/agent-memory/` и новой PO-style wiki.
- Изменить `README.md`: добавить ссылки на knowledge wiki и ручной pipeline.
- Изменить `.gitignore`: добавить ignore patterns для локальных agent/wiki/Obsidian/Python temporary files, если их нет.
- Изменить `CONTRIBUTING.md`: добавить style rules для wiki: русский контент, английские имена `_templates/` и `scripts/`, frontmatter, wikilinks.
- Создать `.obsidian/`: общая Obsidian vault-конфигурация для просмотра wiki-графа.
- Создать `RAW_inputs/`: область сырых источников с пустыми подпапками и `_info.md`.
- Создать `Vision_wiki/`: продуктовая/decision wiki со структурой, шаблонами, follow-up'ами, конфликтами, assumptions, entities и solution.
- Создать `Code_wiki/`: техническая wiki со структурой, шаблонами, архитектурой, dev setup, сборкой, deployment, стилем, glossary и состоянием проекта.
- Создать `memory/llm-wiki-method.md`: адаптированная методология LLM-wiki без фактов donor-проекта.
- Создать `memory/project-state.md`: начальное живое состояние GeoService.
- Создать `Общие_принципы/`: общие методические материалы на русском языке.
- Создать `.agents/skills/source-command-{discover,ingest,sync-vision,lint-wiki}/SKILL.md`: repo-local command docs для ручных процедур.
- Создать `docs/knowledge-pipeline/README.md`: пользовательский runbook для morning, meeting, post-meeting, weekly и repository-change сценариев.
- Создать `scripts/lint-wiki.py`: no-dependency linter для wiki.
- Создать `scripts/repository_change_ingest.py`: автоматический классификатор staged changes, writer knowledge-log и pre-commit guard.
- Создать `scripts/prepare_commit.cmd`: Windows helper для запуска `repository-change ingest` перед pre-commit.
- Создать `scripts/tests/test_lint_wiki.py`: standard-library тесты linter.
- Создать `scripts/tests/test_repository_change_ingest.py`: standard-library тесты automatic ingest.
- Изменить `.pre-commit-config.yaml`: добавить локальный guard hook для проверки, что `repository-change ingest` не пропущен.
- Изменить `docs/agent-memory/file-map.md`: добавить карту новых файлов knowledge pipeline.
- Обновить `docs/agent-memory/decisions/2026-05-30-agent-memory-operating-rules.md`: сохранить только устойчивые правила pipeline.
- Изменить `docs/agent-memory/protocol.md`: добавить явные triggers, когда memory entry обязательна.
- Создать `scripts/check-memory-needed.py`: предупреждение, если меняются планы/spec/rules без изменений в `docs/agent-memory/`.
- Создать `scripts/tests/test_check_memory_needed.py`: standard-library тесты для memory-needed проверки.

## Donor Script Inventory

Перед реализацией использовать `C:\Repositories\ai-po-template-experiments` только read-only и учитывать такую классификацию donor-файлов:

- `scripts/lint-wiki.py` - единственный обязательный donor script для переноса/адаптации. Нужен для `/lint-wiki`.
- `scripts/ingest-raw.sh` - не переносить как обязательный скрипт: это Claude Code wrapper (`claude -p "/ingest <file>"`), не подходящий напрямую для Windows/Codex workflow. Использовать только как reference.
- `.agents/skills/source-command-*/SKILL.md` и `.claude/commands/*.md` - переносить как reference для command docs/runbook, а не как исполняемые скрипты.
- `.codex/hooks.json` - не переносить как готовый hook: donor hook завязан на `PostToolUse`/`CLAUDE_TOOL_PATH` и не реализует наш automatic `repository-change ingest`.
- `.codex/config.toml` - не обязателен; идея `AI_PO_LOCALE=ru` полезна как reference, но язык wiki фиксируется в наших Markdown-инструкциях.
- `.claude/agents/*.md`, `.codex/agents/*.toml` - не нужны для выполнения pipeline; использовать только как reference при необходимости. Obsidian runtime не нужен для выполнения команд, но общий `.obsidian` config переносится отдельно, потому что нужен graph/navigation.
- `.cmd`, `.ps1`, `.bat` pipeline-скриптов в donor-репозитории не найдено.

Automatic `repository-change ingest` в donor-репозитории отсутствует; его нужно реализовать отдельно в GeoService.

## Pipeline Transfer Inventory

Для нормальной работы pipeline перенести или адаптировать из donor-репозитория нужно не только скрипт, но и supporting knowledge structure:

### Обязательно перенести/адаптировать

- `Vision_wiki/_templates/*` и `Code_wiki/_templates/*` - шаблоны для session, ADR, conflict, risk, runbook, service, API endpoint и postmortem нод.
- Все `_info.md` для пустых папок `RAW_inputs/`, `Vision_wiki/`, `Code_wiki/` - нужны для навигации и `lint-wiki`.
- `memory/llm-wiki-method.md` - методология атомарных нод, frontmatter, wikilinks, source и статусов.
- Command docs для `/discover`, `/ingest`, `/sync-vision`, `/lint-wiki` - взять из `.agents/skills/source-command-*` или `.claude/commands/*`, очистить от donor-фактов и адаптировать под ручной запуск.
- `RAW_inputs/index.md`, `Vision_wiki/index.md`, `Code_wiki/index.md`, корневой `index.md` - не копировать как есть, а переписать под GeoService.
- `memory/project-state.md` - создать как baseline state GeoService, не переносить donor state.
- `Vision_wiki/decisions/followups/index.md` - ключевой файл для post-ingest correction и очереди конфликтов.

### Желательно перенести/адаптировать

- `Общие_принципы/*` - методология подготовки встреч, вопросы стейкхолдеру и правила планирования; нужна для полноценного `/discover`.
- `.agents/skills/source-command-*` - локальные процедуры для агентов, чтобы `/ingest`, `/discover`, `/sync-vision`, `/lint-wiki` были discoverable.
- `scripts/README.md` - переписать под GeoService и описать `lint-wiki.py`, `repository_change_ingest.py`, `check-memory-needed.py`.
- `.gitignore` patterns из donor - добавить только недостающие правила для `.obsidian/workspace*.json`, `.obsidian/cache`, `__pycache__/`, `.venv/`, `venv/`, `*.tmp`, `*.bak`, `.claude/local/`, `memory/local/`.
- `CONTRIBUTING.md` style rules из donor - перенести смысл: Markdown без лишнего HTML, wikilinks, frontmatter, русский для содержимого, английский для имен файлов в `_templates/` и кода в `scripts/`, без emoji в именах файлов.
- `.obsidian/app.json`, `.obsidian/appearance.json`, `.obsidian/core-plugins.json`, `.obsidian/graph.json`, `.obsidian/templates.json` - перенести/адаптировать обязательно, потому что Obsidian нужен для графа wiki.

### Нужно реализовать в GeoService, потому что в donor этого нет

- `scripts/repository_change_ingest.py` - automatic repository-change ingest.
- `scripts/check-memory-needed.py` - предупреждение, если durable plan/spec/rule changes идут без `docs/agent-memory/`.
- Тесты для `lint-wiki.py`, `repository_change_ingest.py`, `check-memory-needed.py`.
- `scripts/prepare_commit.cmd` для запуска automatic `repository-change ingest` перед обычным pre-commit.
- Pre-commit guard для `repository-change ingest`: hook не пишет файлы, а проверяет, что для meaningful staged changes уже есть knowledge entry; если нет, печатает команду подготовки и возвращает ошибку.
- `repository-change ingest` должен быть идемпотентным, игнорировать knowledge-файлы и писать entry по fingerprint только один раз.

### Не переносить

- Project-specific donor ноды из `Vision_wiki/chats`, `Vision_wiki/concepts`, `Code_wiki/архитектура` и похожих папок.
- `scripts/ingest-raw.sh` как обязательный механизм; он завязан на Claude CLI.
- `.codex/hooks.json`; donor hook не подходит под наш automatic ingest.
- `.obsidian/workspace.json`, `.obsidian/workspace-mobile.json`, `.obsidian/cache`, `.obsidian/plugins/*/data.json` - не переносить как shared config; это пользовательское локальное состояние.
- `.claude/agents/*`, `.codex/agents/*`; использовать только как reference, не как runtime requirement.

## Задача 1: Создать Каркас Wiki И Базовые Файлы

**Файлы:**
- Создать: `index.md`
- Создать: `RAW_inputs/index.md`
- Создать: `RAW_inputs/meetings/_info.md`
- Создать: `RAW_inputs/documents/_info.md`
- Создать: `RAW_inputs/code/_info.md`
- Создать: `RAW_inputs/docs/_info.md`
- Создать: `RAW_inputs/chats/_info.md`
- Создать: `RAW_inputs/research_results/_info.md`
- Создать: `Vision_wiki/index.md`
- Создать: `Vision_wiki/decisions/followups/index.md`
- Создать: `Code_wiki/index.md`
- Создать: `memory/project-state.md`
- Создать: `.obsidian/app.json`
- Создать: `.obsidian/appearance.json`
- Создать: `.obsidian/core-plugins.json`
- Создать: `.obsidian/graph.json`
- Создать: `.obsidian/templates.json`

- [ ] **Шаг 0: Проверить donor script inventory read-only**

Запустить:

```powershell
Get-ChildItem -Recurse -File 'C:\Repositories\ai-po-template-experiments' -Include *.py,*.sh,*.cmd,*.ps1,*.bat,*.toml,*.json |
  Select-Object -ExpandProperty FullName
```

Ожидается: для pipeline есть `scripts/lint-wiki.py` и `scripts/ingest-raw.sh`; `.cmd`, `.ps1`, `.bat` pipeline-скриптов нет. Не редактировать файлы в `C:\Repositories\ai-po-template-experiments`.

- [ ] **Шаг 0.1: Сверить pipeline transfer inventory**

Проверить, что план реализации покрывает mandatory items:

```powershell
rg -n "Vision_wiki/_templates|Code_wiki/_templates|_info.md|llm-wiki-method|source-command|project-state|followups/index|repository_change_ingest|check-memory-needed" docs/superpowers/plans/2026-05-30-project-knowledge-wiki-pipeline.md
```

Ожидается: все обязательные supporting components найдены в плане.

- [ ] **Шаг 0.2: Создать Obsidian config для wiki graph**

Создать `.obsidian/app.json`:

```json
{
  "alwaysUpdateLinks": true,
  "attachmentFolderPath": "RAW_inputs/documents"
}
```

Создать `.obsidian/appearance.json`:

```json
{
  "baseFontSize": 16,
  "theme": "obsidian"
}
```

Создать `.obsidian/core-plugins.json`:

```json
[
  "file-explorer",
  "global-search",
  "graph",
  "backlink",
  "outgoing-link",
  "tag-pane",
  "page-preview",
  "templates"
]
```

Создать `.obsidian/graph.json`:

```json
{
  "collapse-filter": false,
  "search": "",
  "showTags": true,
  "showAttachments": false,
  "hideUnresolved": false,
  "showOrphans": true,
  "collapse-color-groups": false,
  "colorGroups": [],
  "collapse-display": true,
  "showArrow": false,
  "textFadeMultiplier": 0,
  "nodeSizeMultiplier": 1,
  "lineSizeMultiplier": 1,
  "collapse-forces": true,
  "centerStrength": 0.518713248970312,
  "repelStrength": 10,
  "linkStrength": 1,
  "linkDistance": 250,
  "scale": 1,
  "close": false
}
```

Создать `.obsidian/templates.json`:

```json
{
  "folder": "Vision_wiki/_templates"
}
```

Не переносить `.obsidian/workspace.json`, `.obsidian/workspace-mobile.json`, `.obsidian/cache` и `.obsidian/plugins/*/data.json`.

- [ ] **Шаг 1: Создать корневой wiki index**

Создать `index.md`:

```markdown
---
title: Индекс Знаний GeoService
type: index
status: active
created: 2026-05-30
updated: 2026-05-30
source: null
tags: [knowledge, index, geoservice]
---

# Индекс Знаний GeoService

Это точка входа в project knowledge wiki GeoService.

## Проект

- Название: GeoService
- Репозиторий: `C:\Repositories\geoservice`
- Стадия: experimental MVP
- Кратко: GeoService хранит геообъекты в PostGIS, отдает их через FastAPI и отображает/редактирует карты через Vue и MapLibre.

## Области Знаний

- [[RAW_inputs/index]] - сырые источники и исходные материалы проекта.
- [[Vision_wiki/index]] - продуктовые знания, решения, конфликты, follow-up'ы и заметки встреч.
- [[Code_wiki/index]] - техническая wiki для архитектуры, разработки, deployment и состояния проекта.
- [[memory/project-state]] - живое состояние проекта.
- [[memory/llm-wiki-method]] - методика ведения атомарных LLM-wiki нод.
- [[docs/agent-memory/README]] - компактная инженерная память Codex.

## Ручной Pipeline

- Утро: запустить `/sync-vision`, прочитать `memory/project-state.md`, проверить новые файлы в `RAW_inputs/`, затем запустить `/ingest` для новых RAW inputs.
- Перед встречей: запустить `/discover --context "планирование спринта" --phase "F2"` и подготовить чек-лист из 10-15 вопросов.
- После встречи: положить транскрипт в `RAW_inputs/meetings/`, запустить `/ingest`, обновить wiki-ноды, конфликты, follow-up'ы и project state.
- Раз в неделю: запустить `/lint-wiki`, затем `/sync-vision`, затем проверить отчет о здоровье wiki.

## Автоматический Pipeline

`repository-change ingest` запускается через `scripts\prepare_commit.cmd` перед pre-commit для значимых staged changes. Он пишет только knowledge-документацию и никогда не меняет код, конфигурацию, миграции или тесты. Pre-commit hook только проверяет, что ingest не пропущен.
```

- [ ] **Шаг 2: Создать RAW index и `_info.md` для подпапок**

Создать `RAW_inputs/index.md`:

```markdown
---
title: RAW_inputs
type: index
status: active
created: 2026-05-30
updated: 2026-05-30
source: null
tags: [raw-inputs, source-of-truth]
---

# RAW_inputs

Здесь хранятся сырые материалы проекта. Новые материалы добавляются, но исходные файлы не переписываются на месте.

## Папки

- [[meetings/_info]] - транскрипты и исходные заметки встреч.
- [[documents/_info]] - требования, спецификации, презентации и PDF.
- [[code/_info]] - фрагменты кода, ссылки на коммиты и технические выдержки для разбора.
- [[docs/_info]] - внешняя или импортированная документация.
- [[chats/_info]] - экспорты переписок, писем и мессенджеров.
- [[research_results/_info]] - результаты research.

## Журнал Поступлений

| Дата | Файл | Источник | Обработан |
|---|---|---|---|
```

Создать `_info.md` для каждой подпапки. Пример для `RAW_inputs/meetings/_info.md`:

```markdown
---
title: RAW inputs - meetings
type: info
status: active
created: 2026-05-30
updated: 2026-05-30
source: null
tags: [raw-inputs]
---

# meetings

Здесь хранятся транскрипты встреч и исходные заметки встреч. После добавления файла запустить `/ingest RAW_inputs/meetings/<file>`.
```

Для `documents`, `code`, `docs`, `chats`, `research_results` использовать тот же формат, меняя H1 и описание назначения папки.

- [ ] **Шаг 3: Создать базовый `Vision_wiki`**

Создать `Vision_wiki/index.md`:

```markdown
---
title: Vision_wiki
type: index
status: active
created: 2026-05-30
updated: 2026-05-30
source: null
tags: [vision-wiki, product]
---

# Vision_wiki

Продуктовые знания и решения GeoService.

## Структура

- [[_templates/_info]] - шаблоны продуктовых и decision-нод.
- [[chats/_info]] - чек-листы встреч и структурированные сводки разговоров.
- [[concepts/_info]] - продуктовые и доменные концепты.
- [[decisions/_info]] - решения, assumptions, конфликты и follow-up'ы.
- [[entities/_info]] - стейкхолдеры, персоны, конкуренты и связанные сущности.
- [[solution/_info]] - solution view, user story map, roadmap и NFR notes.

## Стартовые Ноды

- [[../index]] - корневой индекс знаний проекта.
- [[../memory/project-state]] - живое состояние проекта.
- [[../Code_wiki/index]] - техническая wiki.
```

Создать `Vision_wiki/decisions/followups/index.md`:

```markdown
---
title: Follow-ups
type: index
status: active
created: 2026-05-30
updated: 2026-05-30
source: null
tags: [followups, conflicts]
---

# Follow-ups

Контролируемая очередь открытых вопросов, документационных конфликтов и кандидатов на post-ingest correction.

## Открытые Follow-up'ы

| ID | Статус | Область | Источник | Требуемое действие |
|---|---|---|---|---|

## Правило Post-Ingest Correction

После `/ingest` можно исправлять старую документацию только по конфликтам, которые уже перечислены здесь и связаны с `Code_wiki`. Нельзя менять код, конфигурацию, миграции или тесты как часть post-ingest correction.
```

- [ ] **Шаг 4: Создать базовый `Code_wiki`**

Создать `Code_wiki/index.md`:

```markdown
---
title: Code_wiki
type: index
status: active
created: 2026-05-30
updated: 2026-05-30
source: null
tags: [code-wiki, technical-knowledge]
---

# Code_wiki

Технические знания для людей и агентов, работающих с кодом GeoService.

## Структура

- [[_templates/_info]] - шаблоны ADR, сервисов, runbook'ов, API endpoints и postmortems.
- [[архитектура/_info]] - архитектурные заметки и ADR.
- [[dev_setup/_info]] - локальная разработка.
- [[сборка/_info]] - сборка и CI.
- [[deployment/_info]] - deployment notes, runbook'и и postmortems.
- [[правила_и_стиль/_info]] - инженерные соглашения и правила review.
- [[глоссарий/_info]] - технический глоссарий.
- [[состояние_проекта/_info]] - текущее техническое состояние проекта и automatic repository-change log.
```

Создать `memory/project-state.md`:

```markdown
---
title: Состояние Проекта GeoService
type: state
status: active
created: 2026-05-30
updated: 2026-05-30
source: null
tags: [project-state, geoservice]
---

# Состояние Проекта GeoService

Живое состояние knowledge wiki GeoService.

## Кратко

GeoService - experimental MVP для хранения геоданных, API-доступа, отображения карты и базового редактирования.

## Состояние Pipeline

- Последний `/discover`: еще не запускался в этой wiki.
- Последний `/ingest`: еще не запускался в этой wiki.
- Последний `/sync-vision`: еще не запускался в этой wiki.
- Последний `/lint-wiki`: еще не запускался в этой wiki.
- Последний automatic repository-change ingest: еще не запускался в этой wiki.

## Открытые Вопросы

См. [[../Vision_wiki/decisions/followups/index]].
```

- [ ] **Шаг 5: Проверить, что skeleton paths существуют**

Запустить:

```powershell
Test-Path .\RAW_inputs\index.md
Test-Path .\Vision_wiki\decisions\followups\index.md
Test-Path .\Code_wiki\index.md
Test-Path .\memory\project-state.md
```

Ожидается: четыре строки `True`.

## Задача 2: Добавить Шаблоны, Методологию И Runbook

**Файлы:**
- Создать: `Vision_wiki/_templates/_info.md`
- Создать: `Vision_wiki/_templates/session.md`
- Создать: `Vision_wiki/_templates/adr.md`
- Создать: `Vision_wiki/_templates/conflict.md`
- Создать: `Vision_wiki/_templates/risk.md`
- Создать: `Code_wiki/_templates/_info.md`
- Создать: `Code_wiki/_templates/adr.md`
- Создать: `Code_wiki/_templates/runbook.md`
- Создать: `Code_wiki/_templates/service.md`
- Создать: `Code_wiki/_templates/api-endpoint.md`
- Создать: `Code_wiki/_templates/postmortem.md`
- Создать: `memory/llm-wiki-method.md`
- Создать: `docs/knowledge-pipeline/README.md`
- Создать: `.agents/skills/source-command-ingest/SKILL.md`
- Создать: `.agents/skills/source-command-discover/SKILL.md`
- Создать: `.agents/skills/source-command-sync-vision/SKILL.md`
- Создать: `.agents/skills/source-command-lint-wiki/SKILL.md`

- [ ] **Шаг 1: Создать переиспользуемые шаблоны**

Для каждого template-файла использовать frontmatter с нейтральными значениями и без фактов donor-проекта. Пример `Code_wiki/_templates/adr.md`:

```markdown
---
title: Название ADR
type: template
status: active
created: 2026-05-30
updated: 2026-05-30
source: null
tags: [template, adr]
---

# Название ADR

## Статус

Proposed

## Контекст

Описать технический контекст и ограничения.

## Решение

Описать принятое решение.

## Последствия

- Плюсы:
- Минусы:
- Follow-up:
```

Аналогично создать остальные шаблоны. Человекочитаемый текст писать на русском; `type`, `status`, `tags`, пути и технические идентификаторы не переводить.

- [ ] **Шаг 2: Добавить методологию LLM-wiki**

Создать `memory/llm-wiki-method.md`:

```markdown
---
title: Методология LLM-wiki
type: method
status: active
created: 2026-05-30
updated: 2026-05-30
source: null
tags: [llm-wiki, method, knowledge]
---

# Методология LLM-wiki

## Принципы

- Одна нода описывает один концепт, решение, сессию, сервис, runbook или риск.
- Каждый смысловой wiki-файл содержит YAML frontmatter.
- Для внутренних связей используются wikilinks.
- `RAW_inputs/` - исходные материалы; они не переписываются на месте.
- Если факт является выводом, пометить его как inferred или добавить follow-up.
- Не сохранять секреты, полные чаты, шумные логи или неподтвержденные догадки как факты.
- Wiki ведется на русском языке; пути, команды, API и идентификаторы остаются в исходном виде.

## Post-Ingest Correction

После `/ingest` документационные конфликты можно исправлять только если конфликт уже есть в `Vision_wiki/decisions/followups/index.md` и связан с `Code_wiki`. Исправлять можно старую документацию на основе новых knowledge-изменений. Нельзя менять код, конфигурацию, миграции или тесты.
```

- [ ] **Шаг 3: Добавить runbook ручного pipeline**

Создать `docs/knowledge-pipeline/README.md`:

```markdown
# Knowledge Pipeline Runbook

## Язык Wiki

Wiki ведется на русском языке. Пути, команды, API, имена файлов, типы, идентификаторы и код не переводятся.

## Утро

1. Запустить `/sync-vision`.
2. Прочитать `memory/project-state.md`.
3. Проверить `RAW_inputs/` на новые файлы.
4. Запустить `/ingest <path>` для каждого нового RAW-файла.

## Перед Встречей

1. Запустить `/discover --context "планирование спринта" --phase "F2"`.
2. Подготовить 10-15 вопросов.
3. Сохранить чек-лист в `Vision_wiki/chats/YYYY-MM-DD-<topic>-checklist.md`.

## После Встречи

1. Положить транскрипт в `RAW_inputs/meetings/`.
2. Запустить `/ingest RAW_inputs/meetings/<file>`.
3. Обновить `Vision_wiki`.
4. Зафиксировать конфликты и follow-up'ы.
5. Выполнить post-ingest correction только для конфликтов `Code_wiki`, уже перечисленных в `Vision_wiki/decisions/followups/index.md`.
6. Обновить `memory/project-state.md`.

## Раз В Неделю

1. Запустить `/lint-wiki`.
2. Запустить `/sync-vision`.
3. Проверить broken links, orphan nodes, missing frontmatter, stale files, conflicts и follow-up'ы.

## Automatic Repository-Change Ingest

Перед commit запустить `scripts\prepare_commit.cmd`. Он выполняет `python scripts\repository_change_ingest.py --repo-root . --apply`, stage'ит сгенерированный Markdown и запускает `pre-commit run`. Pre-commit guard только проверяет, что ingest не пропущен.
```

- [ ] **Шаг 4: Добавить repo-local command skills**

Создать `.agents/skills/source-command-ingest/SKILL.md`:

```markdown
---
name: source-command-ingest
description: Ручная ingest-процедура для RAW inputs и repository knowledge changes.
---

# /ingest

Прочитать указанный источник, извлечь долговечные факты, обновить `Vision_wiki` или `Code_wiki`, обновить `Vision_wiki/decisions/followups/index.md` и `memory/project-state.md`.

Wiki ведется на русском языке. Пути, команды, API, идентификаторы и код не переводятся.

Не редактировать `C:\Repositories\ai-po-template-experiments`.
Не менять код, конфигурацию, миграции или тесты как часть documentation conflict correction.
Post-ingest correction разрешен только для конфликтов, уже перечисленных в `Vision_wiki/decisions/followups/index.md` и связанных с `Code_wiki`.
```

Создать остальные три skill-файла с такими же явными ручными процедурами для `/discover`, `/sync-vision`, `/lint-wiki`.

- [ ] **Шаг 5: Проверить discoverability command docs**

Запустить:

```powershell
rg -n "/ingest|/discover|/sync-vision|/lint-wiki|Post-Ingest Correction|русском языке" docs/knowledge-pipeline .agents memory Vision_wiki Code_wiki
```

Ожидается: совпадения в runbook, skill docs и методологии.

## Задача 3: Добавить Wiki Linter И Тесты

**Файлы:**
- Создать: `scripts/lint-wiki.py`
- Создать: `scripts/tests/test_lint_wiki.py`

- [ ] **Шаг 1: Написать failing tests для linter**

Создать `scripts/tests/test_lint_wiki.py`:

```python
import importlib.util
from pathlib import Path


def load_linter():
    module_path = Path(__file__).resolve().parents[1] / "lint-wiki.py"
    spec = importlib.util.spec_from_file_location("lint_wiki", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_reports_broken_wikilink(tmp_path):
    linter = load_linter()
    (tmp_path / "Vision_wiki").mkdir()
    (tmp_path / "Vision_wiki" / "index.md").write_text(
        "---\ntitle: Индекс\ntype: index\nstatus: active\ncreated: 2026-05-30\nupdated: 2026-05-30\nsource: null\ntags: []\n---\n\n[[missing-node]]\n",
        encoding="utf-8",
    )

    issues = linter.lint(tmp_path, strict=False)

    assert issues["broken_wikilinks"] == [{"file": "Vision_wiki/index.md", "link": "missing-node"}]


def test_strict_reports_concept_without_source(tmp_path):
    linter = load_linter()
    concepts = tmp_path / "Vision_wiki" / "concepts"
    concepts.mkdir(parents=True)
    (concepts / "thing.md").write_text(
        "---\ntitle: Концепт\ntype: concept\nstatus: active\ncreated: 2026-05-30\nupdated: 2026-05-30\ntags: []\n---\n\n# Концепт\n",
        encoding="utf-8",
    )

    issues = linter.lint(tmp_path, strict=True)

    assert issues["missing_source"] == ["Vision_wiki/concepts/thing.md"]
```

- [ ] **Шаг 2: Запустить тесты и убедиться, что они падают**

Запустить:

```powershell
python -m unittest discover -s scripts/tests -p "test_lint_wiki.py"
```

Ожидается: failure, потому что `scripts/lint-wiki.py` еще не существует.

- [ ] **Шаг 3: Реализовать linter**

Создать `scripts/lint-wiki.py`, адаптировав donor-скрипт, но использовать GeoService roots:

```python
WIKI_ROOTS = ["Vision_wiki", "Code_wiki", "Общие_принципы", "memory", "RAW_inputs", "docs/agent-memory"]
IGNORE_DIRS = {".git", ".ruff_cache", ".worktrees", ".agents", ".github", "node_modules", "__pycache__"}
```

Публичные функции должны быть доступны:

```python
from pathlib import Path


def lint(repo_root: Path, strict: bool = False) -> dict:
    return {
        "broken_wikilinks": [],
        "orphan_files": [],
        "missing_frontmatter": [],
        "invalid_frontmatter": [],
        "stale_files": [],
        "empty_dirs": [],
        "missing_source": [],
    }


def main() -> int:
    return 0
```

Итоговая реализация должна:

- парсить простой YAML frontmatter без external dependencies;
- находить broken wikilinks;
- находить missing frontmatter в смысловых Markdown-файлах;
- находить invalid frontmatter syntax;
- находить orphan files;
- находить empty dirs;
- находить stale files в strict mode;
- находить active concept files без `source` в strict mode.

- [ ] **Шаг 4: Запустить тесты linter**

Запустить:

```powershell
python -m unittest discover -s scripts/tests -p "test_lint_wiki.py"
```

Ожидается: `OK`.

- [ ] **Шаг 5: Запустить linter на репозитории**

Запустить:

```powershell
python scripts/lint-wiki.py --root .
```

Ожидается: нет Python exception. Если linter сообщает structural issues в новом skeleton, исправить только файлы GeoService wiki и запустить повторно.

## Задача 4: Добавить Automatic Repository-Change Ingest Перед Pre-Commit

**Файлы:**
- Создать: `scripts/repository_change_ingest.py`
- Создать: `scripts/prepare_commit.cmd`
- Создать: `scripts/tests/test_repository_change_ingest.py`
- Изменить: `.pre-commit-config.yaml`
- Создать: `Code_wiki/состояние_проекта/repository_change_ingest.md`

- [ ] **Шаг 1: Написать failing tests для repository-change ingest**

Создать `scripts/tests/test_repository_change_ingest.py`:

```python
import importlib.util
from pathlib import Path


def load_module():
    module_path = Path(__file__).resolve().parents[1] / "repository_change_ingest.py"
    spec = importlib.util.spec_from_file_location("repository_change_ingest", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_classifies_backend_feature_change():
    ingest = load_module()

    result = ingest.classify_paths(["apps/backend/app/services/feature_service.py"])

    assert result == {
        "area": "backend",
        "change_type": "feature implementation",
        "knowledge_target": "Code_wiki/состояние_проекта/repository_change_ingest.md",
    }


def test_ignores_existing_knowledge_files():
    ingest = load_module()

    result = ingest.meaningful_paths(["Code_wiki/index.md", "memory/project-state.md"])

    assert result == []


def test_renders_entry_with_fingerprint():
    ingest = load_module()

    entry = ingest.render_entry(
        fingerprint="abc123",
        files=["apps/frontend/src/App.vue"],
        classification={
            "area": "frontend",
            "change_type": "feature implementation",
            "knowledge_target": "Code_wiki/состояние_проекта/repository_change_ingest.md",
        },
        today="2026-05-30",
    )

    assert "Change fingerprint: `abc123`" in entry
    assert "`apps/frontend/src/App.vue`" in entry
    assert "frontend" in entry


def test_append_once_is_idempotent(tmp_path):
    ingest = load_module()
    target = tmp_path / "log.md"
    target.write_text("# Log\n", encoding="utf-8")
    entry = "\n\nChange fingerprint: `abc123`\n"

    first = ingest.append_once(target, entry, "abc123")
    second = ingest.append_once(target, entry, "abc123")

    assert first is True
    assert second is False
    assert target.read_text(encoding="utf-8").count("Change fingerprint: `abc123`") == 1


def test_guard_fails_when_meaningful_change_has_no_entry(tmp_path):
    ingest = load_module()
    target = tmp_path / "repository_change_ingest.md"
    target.write_text("# Log\n", encoding="utf-8")
    fp = ingest.fingerprint(["apps/backend/app/services/feature_service.py"])

    result = ingest.guard_has_entry(target, fp)

    assert result is False


def test_guard_passes_when_entry_exists(tmp_path):
    ingest = load_module()
    target = tmp_path / "repository_change_ingest.md"
    fp = ingest.fingerprint(["apps/backend/app/services/feature_service.py"])
    target.write_text(f"# Log\n\nChange fingerprint: `{fp}`\n", encoding="utf-8")

    result = ingest.guard_has_entry(target, fp)

    assert result is True
```

- [ ] **Шаг 2: Запустить тесты и убедиться, что они падают**

Запустить:

```powershell
python -m unittest discover -s scripts/tests -p "test_repository_change_ingest.py"
```

Ожидается: failure, потому что `scripts/repository_change_ingest.py` еще не существует.

- [ ] **Шаг 3: Реализовать repository-change ingest script**

Создать `scripts/repository_change_ingest.py`:

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import subprocess
from datetime import date
from pathlib import Path

KNOWLEDGE_PREFIXES = (
    "RAW_inputs/",
    "Vision_wiki/",
    "Code_wiki/",
    "memory/",
    "docs/agent-memory/",
    "docs/superpowers/",
)

MEANINGFUL_PREFIXES = (
    "apps/backend/",
    "apps/frontend/",
    "infra/",
    "scripts/",
    ".github/",
    "docs/requirements/",
    "AGENTS.md",
    "README.md",
)

TARGET = Path("Code_wiki/состояние_проекта/repository_change_ingest.md")


def run_git(args: list[str], repo_root: Path) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def staged_paths(repo_root: Path) -> list[str]:
    output = run_git(["diff", "--cached", "--name-only", "--diff-filter=ACMR"], repo_root)
    return [line.strip().replace("\\", "/") for line in output.splitlines() if line.strip()]


def meaningful_paths(paths: list[str]) -> list[str]:
    result = []
    for path in paths:
        normalized = path.replace("\\", "/")
        if normalized.startswith(KNOWLEDGE_PREFIXES):
            continue
        if normalized in MEANINGFUL_PREFIXES or normalized.startswith(MEANINGFUL_PREFIXES):
            result.append(normalized)
    return result


def classify_paths(paths: list[str]) -> dict[str, str]:
    joined = "\n".join(paths)
    if "apps/backend/" in joined:
        area = "backend"
    elif "apps/frontend/" in joined:
        area = "frontend"
    elif "infra/" in joined or ".github/" in joined:
        area = "infra"
    elif "docs/requirements/" in joined:
        area = "requirements"
    elif "scripts/" in joined:
        area = "tooling"
    else:
        area = "repository"

    if area in {"backend", "frontend"}:
        change_type = "feature implementation"
    elif area == "infra":
        change_type = "runbook/dev setup"
    elif area == "requirements":
        change_type = "product requirement update"
    else:
        change_type = "workflow or style rule"

    return {
        "area": area,
        "change_type": change_type,
        "knowledge_target": TARGET.as_posix(),
    }


def fingerprint(paths: list[str]) -> str:
    joined = "\n".join(sorted(paths))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:12]


def ensure_log(repo_root: Path) -> Path:
    target = repo_root / TARGET
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        target.write_text(
            "---\n"
            "title: Repository Change Ingest Log\n"
            "type: state\n"
            "status: active\n"
            "created: 2026-05-30\n"
            "updated: 2026-05-30\n"
            "source: git staged changes\n"
            "tags: [repository-change-ingest, automatic]\n"
            "---\n\n"
            "# Repository Change Ingest Log\n\n"
            "Automatic repository-change ingest appends durable staged-change summaries here.\n",
            encoding="utf-8",
        )
    return target


def render_entry(fingerprint: str, files: list[str], classification: dict[str, str], today: str) -> str:
    file_lines = "\n".join(f"- `{path}`" for path in files)
    return (
        f"\n\n## {today} - {classification['area']} {classification['change_type']}\n\n"
        f"Change fingerprint: `{fingerprint}`\n\n"
        f"Area: `{classification['area']}`\n\n"
        f"Type: `{classification['change_type']}`\n\n"
        "Status: pending human review during commit.\n\n"
        "Changed files:\n\n"
        f"{file_lines}\n\n"
        "Knowledge note: verify whether this change needs a dedicated Code_wiki node after commit.\n"
    )


def append_once(path: Path, entry: str, fingerprint_value: str) -> bool:
    text = path.read_text(encoding="utf-8")
    marker = f"Change fingerprint: `{fingerprint_value}`"
    if marker in text:
        return False
    path.write_text(text.rstrip() + entry + "\n", encoding="utf-8")
    return True


def guard_has_entry(path: Path, fingerprint_value: str) -> bool:
    if not path.exists():
        return False
    return f"Change fingerprint: `{fingerprint_value}`" in path.read_text(encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    paths = meaningful_paths(staged_paths(repo_root))
    if not paths:
        return 0

    fp = fingerprint(paths)

    if args.check:
        target = repo_root / TARGET
        if guard_has_entry(target, fp):
            return 0
        print(
            "repository-change ingest missing for staged changes. "
            "Run `scripts\\prepare_commit.cmd` or `python scripts/repository_change_ingest.py --repo-root . --apply`, "
            "review generated knowledge files, then commit again."
        )
        return 1

    if not args.apply:
        print("Nothing written. Use --apply to update knowledge documentation or --check for pre-commit guard.")
        return 0

    classification = classify_paths(paths)
    target = ensure_log(repo_root)
    entry = render_entry(fp, paths, classification, date.today().isoformat())
    changed = append_once(target, entry, fp)
    if changed:
        run_git(["add", TARGET.as_posix()], repo_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Шаг 4: Запустить тесты repository-change ingest**

Запустить:

```powershell
python -m unittest discover -s scripts/tests -p "test_repository_change_ingest.py"
```

Ожидается: `OK`.

- [ ] **Шаг 5: Добавить prepare commit helper**

Создать `scripts/prepare_commit.cmd`:

```bat
@echo off
setlocal

python scripts\repository_change_ingest.py --repo-root . --apply
if errorlevel 1 exit /b %errorlevel%

pre-commit run
exit /b %errorlevel%
```

Пользовательский flow:

```powershell
scripts\prepare_commit.cmd
git commit -m "docs: update project knowledge"
```

`prepare_commit.cmd` запускает automatic `repository-change ingest` до pre-commit, чтобы hook не был скрытым редактором staged files.

- [ ] **Шаг 6: Добавить local pre-commit guard hook**

Добавить в `.pre-commit-config.yaml`:

```yaml
  - repo: local
    hooks:
      - id: repository-change-ingest-guard
        name: repository-change ingest guard
        entry: python scripts/repository_change_ingest.py --check
        language: system
        pass_filenames: false
        stages: [pre-commit]
```

- [ ] **Шаг 7: Проверить prepare helper и hook guard**

Запустить:

```powershell
scripts\prepare_commit.cmd
pre-commit run repository-change-ingest-guard --all-files
```

Ожидается: `prepare_commit.cmd` применяет `repository-change ingest` до pre-commit. Guard hook не пишет файлы; если staged meaningful changes есть, но entry отсутствует, он печатает команду `scripts\prepare_commit.cmd` и возвращает exit code `1`.

Если `pre-commit` не установлен в shell, зафиксировать, что проверку hook запустить нельзя, и выполнить fallback:

```powershell
python scripts/repository_change_ingest.py --repo-root . --apply
python scripts/repository_change_ingest.py --repo-root . --check
```

Ожидается: команда завершается успешно.

- [ ] **Шаг 8: Проверить идемпотентность prepare behavior**

Сценарий ручной проверки:

```powershell
git add apps/backend/app/services/feature_service.py
python scripts/repository_change_ingest.py --repo-root . --apply
python scripts/repository_change_ingest.py --repo-root . --apply
python scripts/repository_change_ingest.py --repo-root . --check
```

Ожидается:

- первый `--apply` при новом fingerprint создает или обновляет `Code_wiki/состояние_проекта/repository_change_ingest.md`, stage'ит файл и возвращает exit code `0`;
- второй `--apply` с тем же staged fingerprint ничего не добавляет повторно и возвращает exit code `0`;
- `--check` после `--apply` возвращает exit code `0`;
- changes в `Code_wiki/`, `Vision_wiki/`, `memory/`, `docs/agent-memory/`, `docs/superpowers/` не создают новые repository-change entries.

## Задача 5: Обновить Инструкции Репозитория И Существующую Agent Memory

**Файлы:**
- Изменить: `AGENTS.md`
- Изменить: `README.md`
- Изменить: `.gitignore`
- Изменить: `CONTRIBUTING.md`
- Изменить: `docs/agent-memory/file-map.md`
- Изменить: `docs/agent-memory/decisions/2026-05-30-agent-memory-operating-rules.md`

- [ ] **Шаг 1: Обновить `AGENTS.md`**

Заменить текущий короткий workflow расширенной версией:

```markdown
# Agent Instructions

Before working in this repository:

1. Read `docs/agent-memory/protocol.md`.
2. Search `docs/agent-memory/file-map.md` and memory entries for context related to the user's request.
3. Read `memory/project-state.md` if the task touches project knowledge, documentation, product decisions, technical wiki, or repository workflow.
4. Read only memory and wiki entries that are relevant to the request.
5. Do not edit `C:\Repositories\ai-po-template-experiments`; it is read-only donor context.
6. After significant work, add or update `docs/agent-memory/` and, when the change is durable project knowledge, update `Code_wiki/`, `Vision_wiki/`, or `memory/project-state.md`.

Knowledge wiki language:

- Human-facing wiki content is written in Russian.
- Paths, commands, file names, APIs, types, identifiers, package names, and code are not translated.

Manual knowledge pipeline:

- Morning: `/sync-vision`, check `memory/project-state.md`, check `RAW_inputs/`, run `/ingest` for new RAW files.
- Before meeting: `/discover --context "планирование спринта" --phase "F2"`, prepare 10-15 questions and a checklist.
- After meeting: put transcript in `RAW_inputs/meetings/`, run `/ingest`, update wiki, conflicts, follow-ups, and project state.
- Weekly: `/lint-wiki`, `/sync-vision`, review wiki health.

Automatic knowledge pipeline:

- `repository-change ingest` runs before pre-commit through `scripts\prepare_commit.cmd`; pre-commit only guards that ingest was not skipped.
- It may write only knowledge documentation.
- It must not change code, configuration, migrations, or tests.

Pre-final memory gate:

- Before a final response, check whether the work created a durable decision, rule, workflow change, bug root cause, plan/spec update, or project constraint.
- If yes, add or update a memory entry in `docs/agent-memory/` and update `docs/agent-memory/file-map.md` before finalizing.
- If no memory entry is needed, be ready to explain why the work has no durable value beyond the current chat.
```

- [ ] **Шаг 2: Обновить `README.md`**

Добавить раздел:

```markdown
## Knowledge Wiki

GeoService ведет PO-style project knowledge wiki на русском языке:

- [Knowledge index](C:/Repositories/geoservice/index.md)
- [RAW inputs](C:/Repositories/geoservice/RAW_inputs/index.md)
- [Vision wiki](C:/Repositories/geoservice/Vision_wiki/index.md)
- [Code wiki](C:/Repositories/geoservice/Code_wiki/index.md)
- [Project state](C:/Repositories/geoservice/memory/project-state.md)
- [Knowledge pipeline runbook](C:/Repositories/geoservice/docs/knowledge-pipeline/README.md)

Workflow `/discover`, `/ingest`, `/sync-vision`, `/lint-wiki` выполняются вручную. `repository-change ingest` запускается через `scripts\prepare_commit.cmd` перед pre-commit; pre-commit содержит guard, который проверяет, что ingest не пропущен.
```

- [ ] **Шаг 3: Обновить `.gitignore` для wiki/agent temporary files**

Добавить в `.gitignore`, если этих правил еще нет:

```gitignore
# Obsidian local workspace files
.obsidian/workspace.json
.obsidian/workspace-mobile.json
.obsidian/cache
.obsidian/plugins/*/data.json

# Python local tooling
__pycache__/
.venv/
venv/

# Local agent memory and temporary files
.claude/local/
memory/local/
*.tmp
*.bak
```

Не добавлять ignore для `RAW_inputs/` целиком: сырые материалы по умолчанию должны быть версионируемыми, кроме случаев, когда пользователь отдельно решит хранить чувствительные материалы вне Git.

- [ ] **Шаг 4: Обновить `CONTRIBUTING.md` wiki style rules**

Добавить раздел:

```markdown
## Knowledge Wiki Style

- Human-facing wiki content is written in Russian.
- File names in `_templates/`, script names, code, commands, API names, types, and identifiers stay in their original language.
- Use Markdown and wikilinks `[[Название]]` for internal wiki links.
- Every meaningful wiki file should have frontmatter.
- Do not use emoji in file names because they can break paths in some Windows environments.
- Do not commit secrets, `.env` values, full chat logs, noisy logs, or unverified guesses as facts.
```

- [ ] **Шаг 5: Обновить `file-map.md`**

Добавить в `docs/agent-memory/file-map.md` секцию:

```markdown
## Knowledge Wiki

- project knowledge wiki pipeline: `index.md`, `docs/knowledge-pipeline/README.md`, `memory/project-state.md`
- raw input ingest sources: `RAW_inputs/index.md`, `RAW_inputs/meetings/_info.md`, `RAW_inputs/documents/_info.md`, `RAW_inputs/docs/_info.md`
- product knowledge wiki: `Vision_wiki/index.md`, `Vision_wiki/decisions/followups/index.md`
- technical knowledge wiki: `Code_wiki/index.md`, `Code_wiki/состояние_проекта/repository_change_ingest.md`
- wiki lint and automatic repository-change ingest: `scripts/lint-wiki.py`, `scripts/repository_change_ingest.py`, `scripts/prepare_commit.cmd`, `.pre-commit-config.yaml`
- knowledge wiki style and ignore rules: `CONTRIBUTING.md`, `.gitignore`
```

- [ ] **Шаг 6: Обновить durable decision**

Обновить
`docs/agent-memory/decisions/2026-05-30-agent-memory-operating-rules.md`
только устойчивыми правилами pipeline. Не создавать session task-log:
фактическое устройство wiki хранится в `docs/knowledge-pipeline/README.md`,
`AGENTS.md`, repo-local skills и индексах wiki.

## Задача 6: Улучшить Надежность Записи Локальной Памяти

**Файлы:**
- Изменить: `docs/agent-memory/protocol.md`
- Изменить: `AGENTS.md`
- Изменить: `docs/superpowers/plans/2026-05-30-project-knowledge-wiki-pipeline.md`
- Создать: `scripts/check-memory-needed.py`
- Создать: `scripts/tests/test_check_memory_needed.py`
- Изменить: `docs/agent-memory/file-map.md`

**Причина:** Во время планирования было найдено процессное упущение: durable-решение “планы должны быть на русском языке” сначала было внесено в план, но не было сразу записано в `docs/agent-memory/`. Технического блокера не было; агент не прошел явный memory gate. Эта задача добавляет предохранители, чтобы будущие агенты реже забывали записывать важные решения.

- [ ] **Шаг 1: Обновить `docs/agent-memory/protocol.md` явными triggers**

Добавить после секции `## What To Store`:

```markdown
## Always Store Triggers

Always add or update a memory entry when any of these happen:

- the user states a durable rule, preference, or working agreement;
- an agent workflow changes;
- a document format, plan format, language rule, naming rule, or repository convention is approved;
- a boundary or prohibition is established, such as read-only paths or files that must not be edited;
- a root cause is found for a process failure, bug, or repeated miss;
- a design spec or implementation plan is created or materially changed;
- a new automatic check, hook, script, or recurring workflow is introduced;
- a durable conflict resolution rule is created.

If none of these triggers apply, memory is optional and should still follow the "useful in a week" rule.
```

- [ ] **Шаг 2: Обновить `AGENTS.md` pre-final memory gate**

В `AGENTS.md` добавить или сохранить блок:

```markdown
Before final response:

1. Check whether this turn created a durable decision, rule, workflow change, bug root cause, plan/spec update, project constraint, or repository convention.
2. If yes, add or update `docs/agent-memory/` and update `docs/agent-memory/file-map.md`.
3. If no, finish normally.
```

- [ ] **Шаг 3: Добавить failing tests для `check-memory-needed`**

Создать `scripts/tests/test_check_memory_needed.py`:

```python
import importlib.util
from pathlib import Path


def load_module():
    module_path = Path(__file__).resolve().parents[1] / "check-memory-needed.py"
    spec = importlib.util.spec_from_file_location("check_memory_needed", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_requires_memory_when_plan_changes_without_agent_memory():
    checker = load_module()

    result = checker.needs_memory_warning([
        "docs/superpowers/plans/2026-05-30-example.md",
    ])

    assert result is True


def test_no_warning_when_agent_memory_changes_too():
    checker = load_module()

    result = checker.needs_memory_warning([
        "docs/superpowers/plans/2026-05-30-example.md",
        "docs/agent-memory/patterns/2026-05-30-example.md",
    ])

    assert result is False


def test_requires_memory_when_agents_changes_without_memory():
    checker = load_module()

    result = checker.needs_memory_warning(["AGENTS.md"])

    assert result is True
```

- [ ] **Шаг 4: Запустить failing tests**

Запустить:

```powershell
python -m unittest discover -s scripts/tests -p "test_check_memory_needed.py"
```

Ожидается: failure, потому что `scripts/check-memory-needed.py` еще не существует.

- [ ] **Шаг 5: Реализовать `scripts/check-memory-needed.py`**

Создать `scripts/check-memory-needed.py`:

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

MEMORY_PREFIX = "docs/agent-memory/"

DURABLE_CHANGE_PREFIXES = (
    "docs/superpowers/specs/",
    "docs/superpowers/plans/",
    "docs/knowledge-pipeline/",
    ".agents/skills/",
)

DURABLE_CHANGE_FILES = {
    "AGENTS.md",
    "README.md",
    "docs/agent-memory/protocol.md",
    ".pre-commit-config.yaml",
}


def normalize(path: str) -> str:
    return path.strip().replace("\\", "/")


def is_memory_path(path: str) -> bool:
    return normalize(path).startswith(MEMORY_PREFIX)


def is_durable_change_path(path: str) -> bool:
    normalized = normalize(path)
    return normalized in DURABLE_CHANGE_FILES or normalized.startswith(DURABLE_CHANGE_PREFIXES)


def needs_memory_warning(paths: list[str]) -> bool:
    normalized = [normalize(path) for path in paths if path.strip()]
    has_durable_change = any(is_durable_change_path(path) for path in normalized)
    has_memory_change = any(is_memory_path(path) for path in normalized)
    return has_durable_change and not has_memory_change


def staged_paths(repo_root: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in completed.stdout.splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()

    paths = staged_paths(Path(args.repo_root).resolve())
    if needs_memory_warning(paths):
        print(
            "Memory warning: durable workflow/spec/plan files changed, but no docs/agent-memory change is staged. "
            "Add a memory entry or intentionally document why no durable memory is needed."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Шаг 6: Запустить tests для `check-memory-needed`**

Запустить:

```powershell
python -m unittest discover -s scripts/tests -p "test_check_memory_needed.py"
```

Ожидается: `OK`.

- [ ] **Шаг 7: Добавить script в runbook и file-map**

В `docs/knowledge-pipeline/README.md` добавить в раздел weekly или pre-final:

```markdown
## Memory Needed Check

Run `python scripts/check-memory-needed.py --repo-root .` before finishing large documentation, plan, spec, workflow, or rule changes. If it prints a warning, add a memory entry or explicitly decide that no durable memory is needed.
```

В `docs/agent-memory/file-map.md` добавить:

```markdown
- memory write reliability check: `docs/agent-memory/protocol.md`, `scripts/check-memory-needed.py`, `scripts/tests/test_check_memory_needed.py`
```

- [ ] **Шаг 8: Обновить self-review текущего плана**

В `## Self-Review Checklist` этого плана оставить пункт:

```markdown
- [ ] Проверено, нужно ли записать новые durable rules в `docs/agent-memory/`.
```

## Задача 7: Проверка И Donor Read-Only Check

**Файлы:**
- Только проверка; новые файлы не ожидаются.

- [ ] **Шаг 1: Запустить все script tests**

Запустить:

```powershell
python -m unittest discover -s scripts/tests
```

Ожидается: все тесты проходят.

- [ ] **Шаг 2: Запустить wiki linter**

Запустить:

```powershell
python scripts/lint-wiki.py --root .
```

Ожидается: успешное завершение. Если есть skeleton issues, исправить только GeoService wiki files и повторить запуск.

- [ ] **Шаг 3: Проверить отсутствие donor-specific facts**

Запустить:

```powershell
rg -n "Polus|Geoportal|Георгий|Казань|Краснояр|Пашнин" index.md memory Vision_wiki Code_wiki RAW_inputs docs/knowledge-pipeline .agents
```

Ожидается: нет совпадений в runtime wiki files. Если совпадения есть в runtime wiki, удалить или обобщить их.

- [ ] **Шаг 4: Подтвердить, что donor repository не изменен**

Запустить:

```powershell
git -C C:\Repositories\ai-po-template-experiments status --short
```

Ожидается: нет новых изменений, вызванных этой реализацией. Если donor repo уже имел чужие изменения до работы, не редактировать и не откатывать их.

- [ ] **Шаг 5: Запустить smoke test repository-change ingest**

Запустить:

```powershell
python scripts/repository_change_ingest.py --repo-root . --apply
python scripts/repository_change_ingest.py --repo-root . --check
```

Ожидается: успешное завершение. Если meaningful files не staged, knowledge log entry не создается.

- [ ] **Шаг 6: Финальная проверка GeoService status**

Запустить:

```powershell
git status --short
```

Ожидается: изменены только ожидаемые файлы GeoService.

## Self-Review Checklist

- [ ] Каждое требование spec покрыто хотя бы одной задачей.
- [ ] Ни один шаг реализации не редактирует `C:\Repositories\ai-po-template-experiments`.
- [ ] Wiki-ноды, индексы, runbook'и, state-файлы и follow-up'ы ведутся на русском языке.
- [ ] Ручные workflow задокументированы для `/discover`, `/ingest`, `/sync-vision`, `/lint-wiki`.
- [ ] Automatic repository-change ingest реализован через `scripts\prepare_commit.cmd` перед pre-commit и repository-local pre-commit guard.
- [ ] `repository-change ingest` идемпотентен: повторный `--apply` не создает дублей, `--check` проходит после `--apply`.
- [ ] Post-ingest correction ограничен существующими конфликтами из `Vision_wiki/decisions/followups/index.md`, связанными с `Code_wiki`.
- [ ] Ни один шаг не разрешает менять code/config/migration/test files как часть documentation conflict correction.
- [ ] Verification включает tests, linter, donor-term search и donor repo status check.
