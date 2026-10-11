# Журнал исполнения — plan: docs/sprint_2/2026-10-11-day-6-save-plan.md

Спецификация принята; пользователь разрешил реализацию. BASE: `2f020a4`. Работа последовательная, код остаётся unstaged.

## Подготовка и решения

- Ruling: использовать текущий checkout `first-edit-save` с согласованными untracked документами — пригодная feature branch, приложенных worktrees нет; developer instructions предпочитают подходящий checkout. Не создавать дополнительный worktree и не переносить документы.
- Ruling: журнал ведётся в docs/sprint_2 по явному требованию пользователя к артефактам; shell wrappers навыка, завязанные на commits и scratch workspace, заменяются явными проверками и записями здесь. Git add/commit/push запрещены.
- Pre-flight 1→2: command/revision signatures совместимы с Save; root переживает consume, context handles — нет.
- Pre-flight 2→3: SaveGeometryResult payload должен копироваться при replay; immutable dataclass не защищает вложенный dict.
- Pre-flight 1–3→4–5: реальные fixtures должны создавать User, существующая geometry fixture даёт только UUID actor.
- Pre-flight 4–5→6: DB tests только geo_test через isolation guard; mocks не доказывают locks/commit.
- Docker socket был недоступен в sandbox; build выполнен с разрешённой эскалацией, exit 0.

## Задачи

- Task 1: базовый SQL GREEN — 4 DB tests; RED: отсутствующие reserve/increment, GREEN: 4 passed. Проверки provenance включены в DB test вместо отдельного mock-only файла.
- Task 2: service GREEN — 5 тестов до реализации падали на отсутствующем save_geometry; после реализации successful/no-op/revert/stale/commit-failure проходят.
- Task 3: service GREEN — 16 RED до реализации; общий прогон Save/replay/Open: 35 passed.
- Task 4: completed — 14 DB tests атомарности и дополнительных граничных сценариев.
- Task 5: completed — 6 конкурентных DB cases.
- Task 6: completed — полная регрессия, независимое review, отчёт и обновление документов.

## Проверки и уточнения исполнения

- Baseline non-DB: 506 passed, 204 skipped (DB), 2 существующих deprecation warnings.
- Ruling: RED сценарии задач 2 и 3 подготовлены перед общей реализацией Save — replay является частью одного transaction protocol; task-level приёмка сохраняется отдельными suites.
- Ruling: имена и группировка некоторых tests объединены вокруг наблюдаемого сценария; assertions плана сохранены, провенанс проверяется реальной session.
- Task 4 initial GREEN: 7 DB tests; Task 5 GREEN: 6 concurrent DB tests. Дополнительно закрываются legacy rejected rows, baseline вне grid и missing context.
- Initial full regression: 527 passed / 221 DB skipped в non-DB; 222 passed в fresh DB; Ruff и Black GREEN. Первый Black с mounted Windows workspace был остановлен test-project cleanup; повтор в image: 296 files unchanged, exit 0.
- Независимый reviewer нашёл P2: retained ORM User при expire_on_commit=False сохраняет отозванные role/is_active между transactions.
- Review RED: 4 real DB cases (inactive/reviewer × fresh/replay) — DID NOT RAISE WorkOrderApiError. Root cause: UserRepository.get_by_id выполняет SELECT, но не перезаполняет identity-map объект.
- Ruling: добавить populate_existing=True в UserRepository.get_by_id — это источник данных проверки доступа Save; существующие callers получают актуальный User при явном чтении. Public signature не меняется. Цена расширения: регрессия всех callers проверяется полным backend suite.
- Review GREEN после rebuild: 14 passed в atomicity suite, включая все 4 прежних RED. Повторный независимый review подтвердил закрытие P2; блокирующих замечаний нет.
- Final regression после последнего изменения кода: non-DB 531 passed / 228 skipped / 2 warnings; fresh DB 229 passed / 2 warnings. Оба exit 0. Предупреждения существующие: passlib crypt и Starlette BlockingPortal.
- Final Black: 296 files unchanged, exit 0. Ruff: All checks passed, exit 0. git diff --check успешен.
- Ruling finishing-a-development-branch: сохранить текущую branch/checkout и unstaged изменения согласно AGENTS.md; меню merge/push неприменимо к явно заданному пользователем порядку Git review.
- Отчёт: [реализация Дня 6](2026-10-11-day-6-save-implementation-report.md). Новые memory entries и repository-change ingest не нужны для дублирования сохранённых решений.
