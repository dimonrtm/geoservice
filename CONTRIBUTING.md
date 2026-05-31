# Contributing

## Ветки
- `main` — стабильная ветка.
- Для работы создаём ветки:
  - `docs/*` для документации
  - `feat/*` для новых фич
  - `fix/*` для исправлений
  - `chore/*` для тех. обслуживания

Примеры:
- `feat/auth-basic`
- `docs/day-01-notes`
- `fix/import-nullref`

## Коммиты
Пишем сообщения в формате:
`<type>: <краткое действие>`

Типы:
- `feat:` новая функциональность
- `fix:` исправление бага
- `docs:` документация
- `chore:` обслуживание, инфраструктура, форматирование

Правила:
- Один коммит — одна смысловая задача (атомарность).
- Перед коммитом проверяем:
  - `git status`
  - `git diff`
  - `git diff --staged`

  ## Сообщения коммитов (обязательно)
Формат:

type: короткое описание

Где type ∈ {feat, fix, docs, chore, ci, refactor, test}

Примеры:
- feat: add layer import pipeline
- fix: handle null geometry in parser
- docs: update day 1 notes
- chore: bump dependencies
- ci: add pre-commit workflow

Запрещены сообщения вида:
- fix
- update
- wip
- temp

## Секреты и конфиги
- `.env` и любые секреты не коммитим.
- Вместо этого используем `.env.example`.

## Перед merge в main
- Ветка должна быть синхронизирована с `origin/main`.
- История должна быть читаемой (без мусорных коммитов).

## Knowledge Wiki

- Wiki-контент ведем на русском языке.
- Пути, команды, API, типы, идентификаторы, имена файлов, имена пакетов и код не переводим.
- Все wiki-ноды должны иметь frontmatter.
- Для связей используем Obsidian wikilinks: `[[Code_wiki/index]]`.
- Сырые материалы кладем в `RAW_inputs/`, обработанные знания - в `Vision_wiki/` и `Code_wiki/`.
- После полного завершения реализации плана или крупной задачи агент вызывает `/ingest repository-change`.
- Pre-commit не запускает и не проверяет repository-change ingest.
- `repository-change ingest` пишет только knowledge-документацию и не меняет код, конфигурацию, миграции или тесты.
- Post-ingest correction разрешен только для конфликтов из `Vision_wiki/decisions/followups/index.md`, связанных с `Code_wiki`.
