# SDD ledger — plan: docs/sprint_2/2026-10-10-day-5-repository-context-plan.md

## Исполнение

Последовательная реализация, начало 10 октября 2026. BASE: `0c10e4e`, branch `first-edit-save`.

Ruling: используется существующий feature checkout с согласованными unstaged документами — developer instructions предпочитают подходящий текущий checkout; новая копия не нужна — цена: изменения разделяют рабочее дерево, чужие правки необходимо сохранять.

Ruling: ledger/brief ведутся в docs/sprint_2 средствами PowerShell вместо POSIX sdd scripts и commits; DB lifecycle выполнен эквивалентными Compose-командами infra/db-tests.cmd — Windows и запрет staging/commit/push — цена: итоговый unstaged diff проверяется целиком, ledger сохраняется до ручного review; cleanup тестового проекта выполняется явно. При завершении ветка сохраняется без merge/push-меню согласно AGENTS.md.

## Pre-flight

- 1 → 2: context/raw rows и provenance согласованы; decoding откладывается до eligibility.
- 2 → 3: PreparedGeometryHandle сохраняет rejection_code для будущего fingerprint; current-dependent guards выполняются на validation.
- 3 → 4: write принимает только выданный ValidatedGeometryChange; один context/generation, exact EWKB.
- 4 → 5: write не увеличивает revision; compatibility test делает это test-only orchestration.
- 1–5 → 6: M1 подтверждается новым isolated DB suite и unit regression; D5-Q1 остаётся временным.

## Задачи

Task 2: targeted GREEN — 22 passed (context/protocol/validation + canonicalization/structure). Task 3: RED отсутствующего inspect_spatial → GREEN 14 passed (spatial + validation). Task 4: RED write_current отсутствует — 3 failed, 1 existing protocol test passed.

Проверки: baseline unit 151 passed; initial protocol RED (missing repository), context/protocol GREEN 4 passed. Validation RED: отсутствует validation module.

Ruling: scope tracker регистрируется один раз на session и очищает handles при завершении transaction; listeners живут вместе с session — удаление listener из собственного callback небезопасно, а повторная регистрация создаёт накопление — цена: два небольших session-local callbacks до освобождения session.

- Task 1: complete — root lock/context/protocol; U protocol + D context: 4 passed, итоговая DB regression: 205 passed.
- Task 2: complete — исходные инварианты и preparation; D validation/context + U protocol/canonicalization/structure: 22 passed; итоговая unit regression: 506 passed.
- Task 3: complete — spatial validation; D spatial/validation: 14 passed, затем расширены fixtures вогнутой AOI, D5-Q1 after rounding и current; итоговая DB regression: 205 passed.
- Task 4: complete — mutation; RED missing write_current → GREEN 4 passed, затем расширены signed-zero и stale sibling context cases. Все новые tests вместе с protocol: 35 passed.
- Task 5: complete — concurrency/history; новые primitives уже GREEN без искусственной поломки, как разрешено планом. D concurrency + existing event constraints/concurrency: 42 passed. Итоговая DB regression: 205 passed.
- Task 6: complete — fresh full unit 506 passed/204 expected DB skips; fresh full DB 205 passed/0 skipped (повтор после SQL formatting: 205 passed); M1/review/report завершены.

## Команды итоговой проверки

Из корня: `docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml`.

- `run --rm --no-deps -e RUN_DB_TESTS=0 backend_db_tests python -m pytest --tb=short` → 506 passed, 204 skipped, 2 dependency warnings.
- `down -v --remove-orphans`, `up --build --abort-on-container-exit --exit-code-from backend_db_tests`, `down -v --remove-orphans` → 205 passed, 0 skipped; cleanup exit 0. Повтор с `--attach backend_db_tests` после SQL formatting также exit 0, 205 passed.
- `run --rm --no-deps -e RUN_DB_TESTS=0 backend_db_tests python -m black --check .` → 286 файлов без изменений.
- `run --rm --no-deps -e RUN_DB_TESTS=0 backend_db_tests python -m ruff check .` → All checks passed после удаления двух unused test imports.

## Итоговое review

Независимый reviewer `gpt-6-astra`, свежий контекст, read-only, просмотрел новые untracked code/tests, spec/plan и rulings. Critical/Important/Minor замечаний нет. Проверены все пять review focus. Reviewer не дублировал тестовый прогон; результаты получены исполнителем. После review менялось только форматирование SQL/параметров и удалены unused imports, поведение не менялось.

Final: Ruling: writers в обход root-lock protocol — остаются вне гарантии по принятому scope; штатные Save обязаны брать root lock — цена: обходящий writer может нарушить проверенный context.

Final: Ruling: production access/lifecycle/token/replay и registry/history orchestration — остаются в Днях 6–7, совместимость с history проверена test-only — цена: текущая boundary ещё не является публичным Save workflow.

Final: Ruling: окончательная допустимость нулевых сегментов — оставлено принятое временное D5-Q1, GEOMETRY_INVALID после canonicalization — цена: требуется доменное уточнение, возможно изменение правила и tests.

Отложенных minor findings нет. Git staging/commit/push не выполнялись. Новая durable knowledge сохранена в Code_wiki через repository-change; отдельная agent memory не нужна, поскольку дублировала бы spec/wiki.

Финальная передача: Black/Ruff повторно прошли после SQL formatting; cleanup временного DB project exit 0. `git diff --check` и дополнительная проверка 24 changed/new files на whitespace/conflict markers и sprint links прошли. Wiki lint: только 37 известных missing_frontmatter в RAW, источники не изменялись.
