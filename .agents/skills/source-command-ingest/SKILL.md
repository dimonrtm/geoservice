---
name: source-command-ingest
description: Ручная процедура /ingest для обработки RAW_inputs и значимых источников проекта в Vision_wiki/Code_wiki.
---

# /ingest

`/ingest` превращает сырой источник в атомарные wiki-ноды с источниками, связями и follow-up'ами. Он не должен менять код, конфигурацию, миграции или тесты.

## Обязательный Контекст

Перед ingest прочитать:

- `Vision_wiki/index.md` - что уже есть в продуктовой wiki.
- `Code_wiki/index.md` - что уже есть в технической wiki.
- `Vision_wiki/_templates/_info.md` и нужные шаблоны.
- `Code_wiki/_templates/_info.md` и нужные шаблоны.
- `memory/llm-wiki-method.md` - правила атомарных нод, source, frontmatter и wikilinks.
- `memory/project-state.md` - текущее состояние pipeline.

## Шаг 1. Определить Объект Ingest

- Если пользователь указал путь, работать с ним.
- Если путь не указан, проверить `RAW_inputs/` и найти новые или измененные файлы, которых еще нет в обработанных source-записях `RAW_inputs/index.md`, `Vision_wiki/chats/`, `Vision_wiki/index.md`, `Code_wiki/index.md` или `memory/project-state.md`.
- Если новых RAW-кандидатов нет, ничего не менять и коротко сообщить, что ingest не выполнен; предложить явно указать путь, выполнить `/ingest repository-snapshot` или `/ingest repository-change`, если это подходит к ситуации.
- Если найдено 1-5 однозначных RAW-кандидатов, обработать их по очереди в одном запуске `/ingest`: для каждого источника выполнить шаги 2-8, затем в финальном отчете перечислить все обработанные файлы и созданные/обновленные wiki-ноды.
- Если найдено больше 5 RAW-кандидатов, показать список, сгруппированный по папкам `RAW_inputs/`, и попросить подтверждение: обработать все, выбрать часть или начать с одного файла.
- Если есть неоднозначность, не запускать batch без подтверждения. Неоднозначность: непонятен тип источника, файл слишком большой для надежного прохода, несколько файлов выглядят как версии одного документа, уже есть похожая wiki-нода, есть возможный конфликт с существующей документацией, либо источник содержит потенциальные секреты/персональные данные.
- Если источник не из `RAW_inputs/`, явно указать, почему он значим для wiki.

## Шаг 2. Классифицировать Источник

- `RAW_inputs/meetings/` - транскрипт встречи: summary в `Vision_wiki/chats/`, факты в `concepts/`, `decisions/`, `entities/`, `solution/`.
- `RAW_inputs/documents/` - ТЗ, спека, презентация: требования в `Vision_wiki/solution/`, концепты в `Vision_wiki/concepts/`, технические следствия в `Code_wiki/`.
- `RAW_inputs/code/` - фрагменты или обзоры кода: `Code_wiki/архитектура/`, `Code_wiki/состояние_проекта/`, ADR/runbook candidates.
- `RAW_inputs/docs/` - документация проекта: `Vision_wiki/` или `Code_wiki/` по смыслу.
- `RAW_inputs/chats/` - переписка: summary в `Vision_wiki/chats/`, факты по соответствующим нодам.
- `RAW_inputs/research_results/` - research: concepts, decisions, risks, follow-up'ы.
- Уже существующее состояние репозитория - первично фиксируется агентом через `/ingest repository-snapshot` в `Code_wiki/`.
- Значимые изменения репозитория - фиксируются агентом через `/ingest repository-change` в `Code_wiki/состояние_проекта/`.

## Режим `repository-snapshot`

`/ingest repository-snapshot` нужен для первичной или периодической инвентаризации уже существующей кодовой базы, даже если файлы не менялись. Это обзор текущего состояния репозитория, а не diff.

Когда вызывать:

- при первом наполнении `Code_wiki` для существующего проекта;
- после крупных внешних изменений, если агент не видел их как `repository-change`;
- когда `Code_wiki` пустая или явно отстает от реальной структуры проекта.

Порядок:

1. Прочитать `README.md`, `AGENTS.md`, `docs/agent-memory/file-map.md`, `memory/project-state.md`, `Code_wiki/index.md`.
2. Построить карту репозитория через `rg --files`, исключая `.git/`, `.obsidian/`, `node_modules/`, `dist/`, `build/`, `.venv/`, `__pycache__/`, временные файлы и саму wiki, если она не является объектом обзора.
3. Найти ключевые входные точки и конфигурацию: `pyproject.toml`, `requirements*.txt`, `package.json`, `docker-compose*.yml`, `Dockerfile*`, `alembic.ini`, `vite.config.*`, entrypoints backend/frontend, scripts, tests и миграции.
4. Читать файлы порциями и извлекать только устойчивые знания: архитектурные области, сервисы, API, модели данных, dev setup, build/deploy, правила стиля, тестовые стратегии, риски и follow-up'ы.
5. Создать или обновить технические ноды в `Code_wiki/архитектура/`, `Code_wiki/dev_setup/`, `Code_wiki/сборка/`, `Code_wiki/deployment/`, `Code_wiki/правила_и_стиль/`, `Code_wiki/глоссарий/`, `Code_wiki/состояние_проекта/`.
6. Создать или обновить журнал snapshot'ов в `Code_wiki/состояние_проекта/repository_snapshot.md`: дата, область обзора, прочитанные источники, созданные/обновленные wiki-ноды, пробелы и follow-up'ы.
7. Обновить `Code_wiki/index.md` и `memory/project-state.md`.
8. Запустить `python scripts/lint-wiki.py --root .`.

Ограничения:

- Не пытаться индексировать весь репозиторий дословно. Snapshot фиксирует знания и структуру, а не копирует код.
- Не писать секреты, значения `.env`, токены, пароли и персональные данные.
- Не менять код, конфигурацию, миграции или тесты как часть snapshot.
- Если обзор большой, делить на области: backend, frontend, infra, scripts, docs.

## Режим `repository-change`

`/ingest repository-change` вызывается только если завершённая работа содержит
новое устойчивое техническое знание, которое требуется отразить в
`Code_wiki`.

Завершение плана, размер задачи, количество изменённых файлов, запуск тестов и
commit сами по себе не являются триггерами.

До вызова режима определяется только наличие нового устойчивого технического
знания. Конкретные ноды и операция create/update заранее не задаются:
`Repository Change Ingest` определяет их самостоятельно.

Порядок:

1. Определить новое устойчивое техническое знание и его проверяемые источники.
2. Прочитать только нужные части `git status --short`, `git diff --stat` и
   точечные diffs, чтобы проверить факты.
3. Изучить релевантные ноды и индекс `Code_wiki`, затем определить, какие ноды
   нужно создать или содержательно обновить.
4. Создать или обновить выбранные ноды без пересказа плана, временных шагов и
   полного списка файлов.
5. Добавить в активный реестр
   `Code_wiki/состояние_проекта/repository_change_ingest.md` по одной строке
   на содержательно изменённую ноду: дата, нода, причина и источник.
6. Не создавать запись для правок только индексов, live state, самого реестра
   или других служебных файлов pipeline.
7. Обновить `memory/project-state.md` только если изменился живой статус
   проекта; не добавлять туда историю завершённых задач.
8. Запустить `python scripts/lint-wiki.py --root .`.

Если нового устойчивого технического знания нет, режим не вызывается и пустая
запись не создаётся. Pre-commit не проверяет и не запускает repository-change
ingest. Триггер не привязан к commit.

Ограничения:

- Не создавать запись только о выполнении plan/task/tests.
- Не перечислять code files и verification logs в активном реестре.
- Не создавать строку реестра для изменений только index/state.
- Не изменять legacy history до подтверждённой cleanup-задачи.

## Шаг 3. Читать Источник Порциями

- Большие файлы читать блоками.
- Транскрипты разбирать по смысловым кускам.
- Не пытаться поглотить большой источник одним проходом, если теряется точность.
- Не выдумывать факты, которых нет в источнике.

## Шаг 4. Извлечь Факты

Для каждого факта определить:

- `source` - путь к RAW/source или ссылка на repository-change entry.
- `type` - concept, decision, entity, risk, assumption, followup, solution, technical note.
- уверенность - verified, inferred или hypothesis.
- связи - какие wiki-ноды нужно связать wikilinks.

## Шаг 5. Разнести По Wiki

- Концепты: `Vision_wiki/concepts/<slug>.md`, шаблон `Vision_wiki/_templates/concept.md`.
- Краткое описание проекта: `Vision_wiki/concepts/about_project.md`, шаблон `Vision_wiki/_templates/about_project.md`.
- Product Vision Board: `Vision_wiki/concepts/product_vision_board.md`, шаблон `Vision_wiki/_templates/product_vision_board.md`.
- Lean Canvas: `Vision_wiki/concepts/lean_canvas.md`, шаблон `Vision_wiki/_templates/lean_canvas.md`.
- JTBD: `Vision_wiki/concepts/jtbd.md`, шаблон `Vision_wiki/_templates/jtbd.md`.
- Персоны: `Vision_wiki/entities/personas/<slug>.md`, шаблон `Vision_wiki/_templates/persona.md`.
- Решения: `Vision_wiki/decisions/<slug>.md` или ADR в `Code_wiki/архитектура/ADR/`.
- Конфликты: `Vision_wiki/decisions/conflicts/YYYY-MM-DD-<topic>.md`.
- Допущения: `Vision_wiki/decisions/assumptions/<slug>.md`.
- Follow-up'ы: строка в `Vision_wiki/decisions/followups/index.md`.
- Solution: `Vision_wiki/solution/USM.md`, `roadmap.md`, `nfr.md`, `architecture_vision.md`.
- Технические знания: `Code_wiki/архитектура/`, `dev_setup/`, `сборка/`, `deployment/`, `правила_и_стиль/`, `глоссарий/`, `состояние_проекта/`.

## Шаг 6. Создать Summary Источника

Для meeting/document/chat источника создать или обновить `Vision_wiki/chats/YYYY-MM-DD-<source>.md`:

- контекст источника;
- главные тезисы;
- решения;
- конфликты;
- follow-up'ы;
- цитаты, если они короткие и важные;
- links на созданные ноды.

## Шаг 7. Обновить Индексы И State

- `RAW_inputs/index.md` - отметить обработанный источник.
- `Vision_wiki/index.md` - добавить ссылки на важные новые ноды.
- `Code_wiki/index.md` - добавить ссылки на важные технические ноды.
- `memory/project-state.md` - обновить последний `/ingest`.
- `Vision_wiki/decisions/followups/index.md` - сохранить открытые вопросы и конфликты.

## Шаг 8. Проверить

Запустить:

```powershell
python scripts/lint-wiki.py --root .
```

## Ограничения

- Не менять `RAW_inputs/`; только читать.
- Не менять код, конфигурацию, миграции и тесты как часть `/ingest`.
- Не исправлять старую документацию во время `/ingest`; только фиксировать конфликт/follow-up.
- Post-ingest correction разрешен только после `/ingest` и только для конфликтов из `Vision_wiki/decisions/followups/index.md`, связанных с `Code_wiki`.
- Wiki-контент писать на русском языке; пути, команды, API, идентификаторы и имена файлов не переводить.
