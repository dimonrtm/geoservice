# Правила Работы Долговременной Памяти Агентов

Date: 2026-05-30
Type: decision
Tags: agent-memory, workflow, markdown, retrieval, git
Related files:

- `AGENTS.md`
- `docs/agent-memory/protocol.md`
- `docs/agent-memory/file-map.md`
- `docs/superpowers/specs/2026-05-30-agent-memory-design.md`
- `docs/superpowers/specs/2026-06-13-memory-knowledge-base-optimization-design.md`
- `docs/superpowers/plans/2026-06-13-memory-knowledge-base-optimization.md`

## Summary

Память агентов в GeoService хранится внутри репозитория как Markdown и
версионируется через Git. Новая запись создаётся только для уникального
долговременного знания, которое нельзя надёжно восстановить из канонических
файлов. Новый чат читает минимальный протокол и загружает только релевантные
записи. Git staging, commit и push выполняет только пользователь; агентам эти
операции запрещены в этом репозитории.

## Context

Первоначальный Markdown-подход сохраняется без JSONL, базы данных, embeddings
и внешних зависимостей. Оптимизация потребовалась, потому что критерий
«значимой работы» превращал память и repository-change ingest в хронологию
задач, тестовых прогонов и изменений файлов.

## Current Git Rule

Агентам запрещено выполнять `git add`, `git commit` и `git push` в этом
репозитории или запрашивать для этих команд approval/elevated permissions.
Только пользователь проверяет, индексирует, коммитит и отправляет изменения.
Это правило заменяет условные разрешения, записанные 2026-06-15 и 2026-06-16,
и имеет приоритет над требованиями skills создать commit.

## Actions

- 2026-05-30: Зафиксировано, что память должна быть repo-local и Git-versioned.
- 2026-05-30: Выбран ручной Markdown-формат записей.
- 2026-05-30: Выбран компактный `file-map.md` как самый экономный по токенам способ находить связанные файлы.
- 2026-05-30: Выбрана структура `sessions/`, `decisions/`, `patterns/`, `bugfixes/`.
- 2026-06-13: Согласован дизайн оптимизации памяти и knowledge base. После
  реализации memory-записи должны создаваться только для уникального
  долговременного знания, `sessions/` становится исключением, а
  `/ingest repository-change` вызывается только при наличии нового устойчивого
  технического знания для `Code_wiki`; конкретные ноды и create/update
  определяет и выполняет сам ingest.
- 2026-06-13: Подготовлен implementation plan с read-only memory audit,
  бюджетами `20 sessions / 90 days / 200 lines / 24 KiB`, сохранением legacy
  записей до отчёта и отдельным пользовательским подтверждением cleanup.
- 2026-06-13: Реализованы узкий memory gate, исключительный режим
  `sessions/`, read-only `/audit-memory`, двухусловный repository-change gate
  и компактный реестр. После явного подтверждения пользователя process-only
  и canonical-source session task logs удалены, legacy repository-change
  history убрана из рабочего дерева, а Git оставлен историческим архивом.
- 2026-06-15: Зафиксировано пользовательское правило работы с Git: агент не
  выполняет `git add`, `git commit` и не создает commit без прямой явной
  просьбы пользователя. Подтверждение design, завершение реализации или
  требование skill закоммитить документ сами по себе не считаются разрешением.
  По умолчанию изменения остаются в working tree для пользовательской
  проверки и самостоятельного commit.
- 2026-06-16: Правило подтверждено повторно после отказа от staging design spec:
  агент должен оставлять изменения непроиндексированными и не коммитить их,
  пока пользователь явно не попросит выполнить `git add`/`git commit` после
  своей проверки.
- 2026-07-15: Пользователь заменил прежнее условное разрешение абсолютным
  repository-wide правилом: агентам запрещено выполнять `git add`, `git commit`
  и `git push`, а также запрашивать approval или elevated permissions для этих
  команд. Review, staging, commit и push выполняет только пользователь. Явное
  одобрение design, завершение работы и требование skill создать commit не
  отменяют запрет; изменения остаются unstaged для пользовательской проверки.

## Verification

Проверяется smoke-поиском после внедрения:

```powershell
rg -n "уникального|read-only|repository-change gate|file-map" docs/agent-memory
```

Ожидается, что поиск находит эту запись и протокол памяти.

## Retrieval Hints

agent memory, долговременная память, repo-local, markdown memory, file-map, significant work, значимая работа, протокол памяти, новый чат, Git-versioned memory, оптимизация памяти, repository-change trigger, memory audit, агентам запрещены git add git commit git push, commit выполняет только пользователь, не запрашивать approval для Git
