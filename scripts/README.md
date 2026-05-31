# Scripts

Скрипты для project knowledge pipeline.

## `lint-wiki.py`

Проверяет Markdown wiki: frontmatter, wikilinks, пустые файлы, устаревшие ноды и обязательные `source`.

```powershell
python scripts/lint-wiki.py --root .
```

## `check-memory-needed.py`

Предупреждает, если меняются durable plan/spec/rule files без изменения `docs/agent-memory/`.

```powershell
python scripts/check-memory-needed.py --check
```
