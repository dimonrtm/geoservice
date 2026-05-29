# План реализации долговременной памяти Codex-агентов

> **Для агентных исполнителей:** перед реализацией использовать `superpowers:subagent-driven-development` (рекомендуется) или `superpowers:executing-plans`. Выполнять задачи по чекбоксам `- [ ]`, не перескакивая через проверки.

**Цель:** создать в репозитории `GeoService` долговременную память для Codex-агентов, чтобы новые чаты могли быстро восстановить важный контекст проекта, историю действий, принятые решения и связанные файлы.

**Архитектура:** хранить память прямо в репозитории в виде Markdown и JSONL под `docs/agent-memory/`; добавить корневой `AGENTS.md` с правилами старта для агентов; добавить небольшой Python CLI `scripts/agent_memory.py` для поиска, проверки и записи памяти. В первом MVP не использовать внешние сервисы, базы данных, embeddings или API-ключи.

**Стек:** Markdown, JSONL, Python standard library, pytest из root-level `requirements-dev.txt`, Git, `rg` для обычного поиска по репозиторию.

---

## Проверка Готовности Плана

Вердикт: **план готов к реализации после выполнения задач в указанном порядке**.

Исходная идея была правильной: память должна быть repo-local, простой, версионируемой и доступной для чтения человеком. Но перед реализацией нужен более полный цикл планирования, чтобы не получить набор файлов, который выглядит полезно, но не заставляет агентов реально вспоминать контекст и записывать итоги работы.

Что уже хорошо:

- память хранится в Git и видна в diff;
- нет зависимости от внешнего сервиса;
- `AGENTS.md` подходит как точка входа для новых чатов;
- Markdown-записи удобны для чтения, а JSONL-индексы удобны для поиска;
- структура не конфликтует с текущей документацией в `docs/`.

Что обязательно учтено в этом плане:

- разделены MVP и будущие улучшения;
- описаны варианты архитектуры и выбранный подход;
- добавлены критерии `Definition of Ready` и `Definition of Done`;
- CLI обязан поддерживать не только `search` и `validate`, но и `add-session`;
- поиск обязан смотреть не только JSONL, но и Markdown-записи памяти;
- валидация обязана ловить битый JSONL, дубликаты id, отсутствующие поля, сломанные пути и очевидные secret-like значения;
- проверка памяти в MVP запускается вручную через README-команду; CI можно добавить позже.

Главный риск: агент может пропустить протокол, если среда не прочитает `AGENTS.md`. Смягчение: держать протокол коротким, команду поиска простой, а память в очевидном месте `docs/agent-memory/`.

## Полный Цикл Планирования

### Пользовательская Цель

Пользователь хочет, чтобы Codex-агенты сохраняли ключевые моменты из чатов и историю действий в репозитории. При открытии нового чата агент должен по новому сообщению пользователя быстро найти связанный контекст и файлы, прежде чем менять код.

### Принятые Предположения

- Память относится только к этому репозиторию.
- Память должна быть версионируемой и ревьюиться через Git.
- Первый вариант должен работать офлайн и без установки новых зависимостей.
- Нельзя сохранять полные чаты, секреты, токены, пароли и `.env`.
- Для MVP достаточно keyword search, если он хорошо индексирует записи и файлы.
- Embeddings можно добавить позже, не меняя публичный CLI-контракт.

### Рассмотренные Подходы

1. **Рекомендуемый: Markdown + JSONL + Python CLI.**
   - Плюсы: прозрачные diff, легко читать людям и агентам, не нужны сервисы и зависимости.
   - Минусы: поиск менее умный, чем embeddings; качество памяти зависит от дисциплины записи.

2. **SQLite база внутри репозитория.**
   - Плюсы: можно делать более строгие запросы и связи.
   - Минусы: хуже diff и merge, сложнее ревьюить, агенту труднее читать руками.

3. **Внешний vector store или embedding-сервис.**
   - Плюсы: лучший семантический поиск.
   - Минусы: ключи, настройка, нестабильность окружения, лишняя сложность для первого шага.

Решение: для MVP выбрать подход 1. Оставить embeddings как необязательное будущее улучшение за тем же интерфейсом `scripts/agent_memory.py`.

### MVP Scope

Входит в MVP:

- `AGENTS.md` с обязательным стартовым протоколом для агентов;
- `docs/agent-memory/protocol.md` с правилами чтения и записи памяти;
- `docs/agent-memory/README.md`;
- Markdown-записи для `sessions`, `decisions`, `patterns`;
- `docs/agent-memory/index.jsonl` для записей памяти;
- `docs/agent-memory/file-map.jsonl` для быстрого поиска файлов по смыслу;
- `scripts/agent_memory.py search`;
- `scripts/agent_memory.py validate`;
- `scripts/agent_memory.py add-session`;
- `scripts/agent_memory.py scan-files` для автоматического создания базового `file-map.jsonl`;
- pytest-тесты для `scripts/agent_memory.py`;
- root-level `requirements-dev.txt` с dev-зависимостью `pytest>=8,<9`;
- ссылка из `README.md`;
- ручная команда проверки памяти в `README.md`;
- стартовая память о правилах самой памяти: русский язык по умолчанию, ручной коммит пользователем, гибридное подтверждение `decision`/`preference`.

Не входит в MVP:

- embeddings;
- отдельный daemon;
- база данных;
- `index.md`; в MVP используется только `index.jsonl`, потому что он компактнее и тратит меньше токенов при чтении агентом;
- отдельная команда `bootstrap`; для MVP достаточно `search`;
- автоматическое сохранение полного чата;
- автоматические коммиты агентом;
- хранилище вне репозитория;
- персональные данные и секреты.

### Поток Чтения Контекста

1. Пользователь открывает новый чат и пишет запрос.
2. Агент читает `AGENTS.md`.
3. Агент читает `docs/agent-memory/protocol.md`.
4. Агент формирует короткий поисковый запрос из сообщения пользователя.
5. Агент запускает `python scripts/agent_memory.py search "<query>"`.
6. CLI ищет по `index.jsonl`, `file-map.jsonl` и Markdown-записям.
7. Агент читает найденные записи и связанные файлы.
8. Агент продолжает обычное исследование репозитория через `rg`.

### Поток Записи Памяти

1. Агент завершает значимую работу.
2. Агент решает, появился ли долговременный контекст.
3. Агент определяет основной язык текущего чата и пишет человеческие поля памяти на этом языке.
4. Агент определяет тип записи и применяет гибридный режим подтверждения:
   - `session` и `bugfix` агент может добавить сам, если работа уже выполнена и есть проверяемый результат;
   - `decision` и `preference` агент сначала предлагает текст записи пользователю и добавляет ее только после подтверждения;
   - `pattern` агент может добавить сам только если паттерн подтвержден повторным использованием или явно следует из кода.
5. Если запись можно добавить, агент запускает `python scripts/agent_memory.py add-session ...` или вручную пишет запись того же формата.
6. Агент запускает `python scripts/agent_memory.py validate`.
7. Агент оставляет изменения в рабочем дереве и сообщает пользователю, какие файлы нужно проверить перед ручным коммитом.

### Definition Of Ready

Можно начинать реализацию, когда:

- этот план не содержит placeholder-маркеров;
- все пути точные и относятся к текущему репозиторию;
- CLI-команды имеют ожидаемый вывод;
- правила приватности явно описаны;
- validation покрывает JSONL, обязательные поля, дубликаты, пути и secret-like значения;
- есть хотя бы одна seed-запись памяти и одна seed-запись file-map;
- acceptance criteria покрывают и чтение контекста, и запись памяти.

### Definition Of Done

Система памяти считается готовой, когда:

- `python scripts/agent_memory.py validate` завершается с кодом `0`;
- `python scripts/agent_memory.py search "realtime typecheck websocket"` находит seed-запись про realtime typecheck;
- `python scripts/agent_memory.py add-session ...` создает Markdown-запись и строку в `index.jsonl`;
- `python scripts/agent_memory.py scan-files --write` создает или обновляет `docs/agent-memory/file-map.jsonl`;
- `python -m pytest tests/agent_memory/test_agent_memory.py` завершается успешно;
- `AGENTS.md` указывает агентам на протокол и команду поиска;
- `README.md` содержит ссылку на память;
- `.agent-memory-cache/` игнорируется, а `docs/agent-memory/` отслеживается Git;
- `README.md` содержит ручную команду `python scripts/agent_memory.py validate`.

## Правила Памяти

Сохранять нужно только долговременный контекст, а не весь чат.

Язык памяти:

- человеческие поля Markdown-записей (`Summary`, `Context`, `Action History`, `Retrieval Hints`, `Verification`) писать на основном языке чата;
- если чат идет на русском, память писать на русском;
- если чат явно ведется на другом языке, использовать этот язык;
- технические идентификаторы, пути, команды, имена файлов и JSONL-ключи оставлять в принятом для проекта техническом формате;
- если в одной записи нужны русские пояснения и английские технические термины, сохранять оба, но не переводить пути, команды и API-имена.

Режим подтверждения:

- `session`: агент добавляет сам после значимой выполненной работы и показывает diff;
- `bugfix`: агент добавляет сам после найденного root cause и успешной проверки;
- `decision`: агент сначала предлагает формулировку пользователю и ждет подтверждения;
- `preference`: агент сначала предлагает формулировку пользователю и ждет подтверждения;
- `pattern`: агент добавляет сам только после повторного применения или явного подтверждения кодом; если есть сомнение, спрашивает пользователя.

Устаревание памяти:

- устаревшие записи не удалять;
- если запись больше не актуальна, добавить в нее строку `Superseded by: <path-or-id>` рядом с метаданными;
- новая запись должна кратко объяснять, что изменилось;
- поиск может показывать superseded-записи, но агент обязан предпочитать новую запись, если видит `Superseded by:`;
- `search` по умолчанию скрывает superseded-записи;
- для просмотра истории агент использует `python scripts/agent_memory.py search "<query>" --include-superseded`;
- удалять memory-запись можно только если она содержит ошибку, секрет или была создана случайно.

Сохранять:

- пользовательские предпочтения, важные для этого репозитория;
- архитектурные и продуктовые решения;
- неочевидные связи между файлами;
- историю исправления багов, root cause и команды проверки;
- отказанные подходы и причину отказа;
- полезные или медленные команды;
- workflow, затрагивающие несколько частей проекта.

Не сохранять:

- секреты, токены, пароли, ключи, `.env`;
- персональные данные;
- полный текст чатов;
- build output;
- непроверенные догадки;
- временные мысли, которые не будут полезны через неделю.

## Формат Записи Памяти

Формат `id` для всех memory-записей: `YYYY-MM-DD-short-slug`.

Правила:

- дата берется в формате ISO `YYYY-MM-DD`;
- `short-slug` строго ASCII: маленькие латинские буквы `a-z`, цифры `0-9` и дефисы;
- русский текст разрешен в заголовке и содержимом записи, но не в `id` и имени Markdown-файла;
- `id` должен совпадать с именем Markdown-файла без `.md`;
- пример: `2026-05-29-realtime-typecheck`;
- если такой `id` уже существует, CLI автоматически добавляет числовой суффикс: `-2`, `-3` и далее;
- в `Superseded by:` указывать `id` новой записи или путь к ней.

Markdown-запись:

```markdown
# Короткий Заголовок

Date: YYYY-MM-DD
Type: decision | session | pattern | bugfix | preference
Tags: frontend, backend, realtime, tests
Superseded by: optional-newer-memory-id-or-path
Related files:
- apps/frontend/src/example.ts
- apps/backend/app/example.py

## Summary

Краткое описание долговременного факта на основном языке чата.

## Context

Что привело к этой записи и что агент понял. Писать на основном языке чата.

## Action History

- YYYY-MM-DD: короткое действие и результат.

## Retrieval Hints

Использовать эту память, когда пользователь спрашивает про: websocket realtime, layer sync, Vue typecheck.

## Verification

Команды проверки или `Not verified` с причиной. Пояснения писать на основном языке чата.
```

Строка в `index.jsonl`:

```json
{"id":"2026-05-29-realtime-typecheck","type":"bugfix","title":"Realtime frontend typecheck fixes","tags":["frontend","realtime","typescript","tests"],"files":["apps/frontend/src/contracts/realtime.ts","apps/frontend/src/composables/map/useLayerRealtime.test.ts"],"summary":"Fixed strict TypeScript diagnostics around fake websocket lookup and realtime event guards.","path":"docs/agent-memory/sessions/2026-05-29-realtime-typecheck.md","updated":"2026-05-29"}
```

Правила `path` в `index.jsonl`:

- `type` со значениями `decision`, `session`, `pattern`, `bugfix`, `preference` обязан ссылаться на Markdown-файл внутри `docs/agent-memory/`;
- `type` со значениями `project-context` и `planning` может ссылаться на обычные документы проекта, например `README.md` или `docs/requirements/action-plan.md`;
- все `path` должны существовать;
- для memory-записей `id` должен совпадать с именем Markdown-файла без `.md`.

Строка в `file-map.jsonl`:

```json
{"path":"apps/frontend/src/composables/map/useLayerRealtime.ts","area":"frontend","tags":["map","realtime","websocket","layers"],"purpose":"Manages WebSocket subscription for active map layer and reconnect state."}
```

## Структура Файлов

Создать:

```text
AGENTS.md
docs/
  agent-memory/
    README.md
    protocol.md
    index.jsonl
    file-map.jsonl
    decisions/
      .gitkeep
    sessions/
      .gitkeep
    patterns/
      .gitkeep
scripts/
  agent_memory.py
tests/
  agent_memory/
    test_agent_memory.py
requirements-dev.txt
```

Изменить:

```text
README.md
.gitignore
```

Ответственность файлов:

- `AGENTS.md`: стартовый протокол для всех агентов.
- `docs/agent-memory/README.md`: человеческое описание системы памяти.
- `docs/agent-memory/protocol.md`: правила поиска, чтения, записи и приватности.
- `docs/agent-memory/index.jsonl`: компактный индекс записей памяти.
- `docs/agent-memory/index.md`: не создается в MVP; человекочитаемый индекс можно добавить позже как generated view из `index.jsonl`.
- `docs/agent-memory/file-map.jsonl`: карта смысловых областей к файлам.
  `file-map.jsonl` отвечает на вопрос "где искать", а `index.jsonl` отвечает на вопрос "какой контекст уже известен"; поэтому ключевые docs-директории и документы могут присутствовать в file-map даже при наличии planning/project-context записей в index.
- `docs/agent-memory/decisions/`: долгосрочные решения.
- `docs/agent-memory/sessions/`: итоги значимых сессий.
- `docs/agent-memory/patterns/`: повторяемые repo-specific паттерны.
- `scripts/agent_memory.py`: CLI и импортируемый модуль для поиска, проверки и записи.
- `tests/agent_memory/test_agent_memory.py`: pytest-покрытие CLI памяти на временной копии структуры памяти.
- `requirements-dev.txt`: root-level dev-зависимости для agent-memory tooling; в MVP содержит `pytest>=8,<9`.

## План Реализации

### Задача 1: Добавить Точку Входа Для Агентов

**Файлы:**

- Создать: `AGENTS.md`
- Создать: `docs/agent-memory/README.md`
- Создать: `docs/agent-memory/protocol.md`

- [ ] **Шаг 1: Создать `AGENTS.md`**

Содержимое:

```markdown
# Agent Instructions

Before starting work in this repository:

1. Read `docs/agent-memory/protocol.md`.
2. Search memory for the user's request:
   `python scripts/agent_memory.py search "<request summary>"`
3. Read the top relevant memory records and related files before editing.
4. Use `rg` for repository search.
5. After meaningful work, update agent memory when the result contains durable context.

Never store secrets, tokens, passwords, personal data, or full chat transcripts in memory.
```

- [ ] **Шаг 2: Создать `docs/agent-memory/README.md`**

Содержимое:

```markdown
# Agent Memory

This directory stores durable, repository-local memory for Codex agents.

The memory is not a chat transcript. It is a curated set of decisions, session summaries, file ownership hints, test commands, and repo-specific patterns that help future agents recover context quickly.

Start with `protocol.md`.
```

- [ ] **Шаг 3: Создать `docs/agent-memory/protocol.md`**

Содержимое:

```markdown
# Agent Memory Protocol

## Startup

For every new task:

1. Summarize the user request in one short phrase.
2. Run `python scripts/agent_memory.py search "<phrase>"`.
3. Read the most relevant memory records.
4. Read the related files listed by the memory search.
5. Continue normal repository exploration with `rg`.

## Write-Back

Write memory after work when the result includes durable context:

- a decision future agents should preserve;
- a bug root cause and verified fix;
- a new file ownership or workflow pattern;
- a user preference for this repository;
- a command that is slow, flaky, or especially useful.

Preferred command:

`python scripts/agent_memory.py add-session --title "<title>" --summary "<summary>" --tags "tag1,tag2" --files "path/one,path/two" --context "<context>" --action "<action>" --hints "<retrieval hints>" --verification "<verification>"`

## Privacy

Do not store secrets, tokens, passwords, private personal data, raw chat transcripts, or `.env` values.

## Record Format

Use Markdown records with `Date`, `Type`, `Tags`, `Related files`, `Summary`, `Context`, `Action History`, `Retrieval Hints`, and `Verification`.
Update `index.jsonl` when adding a record.
Update `file-map.jsonl` when discovering important file ownership.
```

- [ ] **Шаг 4: Проверить изменения для ручного коммита**

```bash
git status --short
git diff -- AGENTS.md docs/agent-memory/README.md docs/agent-memory/protocol.md
```

Ожидаемый результат: изменения видны в рабочем дереве; коммит делает пользователь вручную после проверки.

### Задача 2: Добавить Индекс Памяти И Подготовить File-Map

**Файлы:**

- Создать: `docs/agent-memory/index.jsonl`
- Создать: `docs/agent-memory/file-map.jsonl` через CLI на Задаче 3
- Создать: `docs/agent-memory/decisions/.gitkeep`
- Создать: `docs/agent-memory/sessions/.gitkeep`
- Создать: `docs/agent-memory/patterns/.gitkeep`

- [ ] **Шаг 1: Создать `index.jsonl`**

Содержимое:

```jsonl
{"id":"project-description","type":"project-context","title":"GeoService project description","tags":["overview","architecture","backend","frontend","gis"],"files":["docs/project-description.md","README.md"],"summary":"GeoService is a GIS MVP with FastAPI/PostGIS backend and Vue/MapLibre frontend.","path":"docs/project-description.md","updated":"2026-05-29"}
{"id":"requirements-action-plan","type":"planning","title":"GeoService action plan","tags":["requirements","sprints","mvp","planning"],"files":["docs/requirements/action-plan.md"],"summary":"High-level sprint plan for closing MVP gaps, including realtime, auth, editing, audit, and analytics work.","path":"docs/requirements/action-plan.md","updated":"2026-05-29"}
```

- [ ] **Шаг 2: Создать временный минимальный `file-map.jsonl`**

До реализации CLI создать минимальный файл, чтобы `validate` и `search` имели стабильный baseline. На Задаче 3 он будет перегенерирован командой `python scripts/agent_memory.py scan-files --write`.

Содержимое:

```jsonl
{"path":"apps/backend/app","area":"backend","tags":["fastapi","sqlalchemy","postgis","api"],"purpose":"Backend application root for API, services, repositories, models, schemas, and tests."}
{"path":"apps/frontend/src","area":"frontend","tags":["vue","typescript","pinia","maplibre"],"purpose":"Frontend source root for map UI, API clients, stores, contracts, and composables."}
{"path":"apps/frontend/src/components/MapView.vue","area":"frontend","tags":["map","maplibre","layers","editing"],"purpose":"Main map component that coordinates layer loading, feature loading, map interaction, and editing UI."}
{"path":"apps/frontend/src/contracts","area":"frontend","tags":["contracts","runtime-validation","api"],"purpose":"Runtime validation and TypeScript contracts for API and realtime payloads."}
{"path":"apps/frontend/src/composables/map","area":"frontend","tags":["map","composables","feature-loading","realtime"],"purpose":"Map-specific Vue composables for loading, realtime sync, map state, and editing behavior."}
{"path":"apps/backend/app/services","area":"backend","tags":["business-logic","features","layers","realtime"],"purpose":"Application services for layer and feature workflows."}
{"path":"apps/backend/app/repositories","area":"backend","tags":["database","sqlalchemy","postgis"],"purpose":"Database access layer."}
{"path":"infra/docker-compose.yml","area":"infra","tags":["docker","postgres","postgis","local-dev"],"purpose":"Local development stack."}
```

- [ ] **Шаг 3: Добавить `.gitkeep`**

```text
docs/agent-memory/decisions/.gitkeep
docs/agent-memory/sessions/.gitkeep
docs/agent-memory/patterns/.gitkeep
```

- [ ] **Шаг 4: Проверить изменения для ручного коммита**

```bash
git status --short
git diff -- docs/agent-memory/index.jsonl docs/agent-memory/file-map.jsonl
```

Ожидаемый результат: изменения видны в рабочем дереве; коммит делает пользователь вручную после проверки.

### Задача 3: Добавить CLI Памяти

**Файлы:**

- Создать: `scripts/agent_memory.py`
- Создать: `tests/agent_memory/test_agent_memory.py`
- Создать: `requirements-dev.txt`

CLI должен быть dependency-free, работать на Python 3.12 и оставаться импортируемым модулем. Логика не должна жить только внутри `argparse`: функции `search`, `validate`, `scan_files`, `add_session` должны быть доступны для прямого вызова из тестов.

- [ ] **Шаг 0A: Зафиксировать импортируемый API**

В `scripts/agent_memory.py` реализовать эти dataclass-модели и функции:

```python
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SearchResult:
    source: str
    score: int
    title: str
    path: str
    summary: str
    superseded: bool = False


@dataclass(frozen=True)
class FileMapEntry:
    path: str
    area: str
    tags: list[str]
    purpose: str


@dataclass(frozen=True)
class SessionInput:
    title: str
    summary: str
    tags: list[str]
    files: list[str]
    context: str
    action: str
    hints: str
    verification: str


def search(
    repo_root: Path,
    query: str,
    *,
    limit: int = 8,
    include_superseded: bool = False,
) -> list[SearchResult]:
    """Search JSONL indexes and Markdown memory records."""


def validate(repo_root: Path) -> None:
    """Raise ValueError with a precise message when memory is invalid."""


def scan_files(repo_root: Path, *, write: bool = False) -> list[FileMapEntry]:
    """Generate compact file-map entries and optionally update file-map.jsonl."""


def add_session(repo_root: Path, session: SessionInput) -> Path:
    """Create a session Markdown record, append index.jsonl, and return the created path."""


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Return process exit code."""
```

Правила:

- функции не читают глобальный `cwd`; все получают `repo_root`;
- `validate` бросает `ValueError`, а `main` преобразует ошибку в понятный stderr и код `1`;
- `main` возвращает код выхода, а `if __name__ == "__main__"` вызывает `raise SystemExit(main())`;
- CLI использует те же функции, что и тесты.

- [ ] **Шаг 0B: Добавить dev-зависимость pytest**

Создать `requirements-dev.txt`:

```text
pytest>=8,<9
```

Команда установки для локальной проверки:

```bash
python -m pip install -r requirements-dev.txt
```

- [ ] **Шаг 1: Добавить pytest-тесты CLI**

Создать `tests/agent_memory/test_agent_memory.py`.

Тесты должны использовать `tmp_path` и изолированную временную структуру репозитория, чтобы не менять реальные `docs/agent-memory/`. Основные проверки должны вызывать импортируемые функции напрямую, а не только subprocess CLI.

Минимальные сценарии:

- `test_validate_accepts_valid_memory`: валидный `index.jsonl`, `file-map.jsonl` и Markdown-запись проходят проверку.
- `test_validate_rejects_missing_index_entry`: Markdown-файл в `sessions/` без строки в `index.jsonl` приводит к ошибке.
- `test_validate_rejects_invalid_field_types`: `tags` строкой вместо массива приводит к ошибке.
- `test_search_hides_superseded_by_default`: запись с `Superseded by:` не показывается обычным `search`.
- `test_search_includes_superseded_with_flag`: та же запись показывается с `--include-superseded`.
- `test_add_session_adds_numeric_suffix_on_id_conflict`: при конфликте `id` создается `...-2.md`.
- `test_scan_files_preserves_manual_existing_path`: `scan-files --write` не затирает ручные `area`, `tags`, `purpose` для уже известного `path`.
- `test_scan_files_skips_generated_and_dependency_paths`: `node_modules`, `.git`, `dist`, `coverage`, `__pycache__` не попадают в `file-map.jsonl`.
- `test_cli_smoke_search_subprocess`: один smoke-тест запускает CLI через subprocess, чтобы проверить wiring `argparse`.

Команда:

```bash
python -m pytest tests/agent_memory/test_agent_memory.py
```

Ожидаемый результат:

```text
9 passed
```

- [ ] **Шаг 2: Реализовать `search`**

Команда:

```bash
python scripts/agent_memory.py search "frontend map realtime"
```

Требования:

- искать по `docs/agent-memory/index.jsonl`;
- искать по `docs/agent-memory/file-map.jsonl`;
- искать по всем `*.md` под `docs/agent-memory/`;
- не искать по содержимому остальных файлов репозитория;
- для поиска по коду и документации вне памяти агент использует `rg`;
- по умолчанию скрывать Markdown-записи, где в метаданных есть `Superseded by:`;
- поддержать флаг `--include-superseded`, который возвращает актуальные и superseded-записи;
- использовать простой lowercase/token matching для русского и английского текста без морфологии, стемминга и внешних зависимостей;
- сортировать результаты по score;
- по умолчанию возвращать максимум 8 результатов;
- поддержать флаг `--limit N` для другого количества результатов;
- по умолчанию печатать краткий человекочитаемый вывод: source, score, title, path, summary;
- JSON output не входит в MVP.

Ожидаемый формат:

```text
[file] score=<number> apps/frontend/src/composables/map
  path: apps/frontend/src/composables/map
  summary: Map-specific Vue composables for loading, realtime sync, map state, and editing behavior.
```

- [ ] **Шаг 3: Реализовать `validate`**

Команда:

```bash
python scripts/agent_memory.py validate
```

Проверки:

- `index.jsonl` валидный JSONL;
- `file-map.jsonl` валидный JSONL;
- строки `index.jsonl` содержат `id`, `type`, `title`, `tags`, `files`, `summary`, `path`, `updated`;
- строки `file-map.jsonl` содержат `path`, `area`, `tags`, `purpose`;
- `id`, `type`, `title`, `summary`, `path`, `updated`, `area`, `purpose` являются непустыми строками;
- `tags` и `files` являются массивами строк;
- `updated` соответствует формату даты `YYYY-MM-DD`;
- `id` в `index.jsonl` уникальны;
- все `path` из `index.jsonl` существуют;
- строки `index.jsonl` с `type` `decision`, `session`, `pattern`, `bugfix`, `preference` ссылаются только на Markdown-файлы внутри `docs/agent-memory/`;
- строки `index.jsonl` с `type` `project-context` и `planning` могут ссылаться на обычные документы проекта;
- каждый `*.md` файл в `docs/agent-memory/decisions/`, `docs/agent-memory/sessions/`, `docs/agent-memory/patterns/` имеет соответствующую строку в `index.jsonl`;
- `id` строки в `index.jsonl` совпадает с именем Markdown-файла без `.md`;
- каждый Markdown-файл памяти содержит секции `## Summary`, `## Context`, `## Action History`, `## Retrieval Hints`, `## Verification`;
- каждый Markdown-файл памяти содержит метаданные `Related files:`;
- список `Related files` в Markdown совпадает с массивом `files` в соответствующей строке `index.jsonl`;
- обязательные секции Markdown-файла памяти не пустые;
- все `path` из `file-map.jsonl` существуют;
- память не содержит очевидные secret-like значения: `password=...`, `secret=...`, `api_key=...`, `access_token=...`.
- secret scanner в MVP проверяет только очевидные паттерны:
  - `password=<value>` или `password: <value>`;
  - `secret=<value>` или `secret: <value>`;
  - `api_key=<value>` или `api_key: <value>`;
  - `access_token=<value>` или `access_token: <value>`;
  - AWS access key pattern `AKIA[0-9A-Z]{16}`.
- secret scanner не должен ругаться на обычные слова `token`, `key`, `secret` без присвоенного значения, чтобы не ломать документацию ложными срабатываниями.

Ожидаемый успешный вывод:

```text
agent memory indexes are valid
```

- [ ] **Шаг 4: Реализовать `add-session`**

Команда:

```bash
python scripts/agent_memory.py add-session --title "<title>" --summary "<summary>" --tags "tag1,tag2" --files "path/one,path/two" --context "<context>" --action "<action>" --hints "<retrieval hints>" --verification "<verification>"
```

Требования:

- создать `docs/agent-memory/sessions/YYYY-MM-DD-<slug>.md`;
- добавить строку в `docs/agent-memory/index.jsonl`;
- сгенерировать `id` в формате `YYYY-MM-DD-short-slug`;
- использовать тот же `id` как имя Markdown-файла без `.md`;
- если такой Markdown-файл уже существует, автоматически выбрать следующий свободный суффикс `-2`, `-3` и далее;
- напечатать созданный путь;
- использовать UTF-8 и LF.

- [ ] **Шаг 5: Реализовать `scan-files`**

Команда:

```bash
python scripts/agent_memory.py scan-files --write
```

Требования:

- автоматически обойти репозиторий от корня;
- создать или обновить `docs/agent-memory/file-map.jsonl`;
- генерировать компактную карту: включать только важные директории и ключевые файлы, а не все файлы подряд;
- сохранять ручные правки для уже известных `path`: если запись с таким `path` уже есть, не затирать ее `area`, `tags` и `purpose`;
- добавлять новые найденные пути;
- удалять из `file-map.jsonl` пути, которых больше нет в репозитории;
- включать важные директории и файлы исходного кода, документации, конфигурации и workflow;
- включать ключевые docs-директории и документы, например `docs/requirements`, `docs/project-description.md`, `docs/codex-agent-long-term-memory-plan.md`;
- предпочитать директории для архитектурных зон (`apps/frontend/src/composables/map`, `apps/backend/app/services`) и отдельные файлы только когда файл является точкой входа, контрактом, конфигурацией или известным большим координатором (`README.md`, `infra/docker-compose.yml`, `apps/frontend/src/components/MapView.vue`);
- не включать `node_modules`, `.git`, `.ruff_cache`, `.agent-memory-cache`, `dist`, `build`, `coverage`, `.vite`, `.next`, `.nuxt`, `.cache`, `__pycache__`, `*.pyc`, бинарные файлы, архивы и generated output;
- для каждого пути вывести поля `path`, `area`, `tags`, `purpose`;
- определять `area` по верхнему уровню пути: `frontend`, `backend`, `infra`, `docs`, `scripts`, `root`;
- формировать `tags` из сегментов пути, имени файла и известных технологий (`vue`, `typescript`, `fastapi`, `sqlalchemy`, `postgis`, `maplibre`, `docker`, `github-actions`);
- формировать `purpose` эвристически, например:
  - `apps/frontend/src/components` -> `Frontend Vue components.`
  - `apps/frontend/src/composables/map` -> `Frontend map composables and MapLibre workflows.`
  - `apps/backend/app/services` -> `Backend application service layer.`
  - `docs/requirements` -> `Product and implementation requirements.`
- сортировать строки по `path`, чтобы diff был стабильным;
- поддержать режим preview без записи:

```bash
python scripts/agent_memory.py scan-files
```

Ожидаемый результат preview: вывести JSONL в stdout, не меняя файлы.

Когда запускать `scan-files --write`:

- при первичном внедрении памяти;
- после структурных изменений в репозитории: новые директории, перенос модулей, удаление важных файлов, появление нового сервиса или крупной зоны ответственности;
- при изменении назначения файла или директории, если старый `purpose` в `file-map.jsonl` стал неверным;
- перед ручным коммитом, если работа меняла структуру файлов.

`scan-files` не запускается автоматически на каждый чат. Не запускать `scan-files --write` после каждой мелкой правки внутри уже известных файлов, чтобы не создавать лишний diff.

- [ ] **Шаг 6: Проверить CLI**

```bash
python -m pip install -r requirements-dev.txt
python scripts/agent_memory.py validate
python scripts/agent_memory.py scan-files --write
python scripts/agent_memory.py validate
python scripts/agent_memory.py search "frontend map realtime"
python scripts/agent_memory.py search "frontend map realtime" --include-superseded
python scripts/agent_memory.py add-session --title "Memory CLI smoke test" --summary "Smoke test for agent memory write-back." --tags "smoke,memory" --files "docs/agent-memory/protocol.md" --context "Testing add-session during implementation." --action "Created a temporary smoke memory record." --hints "memory cli smoke test" --verification "Not verified: temporary smoke record only."
python -m pytest tests/agent_memory/test_agent_memory.py
```

Ожидаемый результат:

- `validate` завершился с кодом `0`;
- `scan-files --write` обновил `docs/agent-memory/file-map.jsonl`;
- `search` вернул минимум один результат;
- `add-session` создал временную запись.
- pytest-тесты завершились успешно.

- [ ] **Шаг 7: Удалить smoke-запись**

Удалить созданный smoke Markdown-файл и соответствующую строку из `index.jsonl`.

Затем снова запустить:

```bash
python scripts/agent_memory.py validate
```

Ожидаемый результат:

```text
agent memory indexes are valid
```

- [ ] **Шаг 8: Проверить изменения для ручного коммита**

```bash
git status --short
git diff -- scripts/agent_memory.py tests/agent_memory/test_agent_memory.py requirements-dev.txt docs/agent-memory/file-map.jsonl
```

Ожидаемый результат: изменения видны в рабочем дереве; коммит делает пользователь вручную после проверки.

### Задача 4: Добавить Первую Реальную Запись Памяти

**Файлы:**

- Создать: `docs/agent-memory/sessions/2026-05-29-realtime-typecheck.md`
- Изменить: `docs/agent-memory/index.jsonl`
- Изменить: `docs/agent-memory/file-map.jsonl`

- [ ] **Шаг 1: Создать session memory**

Содержимое `docs/agent-memory/sessions/2026-05-29-realtime-typecheck.md`:

```markdown
# Realtime Frontend Typecheck Fixes

Date: 2026-05-29
Type: bugfix
Tags: frontend, realtime, typescript, vitest, websocket
Related files:
- apps/frontend/src/contracts/realtime.ts
- apps/frontend/src/contracts/realtime.test.ts
- apps/frontend/src/composables/map/useLayerRealtime.ts
- apps/frontend/src/composables/map/useLayerRealtime.test.ts

## Summary

Frontend realtime typecheck errors were caused by test access to possibly missing fake websocket instances and by a realtime base-field type guard that removed access to variant-specific fields. The fix was to add explicit fake socket lookup helpers in tests and preserve `Record<string, unknown>` in the base realtime guard.

## Context

The TypeScript diagnostics included `socket is possibly undefined`, unsupported `Array.prototype.at`, and missing `feature` / `featureId` properties after type narrowing.

## Action History

- 2026-05-29: Added `getSocketAt()` and `getLastSocket()` helpers in `useLayerRealtime.test.ts`.
- 2026-05-29: Replaced `.at(-1)` usage in realtime tests with `getLastSocket()`.
- 2026-05-29: Updated `hasBaseFeatureRealtimeFields()` return type in `realtime.ts` to keep record access available after narrowing.

## Retrieval Hints

Use this memory when the user asks about realtime websocket tests, strict TypeScript failures, fake websocket instances, frontend realtime contracts, or slow frontend typecheck.

## Verification

- `npm test -- src/contracts/realtime.test.ts src/composables/map/useLayerRealtime.test.ts`: 8 tests passed.
- Scoped temporary `tsc --noEmit` over realtime files passed.
- Full `npm run typecheck` was not rerun because it was too slow for the interactive session.
```

- [ ] **Шаг 2: Добавить запись в `index.jsonl`**

```jsonl
{"id":"2026-05-29-realtime-typecheck","type":"bugfix","title":"Realtime frontend typecheck fixes","tags":["frontend","realtime","typescript","vitest","websocket"],"files":["apps/frontend/src/contracts/realtime.ts","apps/frontend/src/composables/map/useLayerRealtime.test.ts"],"summary":"Fixed strict TypeScript diagnostics around fake websocket lookup and realtime event guards.","path":"docs/agent-memory/sessions/2026-05-29-realtime-typecheck.md","updated":"2026-05-29"}
```

- [ ] **Шаг 3: Добавить записи в `file-map.jsonl`**

```jsonl
{"path":"apps/frontend/src/contracts/realtime.ts","area":"frontend","tags":["realtime","contracts","websocket","runtime-validation"],"purpose":"Runtime parser and type guards for layer realtime WebSocket events."}
{"path":"apps/frontend/src/composables/map/useLayerRealtime.test.ts","area":"frontend","tags":["realtime","tests","websocket","vitest"],"purpose":"Vitest coverage for layer realtime connection, reconnect, auth close, and event routing behavior."}
```

- [ ] **Шаг 4: Проверить retrieval**

```bash
python scripts/agent_memory.py search "realtime typecheck websocket"
```

Ожидаемый результат: вывод содержит `Realtime frontend typecheck fixes`.

- [ ] **Шаг 5: Проверить изменения для ручного коммита**

```bash
git status --short
git diff -- docs/agent-memory/sessions/2026-05-29-realtime-typecheck.md docs/agent-memory/index.jsonl docs/agent-memory/file-map.jsonl
```

Ожидаемый результат: изменения видны в рабочем дереве; коммит делает пользователь вручную после проверки.

### Задача 5: Добавить Память О Правилах Ведения Памяти

**Файлы:**

- Создать: `docs/agent-memory/decisions/2026-05-29-agent-memory-operating-rules.md`
- Изменить: `docs/agent-memory/index.jsonl`

- [ ] **Шаг 1: Создать decision memory**

Содержимое `docs/agent-memory/decisions/2026-05-29-agent-memory-operating-rules.md`:

```markdown
# Правила Ведения Памяти Codex-Агентов

Date: 2026-05-29
Type: decision
Tags: agent-memory, codex, workflow, preferences, russian
Related files:
- docs/codex-agent-long-term-memory-plan.md
- docs/agent-memory/protocol.md
- AGENTS.md

## Summary

Память Codex-агентов в этом репозитории ведется на основном языке чата, чаще всего на русском, чтобы пользователь мог читать записи вручную. Агент не делает коммиты сам: он оставляет изменения в рабочем дереве и показывает diff/status, а пользователь коммитит после проверки. Для записи памяти используется гибридный режим: `session` и `bugfix` агент может добавить сам после проверенной работы, а `decision` и `preference` добавляет только после подтверждения пользователя.

## Context

Эти правила были уточнены во время планирования долговременной памяти. Пользователь выбрал гибридный режим подтверждения и явно попросил убрать автоматические коммиты из плана.

## Action History

- 2026-05-29: Зафиксировано правило писать человеческие поля памяти на основном языке чата.
- 2026-05-29: Зафиксировано правило не делать коммиты агентом.
- 2026-05-29: Зафиксирован гибридный режим подтверждения записей памяти.

## Retrieval Hints

Использовать эту память, когда пользователь спрашивает про правила памяти, язык записей, подтверждение decisions/preferences, ручные коммиты или workflow Codex-агентов.

## Verification

Проверяется ревью плана и командой `python scripts/agent_memory.py validate` после реализации CLI.
```

- [ ] **Шаг 2: Добавить запись в `index.jsonl`**

```jsonl
{"id":"2026-05-29-agent-memory-operating-rules","type":"decision","title":"Правила ведения памяти Codex-агентов","tags":["agent-memory","codex","workflow","preferences","russian"],"files":["docs/codex-agent-long-term-memory-plan.md","docs/agent-memory/protocol.md","AGENTS.md"],"summary":"Память ведется на основном языке чата, агент не коммитит сам, а decisions/preferences добавляются только после подтверждения пользователя.","path":"docs/agent-memory/decisions/2026-05-29-agent-memory-operating-rules.md","updated":"2026-05-29"}
```

- [ ] **Шаг 3: Проверить retrieval**

```bash
python scripts/agent_memory.py search "правила памяти русский коммит подтверждение"
```

Ожидаемый результат: вывод содержит `Правила ведения памяти Codex-агентов`.

- [ ] **Шаг 4: Проверить изменения для ручного коммита**

```bash
git status --short
git diff -- docs/agent-memory/decisions/2026-05-29-agent-memory-operating-rules.md docs/agent-memory/index.jsonl
```

Ожидаемый результат: изменения видны в рабочем дереве; коммит делает пользователь вручную после проверки.

### Задача 6: Подключить Память К Workflow Репозитория

**Файлы:**

- Изменить: `README.md`
- Изменить: `.gitignore`

- [ ] **Шаг 1: Добавить ссылку в README**

В раздел документации добавить:

```markdown
- [agent-memory](C:/Repositories/geoservice/docs/agent-memory/README.md)
```

- [ ] **Шаг 2: Игнорировать только локальный cache**

В `.gitignore` добавить:

```gitignore
.agent-memory-cache/
```

Не добавлять `docs/agent-memory/` в `.gitignore`.

- [ ] **Шаг 3: Добавить команду проверки в README**

Добавить:

````markdown
Agent memory validation:

```bash
python -m pip install -r requirements-dev.txt
python scripts/agent_memory.py validate
```
````

- [ ] **Шаг 4: Проверить изменения для ручного коммита**

```bash
git status --short
git diff -- README.md .gitignore
```

Ожидаемый результат: изменения видны в рабочем дереве; коммит делает пользователь вручную после проверки.

## Acceptance Criteria

- Новый чат может обнаружить workflow памяти через `AGENTS.md`.
- `python scripts/agent_memory.py search "<request>"` ищет по JSONL и Markdown, затем возвращает релевантные записи и файлы.
- `search` ищет только по памяти; поиск по коду и остальной документации выполняется через `rg`.
- `search` скрывает superseded-записи по умолчанию и показывает их только с `--include-superseded`.
- `search` по умолчанию возвращает максимум 8 результатов и поддерживает `--limit N`.
- `python scripts/agent_memory.py add-session ...` создает session Markdown и индексную строку.
- Все memory `id` используют формат `YYYY-MM-DD-short-slug` и совпадают с именем Markdown-файла без `.md`.
- При конфликте `id` CLI автоматически выбирает следующий свободный суффикс `-2`, `-3` и далее.
- `python scripts/agent_memory.py scan-files --write` автоматически создает или обновляет стабильный `docs/agent-memory/file-map.jsonl` без мусорных и generated путей.
- `scan-files --write` сохраняет ручные правки существующих записей по `path`, добавляет новые пути и удаляет исчезнувшие.
- `file-map.jsonl` включает ключевые docs-директории и документы; это не считается дублем `index.jsonl`, потому что у них разные роли.
- `python scripts/agent_memory.py validate` ловит битый JSONL, дубликаты id, отсутствующие поля, неверные типы полей, неверный формат `updated`, сломанные пути и очевидные secret-like значения.
- `python -m pytest tests/agent_memory/test_agent_memory.py` покрывает validate/search/add-session/scan-files и завершается успешно.
- `scripts/agent_memory.py` импортируется в тестах; основная логика покрыта прямыми вызовами функций, а CLI wiring покрыт subprocess smoke-тестом.
- `requirements-dev.txt` содержит `pytest>=8,<9` для воспроизводимого запуска CLI-тестов.
- `validate` падает, если Markdown-запись в `decisions/`, `sessions/` или `patterns/` отсутствует в `index.jsonl`.
- `validate` падает, если Markdown-запись не содержит обязательные секции или оставляет их пустыми.
- `validate` падает, если `Related files` в Markdown не совпадает с `files` в `index.jsonl`.
- `index.jsonl` разрешает ссылки на обычные docs только для `project-context` и `planning`; настоящие memory-записи обязаны лежать под `docs/agent-memory/`.
- В MVP нет `index.md`; машинный `index.jsonl` является единственным индексом, чтобы экономить токены.
- Долговременные записи находятся в `docs/agent-memory/` и ревьюятся через Git.
- Устаревшие записи не удаляются, а помечаются `Superseded by:`.
- Markdown-записи памяти написаны на основном языке соответствующего чата, обычно на русском.
- Правила явно говорят, что сохранять можно, а что нельзя.
- Первая реальная запись памяти ищется по `realtime`, `typecheck`, `websocket`.
- Нет внешнего сервиса, API-ключа, базы данных или package install.
- В MVP проверка памяти выполняется вручную командой из `README.md`; CI-проверка остается будущим улучшением.
- В MVP нет отдельной команды `bootstrap`; старт нового чата покрывается командой `search`.

## Риски И Смягчения

- **Риск:** агенты начнут сохранять слишком много шума.
  **Смягчение:** protocol запрещает полные чаты и требует только долговременные summaries.

- **Риск:** память устареет.
  **Смягчение:** у каждой записи есть `updated`; при изменении связанных файлов агент обновляет или supersede-ит запись.

- **Риск:** keyword search пропустит важный контекст.
  **Смягчение:** поддерживать `tags`, `Retrieval Hints`, `index.jsonl` и `file-map.jsonl`; embeddings добавить позже.

- **Риск:** секрет попадет в Git.
  **Смягчение:** protocol запрещает секреты, а `validate` сканирует secret-like паттерны.

- **Риск:** агент пропустит memory lookup.
  **Смягчение:** `AGENTS.md` делает memory lookup первым шагом.

## Будущие Улучшения

- `python scripts/agent_memory.py related-files "<query>"` для вывода только файлов.
- флаг `--json` для машинного вывода результатов поиска.
- generated `docs/agent-memory/index.md` для ручного чтения пользователем, если позже понадобится человекочитаемый обзор.
- `python scripts/agent_memory.py bootstrap "<query>"` для вывода top memory, related files и рекомендуемых `rg` запросов.
- улучшенный поиск со стеммингом, морфологией или embeddings, если простого token matching станет недостаточно.
- `python scripts/agent_memory.py add-decision` и `add-pattern`.
- Более богатый secret scanner с allowlist для ложных срабатываний.
- Локальный embedding cache в `.agent-memory-cache/`, без добавления generated vectors в Git.
- CI job для `python scripts/agent_memory.py validate`.
- Pre-commit hook для `python scripts/agent_memory.py validate`.

## Self-Review

- Покрытие требований: план покрывает сохранение ключевых моментов чата, историю действий, новый стартовый retrieval, быстрый поиск файлов, правила приватности и полный implementation workflow.
- Placeholder scan: placeholder-маркеров и неопределенных шагов нет.
- Согласованность путей: все пути находятся внутри текущего репозитория.
- Готовность к реализации: реализацию можно начинать с Task 1 и выполнять задачи последовательно.
