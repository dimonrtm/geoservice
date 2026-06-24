# Scripts

Скрипты для project knowledge pipeline.

## `lint-wiki.py`

Проверяет корни `Wiki/`, `DDD_Wiki/`, `Vision_wiki/`, `Code_wiki`, `RAW_inputs/`, `memory/`, `Общие_принципы/` и `docs/knowledge-pipeline/`. Для доменных узлов дополнительно проверяет `confidence`, `related` и обязательные DDD-секции.

Проверяет Markdown wiki: frontmatter, wikilinks, пустые файлы, устаревшие ноды и обязательные `source`.

```powershell
python scripts/lint-wiki.py --root .
```

## `check-memory-needed.py`

Предупреждает, если меняются operating rules памяти или knowledge pipeline без изменения `docs/agent-memory/`. Обычные plan/spec сами по себе не требуют memory-записи.

```powershell
python scripts/check-memory-needed.py --check
```

## `audit-memory.py`

Read-only аудит agent memory: broken references, noisy sessions, exact duplicate summaries, age candidates, budgets и legacy repository-change entries.

```powershell
python scripts/audit-memory.py --root . --format markdown
```

Findings являются отчётом для review и не приводят к автоматическому удалению.
