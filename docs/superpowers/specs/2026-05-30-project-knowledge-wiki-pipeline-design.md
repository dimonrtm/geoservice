# Дизайн Project Knowledge Wiki Pipeline

> **Актуализация 2026-05-30:** прежняя идея автоматизации через Python-скрипт, `prepare_commit.cmd` и pre-commit guard заменена. Актуальное правило: после полного завершения реализации плана или крупной задачи агент вызывает `/ingest repository-change` через repo-local skill `source-command-ingest` перед финальным отчётом пользователю. Pre-commit не запускает и не проверяет repository-change ingest.

Date: 2026-05-30
Status: Approved for spec review

## Цель

Перенести в GeoService шаблонный pipeline базы знаний из `C:\Repositories\ai-po-template-experiments` без привязки к Polus/Geoportal. Итоговая система должна сохранять структуру PO-репозитория, поддерживать ручной цикл `/discover`, `/ingest`, `/sync-vision`, `/lint-wiki`, собирать знания не только из `RAW_inputs/`, но и из значимых изменений по всему репозиторию.

Основной pipeline выполняется пользователем вручную. Репозиторий должен предоставить все необходимое для такого выполнения: структуру папок, шаблоны, command-документацию, проверочные скрипты, README/runbook и явные чек-листы для утреннего, встречного, post-meeting и weekly сценариев.

Исключение: `repository-change ingest` должен запускаться автоматически при значимых изменениях репозитория, которые требуют коммита. Автоматизация не должна менять код, конфигурацию, миграции или тесты; она должна создавать или обновлять только knowledge-документацию. После `/ingest` допускается post-ingest correction: исправлять старую документацию можно только для конфликтов, которые уже зафиксированы в `Vision_wiki/decisions/followups/index.md` и связаны с `Code_wiki`. Новые или неясные конфликты сначала добавляются в follow-up index.

Существующая `docs/agent-memory/` остается в репозитории как короткая инженерная память Codex: сессии, решения, паттерны, багфиксы и быстрый `file-map.md`. Новая wiki-система становится более широкой базой знаний проекта: продуктовое видение, техническая wiki, сырые источники, состояние проекта, конфликты, follow-up'ы и weekly health workflow.

## Что Переносится

Переносятся только шаблонные и методологические элементы из PO-репозитория:

- структура директорий `RAW_inputs/`, `Vision_wiki/`, `Code_wiki/`, `memory/`, `Общие_принципы/`;
- шаблоны из `Vision_wiki/_templates/` и `Code_wiki/_templates/`;
- `_info.md` и пустые индексные файлы, очищенные от фактов donor-проекта;
- `memory/llm-wiki-method.md` как методология ведения LLM-wiki;
- `memory/project-state.md` как живое состояние проекта, но с пустым/GeoService-specific baseline;
- command-документация, repo-local skills или runbook'и для ручного выполнения `/discover`, `/ingest`, `/sync-vision`, `/lint-wiki`;
- `scripts/lint-wiki.py`, адаптированный под GeoService и Windows/Python workflow.
- Obsidian-конфигурация для просмотра wiki-графа, без пользовательских workspace/cache файлов.

PO-репозиторий `C:\Repositories\ai-po-template-experiments` используется только как read-only источник шаблонов и методологии. Его файлы нельзя редактировать, перемещать, удалять, форматировать или коммитить в рамках этой работы. Все изменения выполняются только в `C:\Repositories\geoservice`.

Не переносятся:

- факты, названия, стейкхолдеры, метрики и дорожные карты Polus/Geoportal;
- содержимое donor `Vision_wiki/chats`, `Vision_wiki/concepts`, `Code_wiki/архитектура` и похожие project-specific ноды;
- donor `RAW_inputs` кроме пустой структуры и `_info.md`;
- donor `memory/project-state.md` как фактическое состояние проекта;
- Claude-specific hooks, если они не работают в Codex без отдельной адаптации.

## Структура

Новая структура должна быть максимально близкой к PO-репозиторию:

```text
AGENTS.md
index.md
RAW_inputs/
  index.md
  meetings/
  documents/
  code/
  docs/
  chats/
  research_results/
Vision_wiki/
  index.md
  _templates/
  chats/
  concepts/
  decisions/
    assumptions/
    conflicts/
    followups/
  entities/
    stakeholders/
    personas/
    competitors/
  solution/
Code_wiki/
  index.md
  _templates/
  архитектура/
    ADR/
  dev_setup/
  сборка/
  deployment/
    runbooks/
    postmortems/
  правила_и_стиль/
  глоссарий/
  состояние_проекта/
memory/
  llm-wiki-method.md
  project-state.md
Общие_принципы/
scripts/
  lint-wiki.py
.obsidian/
  app.json
  appearance.json
  core-plugins.json
  graph.json
  templates.json
docs/agent-memory/
  ...
```

`docs/agent-memory/` не дублирует PO-wiki. Его роль - компактная инженерная память для будущих агентских сессий. При значимой работе агент может обновлять оба слоя:

- `docs/agent-memory/` - краткая долговременная запись для Codex retrieval;
- `Code_wiki/` или `Vision_wiki/` - полноценная проектная knowledge-нода, если изменение влияет на архитектуру, продукт, workflow, runbook, конфликт или follow-up.

## Pipeline

### Утро

Пользователь вручную запускает утренний pipeline по README/runbook:

1. `/sync-vision`.
2. Проверяет `memory/project-state.md`.
3. Проверяет наличие новых файлов в `RAW_inputs/`.
4. Если новые RAW-файлы есть, запускает `/ingest` для каждого релевантного файла или предлагает порядок обработки, если объем большой.

### Перед Встречей

Пользователь вручную запускает подготовку к встрече:

1. `/discover --context ... --phase ...`.
2. Читает `memory/project-state.md`, `Vision_wiki/index.md` и релевантные ноды.
3. Подбирает 10-15 вопросов под контекст и фазу.
4. Создает чек-лист встречи в `Vision_wiki/chats/YYYY-MM-DD-<topic>-checklist.md`.
5. Обновляет `memory/project-state.md` разделом про последний discovery.

### После Встречи

Пользователь вручную выполняет post-meeting pipeline:

1. Кладет или ожидает транскрипт в `RAW_inputs/meetings/`.
2. Запускает `/ingest <path>`.
3. Обновляет `Vision_wiki/`: concepts, decisions, entities, solution и session-сводку.
4. Фиксирует конфликты в `Vision_wiki/decisions/conflicts/`.
5. Фиксирует follow-up'ы в `Vision_wiki/decisions/followups/`.
6. Выполняет post-ingest correction только для уже зафиксированных в `Vision_wiki/decisions/followups/index.md` конфликтов, связанных с `Code_wiki`: исправляет старую документацию на основе новых knowledge-изменений. Конфликты вне `Code_wiki` не исправляются автоматически.
7. Обновляет `RAW_inputs/index.md`, `Vision_wiki/index.md`, корневой `index.md` и `memory/project-state.md`.

### Крупные Изменения В Репозитории

Если работа в репозитории требует коммита и меняет стабильное знание о проекте, `repository-change ingest` запускается автоматически перед завершением работы или перед коммитом:

1. Определяет измененные файлы через `git status` и при необходимости `git diff --stat`.
2. Классифицирует изменение:
   - feature implementation;
   - architecture decision;
   - bug root cause;
   - runbook/dev setup;
   - workflow or style rule;
   - product requirement update.
3. Обновляет `Code_wiki/` или `Vision_wiki/` атомарными нодами.
4. Обновляет `memory/project-state.md`.
5. При необходимости добавляет короткую запись в `docs/agent-memory/`.

Этот поток не должен сохранять временный шум, полные diff'ы, build output или секреты. Он фиксирует только знания, которые будут полезны через неделю.

Автоматический запуск должен быть fail-soft: если изменение нельзя уверенно классифицировать или безопасно записать, pipeline не блокирует коммит бесконечно и добавляет follow-up в `Vision_wiki/decisions/followups/index.md` с указанием, что knowledge update требует ручного решения. Post-ingest correction в автоматическом сценарии также ограничен конфликтами, связанными с `Code_wiki`.

### Раз В Неделю

Пользователь вручную запускает weekly health pipeline:

1. `/lint-wiki`.
2. `/sync-vision`.
3. Формирует отчет здоровья wiki:
   - broken wikilinks;
   - orphan nodes;
   - missing frontmatter;
   - stale files;
   - empty dirs;
   - открытые конфликты;
   - открытые follow-up'ы.
4. Обновляет `memory/project-state.md`.

## Команды

Команды `/discover`, `/ingest`, `/sync-vision`, `/lint-wiki` в этом дизайне являются ручными процедурами репозитория. Реализация должна дать пользователю один понятный способ запускать каждую процедуру: Markdown runbook, repo-local skill, script wrapper или их сочетание.

`repository-change ingest` является автоматической процедурой. Реализация должна предусмотреть механизм автозапуска перед коммитом или при обнаружении значимых staged/working-tree изменений. Подход должен быть совместим с текущим репозиторием и не требовать внешних сервисов.

### `/ingest`

Обрабатывает источники из `RAW_inputs/` и значимые изменения репозитория. Источники классифицируются по папке или по типу изменения:

- `RAW_inputs/meetings/` -> session-сводки, concepts, decisions, conflicts, follow-up'ы;
- `RAW_inputs/documents/` -> Vision_wiki concepts и solution;
- `RAW_inputs/code/` -> Code_wiki architecture/state;
- `RAW_inputs/docs/` -> Code_wiki или Vision_wiki по содержанию;
- repository changes -> Code_wiki/Vision_wiki и `project-state`.

### `/discover`

Готовит discovery-встречи и checklist'ы. Для существующего GeoService не нужен режим "переименовать корневую папку"; вместо этого команда должна работать с текущим проектом и текущими wiki-нода.

### `/sync-vision`

Актуализирует индексы, метрики и `memory/project-state.md`. Не редактирует смысловые ноды без необходимости.

### `/lint-wiki`

Запускает `scripts/lint-wiki.py`, проверяет структуру wiki и готовит отчет. Автоисправления допустимы только для структурных проблем и только когда команда явно вызвана с режимом fix.

## Data Flow

```text
RAW_inputs/                  repository changes
    |                               |
    |                               +-- automatic repository-change ingest
    |                                                   |
    +------ manual /ingest -----------------------------+
                     |
        +------------+-------------+
        |                          |
   Vision_wiki/                Code_wiki/
        |                          |
        +------------+-------------+
                     |
              /sync-vision
                     |
          index.md + memory/project-state.md
                     |
              /lint-wiki weekly health
```

`docs/agent-memory/` подключается как быстрый retrieval-слой Codex, а не как источник фактов для продуктовой wiki. Если есть конфликт между RAW и wiki, RAW считается источником истины, а конфликт фиксируется явно.

## Ошибки И Границы

- Если факт не подтвержден RAW, коммитом, файлом в репозитории или явным ответом пользователя, он помечается как hypothesis/inferred.
- `RAW_inputs/` не редактируется, кроме добавления новых файлов и индекса.
- Секреты, `.env` значения, токены, приватные персональные данные и временные логи не попадают в wiki.
- Donor-факты Polus/Geoportal не копируются в GeoService.
- Donor-репозиторий `C:\Repositories\ai-po-template-experiments` нельзя изменять; при переносе разрешены только чтение и копирование шаблонного смысла в файлы GeoService.
- При массовом ingest больших файлов агент делает первый проход и предлагает углубление по разделам, а не пытается переварить все за один раз.
- После `/ingest`, если новые knowledge-файлы конфликтуют со старой документацией, самостоятельно исправлять можно только конфликты, которые уже зафиксированы в `Vision_wiki/decisions/followups/index.md` и связаны с `Code_wiki`. Исправление выполняется в старой документации на основе новых knowledge-изменений, чтобы привести технические документы к актуальной версии. Если конфликт не зафиксирован в follow-up index или не связан с `Code_wiki`, его нельзя исправлять напрямую: нужно сначала добавить или уточнить follow-up. Код, конфигурацию, миграции и тесты нельзя менять в рамках такого исправления без отдельного явного запроса или implementation task.

## Testing And Verification

Минимальная проверка после внедрения:

```powershell
python scripts/lint-wiki.py --root .
rg -n "/sync-vision|/ingest|RAW_inputs|project-state|repository changes" AGENTS.md index.md memory Vision_wiki Code_wiki RAW_inputs scripts
rg -n "Polus|Geoportal|Георгий|Казань|Краснояр" index.md memory Vision_wiki Code_wiki RAW_inputs
```

Ожидаемый результат:

- `lint-wiki.py` запускается без Python dependencies вне стандартной библиотеки;
- команды и pipeline находятся через `rg`;
- donor-specific факты отсутствуют в шаблонной базе;
- `docs/agent-memory/` остается доступной и не конфликтует с новой wiki.

## Acceptance Criteria

- В GeoService есть структура wiki как в PO-репозитории.
- Перенесены только шаблонные файлы и методология, без donor-фактов Polus/Geoportal.
- Во время реализации не изменяются файлы в `C:\Repositories\ai-po-template-experiments`; все правки находятся только в `C:\Repositories\geoservice`.
- `AGENTS.md` и wiki README описывают, что основной pipeline выполняется пользователем вручную, и дают понятные инструкции для `/ingest`, `/discover`, `/sync-vision`, `/lint-wiki`.
- `RAW_inputs/` используется как сырая память, но знания могут собираться и из значимых изменений по всему репозиторию.
- После реализации новой фичи или важного действия `repository-change ingest` запускается автоматически и обновляет knowledge base, если изменение будет полезно через неделю.
- Post-ingest correction исправляет только конфликты, которые уже есть в `Vision_wiki/decisions/followups/index.md` и связаны с `Code_wiki`; исправлять можно старую документацию на основе новых knowledge-изменений, но не код, конфигурацию, миграции или тесты.
- `docs/agent-memory/` и новая PO-wiki имеют разные роли и не конфликтуют.
- `scripts/lint-wiki.py` работает в GeoService и проверяет новую wiki-структуру.
- Obsidian graph можно использовать для навигации по wiki; переносится только общий vault/config, пользовательские workspace/cache файлы игнорируются.
- `memory/project-state.md` является живым состоянием проекта и обновляется при ручном выполнении pipeline.

## Risks

- Риск: две системы памяти будут казаться дублирующимися. Смягчение: явно разделить роли в `AGENTS.md` и `memory/project-state.md`.
- Риск: агенты начнут сохранять слишком много временного шума. Смягчение: критерий "полезно через неделю" и запрет на build output/full diff/full chats.
- Риск: donor-факты попадут в GeoService при копировании. Смягчение: переписывать индексы и state вручную под пустой шаблон, затем проверить `rg` по donor-терминам.
- Риск: slash commands не являются native-командами Codex. Смягчение: оформить их как repo-local skills/instructions или Markdown command docs, чтобы пользователь мог запускать ручной pipeline и при необходимости просить агента выполнить конкретную процедуру.
- Риск: автоматический `repository-change ingest` будет мешать коммитам. Смягчение: сделать его fail-soft, ограничить правки knowledge-документацией и фиксировать неясные случаи в `Vision_wiki/decisions/followups/index.md`.
