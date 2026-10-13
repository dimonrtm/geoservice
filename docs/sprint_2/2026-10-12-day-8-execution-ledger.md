# Журнал исполнения — docs/sprint_2/2026-10-12-day-8-api-readback-plan.md

Спецификация и план приняты; пользователь поручил реализацию. Последовательное исполнение в текущем чате, отдельное итоговое review.

## Решения и предварительная сверка

- Ruling: используется текущий checkout `first-edit-save`, не main/master — он содержит согласованные незакоммиченные документы; новый worktree не нужен по правилу платформы о переиспользовании подходящего checkout. Цена ошибки: изменения остаются в этой feature branch для ручного review.
- Ruling: журнал находится в `docs/sprint_2`, вместо Bash scratch helpers навыка — пользователь задал папку артефактов, Windows и запрет commits делают commit-based ledger неприменимым. Результаты сохраняются по задачам и тестам, не по commit ranges.
- Pre-flight 1→3: BasicValidationOut переиспользуется в workspace, aliases совпадают со спецификацией.
- Pre-flight 2→3: raw EWKB в features_data декодируется после access guards; old unit fixtures обновляются вместе с projection.
- Pre-flight 3→4: off-grid fixture должна создавать согласованные baseline/current; правило immutable production baseline не меняется.
- Pre-flight 1→4→5: настоящие auth/service dependencies получают fresh session на запрос; CORS проверяется на production ASGI wrapper.

## Задачи

- Baseline: 555 passed, 257 skipped (RUN_DB_TESTS=0), 2 existing dependency warnings.
- Задача 1: complete. RED: 29 failed / 1 passed (нет PUT, default validation body, CORS). GREEN: 68 passed, 2 existing warnings — новые API/contract tests и прежние parser/work_orders tests. Parser/fingerprint/Save service не изменены.
- Задача 2: complete. RED: 2 failed / 3 passed — отсутствуют revision и baseline rows. GREEN: 5 passed, включая реальные SQL-пары вне AOI и baseline именно этой версии; один SQL execute.
- Задача 3: complete. RED: отсутствует модуль projection; добавлены проверки состояния, целостности всех пар и signed zero. GREEN: 45 целевых проверок (в составе прогона 55 passed вместе с задачей 4). Единственная поправка теста: GeoJSON Pydantic хранит пары tuple; JSON assertion выполняется через model_dump(mode="json"). Production codec не менялся.
- Задача 4: complete. 10 HTTP + DB cases прошли с первого запуска после сборки harness: auth/services настоящие, override только session. Для Open fixture удаляет заранее созданную тестовую версию без истории и переводит задание в assigned до начала сценария. Добавлен no-op readback. Этот этап подтверждает уже реализованную интеграцию; искусственное RED не заявляется.
- Задача 5: complete. 14 passed: concurrency + HTTP regression + OpenAPI. Первый прогон зелёный: требуемый wiring уже обеспечен задачами 1–3. Event barrier останавливает Save после write_current до commit; GET без root lock возвращает старый снимок, затем новый. Проверены ссылки схем, UUID, XY, nullability, legacy open validation и CORS.
- Задача 6: complete. Общая регрессия и независимое review завершены; отчёт и README обновлены. Изменения unstaged.

## Проверки общей регрессии

- Black: 314 files unchanged. Ruff: all checks passed. Unit: 610 passed, 269 skipped (DB отключена), 2 existing warnings.
- Первый полный DB-прогон после локальных committed сценариев: 267 passed / 3 failed. Причина: старый cross-context fixture удаляет working-copy rows, которые уже связаны с append-only history предыдущих прогонов. Попытка изменить порядок DELETE наткнулась на запрет удаления history; изменение fixture отменено полностью. Ruling: полный набор запускать на свежем `postgis_test`/`geo_test` в tmpfs, как предполагает disposable test harness; не ослаблять production constraints и не менять сторонние тесты ради очистки.
- Полная свежая DB regression: 270 passed, 0 skipped, 2 existing warnings. Demo DB не затрагивалась.

## Итоговое review и решения

- Fresh-context review выполнено `day8_final_review` (gpt-6-astra) по всему unstaged/untracked Day8 diff: Critical/Important нет, один Minor по multiline style.
- Final: Ruling: Minor style исправлен, поскольку это прямо сохранённое пользовательское правило оформления нового кода. Поведение не менялось: сравнение AST/SQL tokens пяти файлов совпало. Финальные Black/Ruff чистые, 22 затронутых API/service/DB tests passed.
- Final: Ruling: повторная spatial/topology validation при GET — не выполняется по принятому дизайну; summary описывает гарантии persisted Save, не новую приёмку качества. Цена неверного толкования — ложное представление о readiness; status POSITIONAL_ACCURACY_UNVERIFIED сохранён.
- Final: Ruling: browser/backend restart не подтверждён новыми sessions и остаётся отдельным этапом. Цена неверного толкования — неподтверждённая recovery readiness; отчёт явно ограничивает доказательство.
- Final: Ruling: dirty disposable DB не поддерживает старую глобальную очистку при наличии append-only history; свежий контейнер является границей полного тестового прогона. Цена нарушения — ложные setup failures, не ослабление history guards.
- Новая техническая нода API/readback сохранена через repository-change только в Code_wiki; исторические расхождения перечислены как follow-up без правок внешних wiki/state. Lint: только 37 известных RAW missing_frontmatter. Agent memory не дублирует код/спецификацию/ноду.
- Ruling по finishing-a-development-branch: пользователь заранее требует оставить unstaged и лично выполняет stage/commit/push. Ветка и checkout сохраняются, меню merge/push не предлагается; Git state не меняется.
