# День 13: план реализации сквозной автоматической проверки

> **Для исполнителя:** применять `superpowers:executing-plans` при самостоятельном исполнении либо `superpowers:subagent-driven-development` при выбранном пользователем исполнении через агентов. Задачи выполнять последовательно; staging, commit и push запрещены правилами репозитория.

**Цель:** включить в CI воспроизводимый live API сценарий Save → restart → readback/retry/Revert с отрицательными исходами и доказательством неизменности baseline geometry L-003.

**Архитектура:** расширить существующий smoke двумя фазами; HTTP выполняет сценарные mutations, независимые read-only SQL snapshots проверяют persistence. CI хранит фазовый JSON вне backend, перезапускает штатный сервис и собирает evidence до очистки.

**Стек:** Python 3.12, pytest, urllib, SQLAlchemy/asyncpg из существующего backend, PostgreSQL/PostGIS, Docker Compose, GitHub Actions. Новые dependencies не нужны.

**Спецификация:** [принятый дизайн](2026-10-25-day-13-smoke-design.md). Статус плана: выполнен; фактические проверки и ограничения — в отчёте реализации. Remote GitHub Actions ожидает действий пользователя.

## Общие ограничения

- Fresh database на каждый полный прогон; та же БД между фазами и при restart API.
- Браузерный M4 только локально; четыре отрицательных исхода по одному разу.
- Проверять геометрию только baseline L-003; не расширять предмет проверки до всех baseline rows.
- Только HTTP меняет данные сценария. SQL-наблюдатель открывает read-only транзакцию.
- Не сбрасывать историю, команды или revision; не исправлять fixture скрытой mutation.
- Существующий smoke без параметров сохраняет прежний контракт.
- Данные для Revert берутся из baselineGeometry HTTP readback.
- Не редактировать продуктовый backend/frontend, миграции и доменные правила в рамках тестовой задачи. Обнаруженный продуктовый дефект описать отдельно.
- Документация — русский, UTF-8/LF; команды, пути и identifiers без перевода. `.cmd` — CRLF.
- Запрет `git add`, `git commit`, `git push` распространяется на все задачи плана.

## Особое внимание при review

1. Чужой, устаревший или незавершённый state-файл: отказ до PUT, не случайный replay чужой команды — задача 1.
2. HTTP replay верен, но registry/history повреждены: независимый снимок должен провалить smoke — задачи 2–3.
3. Координаты округлились в no-op или отрицательный запрос упёрся в другой guard: проверять canonical diff и точный code — задачи 2–3.
4. Restart ещё не начался, а прежний health уже healthy: требовать смену StartedAt до readiness — задача 4.
5. Ошибка посреди сценария или cleanup: evidence не объявляет success, диагностика собрана до удаления, исходная ошибка не теряется — задачи 1 и 4.

## Карта файлов

| Файл | Ответственность |
| --- | --- |
| `apps/backend/tests/smoke/full_path_workspace_smoke.py` | Прежний smoke, HTTP helpers, CLI dispatch новых фаз |
| `apps/backend/tests/smoke/save_geometry_smoke.py` — новый | Фазовый state, assertions и последовательность Save/verify/retry/revert |
| `apps/backend/tests/smoke/save_geometry_observer.py` — новый | Read-only SQL snapshot с проверкой identity |
| `apps/backend/tests/smoke/test_full_path_workspace_smoke.py` | Совместимость прежнего пути и HTTP error decoding |
| `apps/backend/tests/smoke/test_save_geometry_smoke.py` — новый | Тесты фаз на управляемом HTTP transport и observer |
| `apps/backend/tests/integration_tests/test_save_geometry_smoke_observer.py` — новый | Доказательство корректности SQL snapshot на disposable БД |
| `.github/workflows/ci.yml` | Save, export state, restart, verify, evidence upload и cleanup |
| `docs/sprint_2/2026-10-25-day-13-smoke-runbook.md` — новый | Команды запуска, preconditions, диагностика и безопасная изоляция |
| `docs/sprint_2/2026-10-25-day-13-smoke-implementation-report.md` — после исполнения | Фактические результаты и ограничения |

## Задача 1. Фазовое состояние и ожидаемые HTTP ошибки

**Файлы:** `full_path_workspace_smoke.py`, `test_full_path_workspace_smoke.py`, новые `save_geometry_smoke.py` и `test_save_geometry_smoke.py`.

**Интерфейсы:**

- `request_json_response(config, method, path, *, token=None, payload=None, opener=urlopen) -> tuple[int, dict[str, Any]]`: декодирует JSON и для HTTPError; transport/JSON failures остаются SmokeFailure. Старый `request_json` оборачивает его и сохраняет отказ на non-2xx.
- `load_phase_state(path: Path, *, run_id: str) -> dict[str, Any]`: строгая проверка schemaVersion=1, runId, status=save-complete, UUID identities, полной исходной команды, response и snapshots.
- `write_phase_state(path: Path, state: dict[str, Any]) -> None`: атомарная замена через временный файл в той же директории, UTF-8/LF.
- CLI: `--phase save|verify-retry-revert`, `--run-id UUID`, `--state-file PATH`, `--evidence-file PATH`; при отсутствии `--phase` работает прежний smoke. Фазовый режим требует все остальные параметры. Повтор save с существующим state и verify с завершённым state запрещены.

- [x] Добавить tests: прежний успешный путь; JSON при 409/422; malformed JSON и transport error; unknown schema, неверный runId, отсутствующая команда, completed state, повтор save. Для invalid state проверять `put_calls == []`.
- [x] Запустить `pytest tests/smoke/test_full_path_workspace_smoke.py tests/smoke/test_save_geometry_smoke.py`; новые проверки должны выявить отсутствие поведения.
- [x] Реализовать transport и state helpers; новые фазы импортировать из CLI лениво, сохранив запуск скрипта по прежнему пути. State model не должен включать auth/credentials.
- [x] Повторить targeted tests: exit 0. Проверить отсутствие частично записанного успешного state при ошибке записи и отсутствие PUT после провала preflight.

## Задача 2. Независимый observer и фаза Save

**Файлы:** новый `save_geometry_observer.py`, `save_geometry_smoke.py`, оба новых тестовых файла.

**Вход:** HTTP helpers задачи 1 и workspace shape текущего API.

**Выход:**

- `snapshot_save_state(*, work_order_id: str, edit_version_id: str, feature_id: str) -> dict[str, Any]`: синхронная оболочка над отдельной async read-only транзакцией с существующим DATABASE_URL, без вывода connection string. Параметризованный SQL. Проверяет linkage WorkOrder/EditVersion/DefaultState/feature и возвращает IDs, owner, revision, current EWKB/GeoJSON, operation, baseline EWKB/GeoJSON, упорядоченные command/event records версии с полями identity/outcome/history.
- `run_save_phase(config, *, run_id: str, state_path: Path, evidence_path: Path, opener=urlopen, observer=snapshot_save_state) -> None`.

- [x] Создать integration test observer по паттерну `run_committed_scenario` и `seed_save_context`: снимок соответствует fixture, неверный target отклонён, наблюдение не меняет rows. После service Save observer обнаруживает изменение revision/current/registry/event, сохраняя baseline. Запуск только в isolated test DB.
- [x] Создать phase tests с последовательными fake responses/snapshots: успешный Save; unexpected dirty initial workspace; no-op вместо изменения; canonical response не совпадает с GET; новая history row отсутствует; baseline изменился. Проверять точные postconditions из спецификации.
- [x] Запустить targeted unit tests и isolated integration test, зафиксировать осмысленные failures.
- [x] Реализовать observer и Save phase. Выбирать L-003 по asset code из workspace, требовать три вершины и baseline/current consistency. Для штатной fixture выбрать детерминированный сдвиг внутренней вершины внутри AOI, сохраняющий endpoints; величину и проверку предусловий назвать константами smoke. Проверка не должна импортировать production canonicalizer как единственный oracle: сравнить returned canonical geometry с требуемой неизменностью endpoints и ненулевым внутренним diff.
- [x] Сохранить state только после GET и SQL подтверждения: `schemaVersion`, `runId`, `status`, `target`, `originalRequest`, `saveResponse`, `savedWorkspace`, `beforeSnapshot`, `savedSnapshot`. Записывать отдельный failure evidence без credentials при исключениях.
- [x] Проверить targeted tests (exit 0) и observer через isolated DB suite. Не запускать `RUN_DB_TESTS=1` против demo.

## Задача 3. Verify, replay, четыре отказа и Revert

**Файлы:** `save_geometry_smoke.py`, `test_save_geometry_smoke.py`, CLI в `full_path_workspace_smoke.py`.

**Вход:** `load_phase_state`, HTTP helper и observer предыдущих задач.

**Выход:** `run_verify_phase(config, *, run_id: str, state_path: Path, evidence_path: Path, opener=urlopen, observer=snapshot_save_state) -> None`; success evidence и state status=complete только после всех postconditions.

- [x] Добавить успешный fake сценарий и точные assertions: replay body равен originalRequest; после replay снимок равен savedSnapshot; Revert geometry равна baselineGeometry из GET, а не SQL; два события связаны с двумя successful commands.
- [x] Добавить failures: старая квитанция вернулась с неверным token; replay добавил event; stale возвратил другой code; reused изменил исходную command row; invalid отклонён parsing/structure вместо GEOMETRY_INVALID; отказ изменил current; Revert не очистил changeSet; baseline различается в финале. Каждый провал прерывает дальнейшие mutations.
- [x] Выполнить targeted tests, получить RED на новом поведении.
- [x] Реализовать новую login/session, readback и SQL-сравнение до replay. Выполнить replay без пересоздания CommandId/token/body.
- [x] Реализовать последовательность `stale → reused → invalid → outside` по таблице спецификации. Stale использует original token, остальные новые intents — текущий token; invalid сближает внутреннюю вершину с endpoint, outside перемещает её за штатную AOI. Проверять строгую error shape и сохранённый terminal outcome независимо от HTTP.
- [x] Реализовать Revert и final assertions. На завершении: revision от исходной +2, successful commands=2, rejected=3, events=2; original success и persisted event сохранены. Никаких дополнительных подготовительных Save/no-op.
- [x] Повторить targeted tests и прежний smoke test: exit 0. Убедиться, что каждый из четырёх отрицательных PUT отправлен ровно один раз, завершённый state нельзя использовать повторно.

## Задача 4. CI с настоящим restart и диагностикой

**Файлы:** `.github/workflows/ci.yml`, новый runbook. Продолжает существующий `smoke_test`, не создаёт отдельный browser job или новый полный runner.

**Интерфейс:** CLI задачи 1; директория `$RUNNER_TEMP/day13-smoke` на host и `/tmp/day13-smoke` в backend. UUID run ID создаётся один раз и передаётся обеим фазам. Manifest orchestration содержит StartedAt до/после и status этапов; не содержит секретов.

- [x] Добавить Save step после существующих API smoke. Сохранять state/evidence в контейнере, копировать на host до restart. Следующая фаза получает экспортированный state; не полагаться исключительно на память Python либо оставшийся файл контейнера.
- [x] Добавить restart step: получить container ID и StartedAt, restart только utility_service, в bounded loop сначала доказать смену StartedAt, затем healthy и HTTP health. Timeout/inspect error — nonzero exit, диагностировать сервис без dump окружения. Readiness не принимает старый healthy.
- [x] Добавить verify step с тем же UUID и восстановленным host state. После него копировать финальный evidence/state.
- [x] Добавить `if: always()` сбор доступных файлов и ограниченных logs до Shutdown compose, затем upload artifact. При отсутствии успешного Save не пытаться execute verify; существующий cleanup always сохраняется. Ошибка основного step остаётся failure независимо от успешного upload/cleanup.
- [x] В runbook описать эквивалентные команды и порядок фаз, fresh/readiness guards, значения exit codes, чтение evidence. Для локального полного smoke выбрать отдельную VM/Docker daemon context с disposable stack; перед командами проверять явный context и отсутствие чужих контейнеров. Один новый Compose project name не изолирует фиксированные container_name/ports. Не добавлять локальный `down -v` обычного demo.
- [x] Выполнить live успешный прогон фаз в таком изолированном окружении. Проверить StartedAt различны, PostGIS не перезапускался, сохранённая revision пережила startup chain, итоговые counters и baseline совпали с ожиданиями.
- [x] Проверить fail paths без порчи пользовательской БД: неверный run ID и completed state должны завершиться до PUT; тест orchestration с неизменным StartedAt не допускает verify; недоступный backend даёт timeout/failure evidence. Для readiness predicate использовать извлечённую проверяемую функцию/helper, если shell-цикл иначе нельзя независимо проверить; не подменять live restart mock-проверкой.
- [x] Проверить Compose config и workflow syntax доступным валидатором, `git diff --check`. Локальное выполнение команд workflow не называть успешным GitHub Actions run. Push для запуска CI не выполнять.

## Задача 5. Полная проверка и отчёт

**Файлы:** новый implementation report, `docs/sprint_2/README.md`; при необходимости узкие правки smoke после review. Продуктовые дефекты оформлять отдельно.

- [x] Backend dev image: `docker build --target dev -t geoservice-day13-check apps/backend`; затем `docker run --rm --entrypoint bash geoservice-day13-check -lc "black --check ."`, аналогично `ruff check .` и `pytest`. Expected: exit 0; DB tests без RUN_DB_TESTS штатно пропускаются.
- [x] Из корня репозитория выполнить `infra\db-tests.cmd` (Windows): isolated PostgreSQL/PostGIS integration suite, exit 0. Оно включает новый observer test; обычная demo-БД не используется.
- [x] Из `apps/frontend`: `npm.cmd test -- --maxWorkers=2`, `npm.cmd run typecheck`, `npm.cmd run lint`, `npm.cmd run format:check`, `npm.cmd run build`. Expected: exit 0. В Linux убрать `.cmd`.
- [x] Из `infra/m4`: при отсутствующих dependencies выполнить `npm.cmd ci` и `npx.cmd playwright install chromium`, затем `npm.cmd test`. Проверить exit 0 всех текущих M4/S2-X01 сценариев, без добавления browser job в CI.
- [x] Проверить live API evidence задачи 4 и выполнить итоговое read-only review diff на соответствие спецификации; исправления требуют соответствующего targeted прогона. Повторять полный suite только при изменениях, которые делают прежние результаты недостаточными.
- [x] Проверить все новые и изменённые текстовые файлы на UTF-8/LF, включая untracked, и `git diff --check`.
- [x] Создать русский implementation report: что проверено, команды, run ID/StartedAt, итоговая матрица, пути evidence, фактические ограничения (включая CI ещё не запущен, если так). Не включать auth/credentials и не считать старые evidence новым прогоном.
- [x] Обновить README. Оценить новую устойчивую техническую информацию для repository-change ingest; запускать только при её наличии. Agent memory не дублирует этот план, runbook и отчёт.

## Самопроверка плана

Спецификация покрыта задачами 1–5: phase/state — 1; fresh preconditions и независимое чтение — 2; positive/negative/revert — 3; настоящий restart, штатные seeds, evidence и безопасный lifecycle — 4; suites, локальный browser и отчёт — 5. Все пять рисков review имеют проверки в соответствующих задачах. Публичные interfaces последовательных задач согласованы. Тестовые transport/observer doubles проверяют ошибки oracle, но не заменяют живой прогон. Пользователь поручил исполнение в текущем чате; результаты и решения исполнения сохранены в журнале и отчёте.
