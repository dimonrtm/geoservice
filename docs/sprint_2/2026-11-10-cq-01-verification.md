# CQ-01 — журнал реализации и проверки

План: [2026-11-10-cq-01-plan.md](2026-11-10-cq-01-plan.md).
Дизайн принят пользователем. Статус: реализация и проверка завершены 2026-11-10, независимое ревью без замечаний. Изменения оставлены unstaged.

## Решения исполнения

- Работа продолжается в существующем checkout `first-edit-save`: пользователь поручил выполнение в текущем чате, новый worktree не запрашивал. До реализации рабочее дерево содержит только три документа CQ-01. Git add/commit/push запрещены.
- Журнал и результаты хранятся здесь, в запрошенной пользователем папке docs/sprint_2. Shell helpers навыка, рассчитанные на commit ranges, заменены прямыми запусками тестов и проверкой unstaged diff: коммитов в этой работе не будет.
- Окружение: существующий image `ar03-check-1108-b102-backend_db_tests:latest`; исходники `/app` подключены read-only, сеть отключена, PYTHONDONTWRITEBYTECODE=1, pytest без cacheprovider. Доступ к Docker разрешён через escalation после sandbox access denied.
- Предварительная сверка интерфейсов: задача 1 вводит InvalidBboxError и handler; задача 2 меняет путь registry; задача 3 проверяет итоговую независимость domain_services после обеих задач. Конфликтов интерфейсов нет.

## Проверки

Исходный полный backend-прогон: 742 passed, 335 skipped, 2 warnings, 36.21 s.

Задача 1 завершена: RED — два ImportError отсутствующего InvalidBboxError; GREEN — 53 passed, 2 warnings. Команда pytest: `utility_service/domain_services/tests/test_bbox.py utility_service/web_api/tests/test_layers_api.py utility_service/web_api/tests/test_exception_handlers.py -p no:cacheprovider`.

Уточнение плана: две однотипные handler-проверки объединены параметризацией `test_specific_validation_errors_preserve_legacy_422`; проверяются оба типа, точные сообщения и correlation header.

Задача 2 завершена: RED — ModuleNotFoundError нового пути registry; GREEN — 62 passed, 2 warnings. Команда pytest: `utility_service/infrastructure/tests/test_feature_registry.py utility_service/use_cases/tests/test_feature_service.py utility_service/web_api/tests/test_layers_api.py tests/test_architecture_boundaries.py -p no:cacheprovider`.

Задача 3 завершена. RED: 22 failed, 3 passed — новые проверки требовали отсутствующих параметров управления областью анализа и разрешением относительных импортов. GREEN: 25 passed; команда `python -m pytest tests/test_architecture_boundaries.py -p no:cacheprovider`.

## Итоговые результаты

Полный backend: **798 passed, 335 skipped, 2 warnings**, 32.02 s. Команда в PowerShell из корня репозитория:

```powershell
docker run --rm --network none --mount 'type=bind,source=C:\Repositories\geoservice\apps\backend,target=/app,readonly' --workdir /app -e PYTHONDONTWRITEBYTECODE=1 --entrypoint python ar03-check-1108-b102-backend_db_tests:latest -m pytest -p no:cacheprovider
```

Добавлено 56 проверок. Пропуски совпадают с baseline: DB-dependent и environment-dependent проверки этого запуска не выполнялись. Это не PostGIS-интеграция и не production smoke. Два предупреждения существовали до изменения: deprecated anyio BlockingPortal alias в Starlette и deprecated crypt в passlib.

Ruff (`python -m ruff check --no-cache`) и Black (`python -m black --check`) прошли для девяти Python-файлов, перечисленных в задачах плана; оба exit 0. Black при форматировании изменил четыре тестовых файла, для этого один запуск использовал write mount; все тестовые и проверочные запуски использовали read-only mount и отключённую сеть.

`git diff --check` прошёл. Все новые/изменённые текстовые файлы проверены на UTF-8 и LF, включая untracked. Старых импортов `domain_services.feature_registry` в Python-коде нет. Перенесённый registry побайтно совпадает с исходным. Изменение LayerRepository ограничено импортом; SQL, модели, миграции, FeatureService и frontend не затронуты. Production domain_services импортирует только стандартную библиотеку и свои модули; транзитивного обхода через внешние helpers не найдено.

Независимый рецензент проверил весь unstaged diff и новые файлы относительно исходного HEAD `1daa76774451a5323bd000b39c4da8f6205a90ed`. Critical/Important/Minor замечаний нет. Сам рецензент тесты повторно не запускал; итоговые прогоны выполнены координатором.

## Документация и ограничения

CQ-01 закрыта в реестре; CQ-02/CQ-03 остаются открытыми. Repository-change ingest дополнил существующую ноду `Code_wiki/архитектура/backend.md`: владение registry, ошибка bbox и граница статической проверки. Доменная модель и live state не менялись; отдельная agent memory не создавалась, поскольку дизайн и wiki сохраняют причины решения.

Wiki lint: `python scripts/lint-wiki.py --root .` в том же image с read-only mount корня репозитория — exit 1, **37 известных missing_frontmatter в RAW_inputs**, новых ошибок нет. RAW не изменялись.

Git add/commit/push не выполнялись. По правилу репозитория результат передаётся пользователю для ревью и самостоятельного коммита; действия интеграции из finishing-a-development-branch не применяются.
