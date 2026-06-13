---
name: source-command-audit-memory
description: Ручная read-only процедура /audit-memory для поиска шума, дублей, устаревших ссылок и кандидатов на очистку agent memory.
---

# /audit-memory

`/audit-memory` анализирует `docs/agent-memory/` и legacy записи
`repository_change_ingest.md`. Команда формирует кандидатов, но не изменяет и
не удаляет файлы.

## Шаг 1. Запустить Детерминированный Аудит

```powershell
python scripts/audit-memory.py --root . --format markdown
```

Если системный `python` недоступен, использовать bundled Python текущей среды.

## Шаг 2. Проверить Findings

Для каждого кандидата проверить:

- есть ли уникальное знание, которого нет в design, plan, code или wiki;
- существует ли указанный canonical source;
- актуальны ли decision, pattern или bug root cause;
- не является ли session-запись только результатом sync, ingest, lint,
  planning или завершения задачи.

## Шаг 3. Подготовить Отчёт Пользователю

Сгруппировать кандидатов по рекомендациям:

- `keep`;
- `merge`;
- `replace-reference`;
- `delete`;
- `review`.

Для `merge`, `replace-reference` и `delete` назвать конкретные paths и причины.

## Шаг 4. Остановиться До Подтверждения

Не удалять, не перемещать и не объединять файлы без отдельного подтверждения
пользователя. После подтверждения выполнить отдельную implementation-задачу,
очистить `file-map.md` и проверить ссылки.

## Ограничения

- Не изменять файлы как часть аудита.
- Не считать возраст достаточным основанием для удаления decision, pattern или
  bugfix.
- Не использовать `Superseded by` вместо удаления явного шума.
- Не сохранять каждый audit report как новую memory/session запись.
