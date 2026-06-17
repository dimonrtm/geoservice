# Очистка Памяти И Legacy Repository-Change Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Удалить подтверждённый process/task-log шум из agent memory и
legacy repository-change history без потери уникального знания.

**Architecture:** Каноническими источниками остаются `Vision_wiki`,
`Code_wiki`, design/plan, code и durable decision-записи. Подтверждённые
session-файлы и 19 legacy-блоков удаляются из рабочего дерева, прямые ссылки
переводятся на канонические источники, после чего read-only аудит подтверждает
новое состояние. Git остаётся историческим архивом.

**Tech Stack:** Markdown, PowerShell, Python standard library, `unittest`.

---

### Task 1: Зафиксировать Границы Cleanup

**Files:**
- Read: `docs/agent-memory/sessions/*.md`
- Read: `Vision_wiki/`
- Read: `Code_wiki/`
- Read: `docs/superpowers/`

- [ ] Получить из `audit-memory.py` 15 process-only и 17
  canonical-source session-кандидатов.
- [ ] Проверить `Summary`, `Context`, `Actions` и `Related files` каждого
  canonical-source кандидата.
- [ ] Убедиться, что каждое устойчивое решение уже хранится в каноническом
  источнике; при отсутствии источника остановить удаление конкретного файла.

### Task 2: Удалить Подтверждённые Session-Записи

**Files:**
- Delete: 33 файла, классифицированных как `noisy_session` или
  `canonical_source_session`; последний кандидат обнаружен после добавления
  `docs/release_1/sprint_1/` в canonical prefixes аудита
- Preserve: `docs/agent-memory/sessions/2026-05-30-agent-memory-mvp.md`

- [ ] Удалить только подтверждённые process/canonical-source файлы.
- [ ] Не удалять исходную memory MVP запись вне подтверждённого audit-набора.

### Task 3: Удалить Legacy Repository-Change History

**Files:**
- Modify:
  `Code_wiki/состояние_проекта/repository_change_ingest.md`

- [ ] Удалить раздел `Исторические Записи, Ожидающие Ревизии` и все 19
  legacy-блоков.
- [ ] Оставить frontmatter, правила и три строки активного реестра.

### Task 4: Исправить Прямые Ссылки

**Files:**
- Modify: `Code_wiki/состояние_проекта/repository_snapshot.md`
- Modify:
  `docs/superpowers/plans/2026-05-30-project-knowledge-wiki-pipeline.md`
- Modify:
  `docs/release_1/sprint_1/2026-06-13-sprint-1-day-2-roles-access-implementation-plan.md`
- Modify: `memory/project-state.md`

- [ ] Удалить или заменить прямые ссылки на удалённые session-файлы.
- [ ] Убрать из live state ожидание legacy cleanup.
- [ ] Не переписывать исторические продуктовые и технические решения.

### Task 5: Проверить Результат

**Files:**
- No repository edits expected

- [ ] Запустить `python -m unittest discover -s scripts\tests -v`.
- [ ] Запустить `python scripts/check-memory-needed.py --check`.
- [ ] Дважды запустить `audit-memory.py` и подтвердить deterministic/read-only.
- [ ] Подтвердить отсутствие `legacy_registry_entry`,
  `registry_budget_exceeded`, `session_budget_exceeded` и broken references.
- [ ] Запустить `lint-wiki.py`, `git diff --check` и placeholder scan.
- [ ] Проверить, что staging не изменился. Не выполнять `git add` или commit.
