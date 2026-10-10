# День 5: результат реализации атомарного repository context

Дата: 10 октября 2026 года. Контрольная точка **M1 пройдена** в scope [принятой спецификации](2026-10-10-day-5-repository-context-design.md). Изменения оставлены unstaged в `first-edit-save`; staging, commit и push не выполнялись.

## Реализованная граница

`EditVersionRepository` принадлежит агрегату **EditVersion**. Геометрия остаётся значением current feature. После дополнительного решения пользователя операции создания и повторного открытия также перенесены в этот репозиторий; подробности ниже.

Repository получает внешнюю AsyncSession transaction, блокирует нужный root через `FOR UPDATE` и отдельным последующим SQL читает current, immutable baseline по `default_state_id`, AOI и остальные изменённые features всей версии. Чтение использует column projection, поэтому ранее загруженные ORM objects не подменяют актуальные данные после ожидания lock. Repository не вызывает begin/commit/rollback.

`prepare_candidate` использует persisted policy и Decimal-ядро Дня 4. `validate_candidate` проверяет исходный context, структуру и переход, затем точные записываемые bytes средствами PostGIS: XY/SRID/range, nonempty, valid/simple, нулевые сегменты и покрытие всей линии AOI. AOI boundary допустима; holes, вогнутость и MultiPolygon учитываются. Ожидаемые отказы возвращаются без перевода transaction в aborted state.

`write_current` меняет только geometry/operation target. Numeric no-op не выполняет UPDATE. Настоящий Revert восстанавливает baseline EWKB без округления исходных off-grid координат; signed zero не создаёт искусственное изменение. DefaultState, associations, properties, network_version и draft_revision repository не изменяет.

Handles привязаны к session, внешней transaction, identity выдачи и поколению context. Чужие, завершённые, подменённые и повторно использованные handles отвергаются. Savepoint во время жизни scope инвалидирует его. После записи либо no-op старые context одной версии непригодны; fresh read под прежним root lock допустим.

## Проверки M1

| Область | Evidence |
| --- | --- |
| Root/current/baseline/AOI | `test_edit_geometry_context.py`, `test_edit_geometry_validation.py`: missing links, eligibility, несовместимые исходные данные, persisted policy |
| Spatial validation | `test_edit_geometry_spatial.py`: valid и non-simple раздельно, invalid, collapsed segment после canonicalization, boundary/hole/вогнутая AOI/MultiPolygon, changed feature вне workspace |
| Mutation и precision | `test_edit_geometry_mutation.py`: полный snapshot до/после, точный baseline restore, signed zero, SQL-observer отсутствия UPDATE на no-op, rollback, stale/forged/session/transaction/savepoint handles |
| Конкуренция | `test_edit_geometry_concurrency.py`: независимые соединения, `pg_blocking_pids`, commit/rollback, stale identity map, разные версии, reopen в обоих порядках |
| History compatibility | Root → command → feature → test-only revision → terminal command → event; проверены before/after EWKB и event trigger |
| Новые tests | 35 passed: новые repository integration tests и unit protocol tests |
| Регрессия без БД | `python -m pytest --tb=short`, `RUN_DB_TESTS=0`: **506 passed, 204 skipped**, 2 dependency deprecation warnings; skips относятся к отдельно запущенной DB-матрице |
| Полная isolated DB-регрессия | Fresh `geo_test` / `geoservice-db-tests`, штатный Compose runner: **205 passed, 0 skipped**, 2 dependency deprecation warnings |
| Backend quality | `python -m black --check .`: 286 файлов; `python -m ruff check .`: passed |
| Независимое review | Отдельный reviewer `gpt-6-astra`, read-only, все пять focus cases; Critical/Important/Minor замечаний нет |

Команды выполнялись из корня репозитория. Для unit/quality использован `docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml run --rm --no-deps -e RUN_DB_TESTS=0 backend_db_tests` с соответствующей командой Python.

Полный DB lifecycle выполнен теми же командами, что содержит `infra/db-tests.cmd`: `down -v --remove-orphans`, затем `up --build --abort-on-container-exit --exit-code-from backend_db_tests`, затем cleanup. В повторном прогоне после форматирования SQL добавлен только `--attach backend_db_tests`, ограничивающий вывод логов. Demo-БД не использовалась.

Ruff первоначально выявил два неиспользуемых test imports; они удалены, повторная проверка прошла. SQL-строки новых tests отформатированы; повторный DB-прогон итоговых файлов дал 205 passed, повторные Black/Ruff прошли. Тестовый Compose project удалён, cleanup exit 0. TDD evidence и решения при исполнении сохранены в [ledger](2026-10-10-day-5-execution-ledger.md).

## Границы результата и открытое уточнение

- **D5-Q1 требует доменного уточнения:** временно любой нулевой сегмент после canonicalization запрещён с `GEOMETRY_INVALID`. Самопересечение отклоняется независимо от этого временного правила.
- Production Save endpoint/service, access/lifecycle/token/replay, revision increment, registry и event orchestration остаются задачами Дней 6–7. Repository compatibility test не означает готовность публичного Save.
- Контракт требует READ COMMITTED и стабильности baseline/AOI/assignment во время Save. Все конкурирующие Saves должны соблюдать root-lock protocol; произвольные SQL/ORM writers за его пределами не защищены.
- Session-local listeners очищают ссылки на handles при завершении transaction, но сами живут до освобождения session. Это осознанное отличие от буквального удаления listeners после каждой transaction.

## Документация и передача

### Перенос операций версии после обсуждения реализации

По прямому решению пользователя `get_open_edit_version`, `create_open_edit_version` и `touch_edit_version` перенесены из WorkOrderRepository в EditVersionRepository. Тела методов сохранены. В EditVersionService добавлена обязательная зависимость `edit_version_repository`; обновлены сборка зависимостей и все места создания сервиса в тестах. В тестах сервиса разделены подмены репозиториев наряда и версии.

WorkOrderRepository сохраняет чтение, блокировку и запись наряда, поиск по коду, список нарядов исполнителя и `get_workspace_aggregate`. Общая транзакция, порядок блокировок, ответы API, копирование базового состояния, policy и обработка конфликта уникальности сохранены.

Проверка после переноса: 24 теста сервиса/API прошли; полный backend-прогон без БД — 506 passed / 204 ожидаемых DB skips; отдельный свежий PostGIS-прогон — 205 passed без skips. Black (286 файлов) и Ruff прошли. Изменение относится к распределению ответственности, без новых таблиц или API. Результат независимого review выше относится к первоначальной реализации Дня 5; перенос проверен отдельной регрессией.

### Техническая wiki

Через `source-command-ingest` в режиме `repository-change` сохранено новое техническое знание в `Code_wiki/архитектура/edit_version_persistence.md`. Конфликт старого утверждения об отсутствии EditVersionRepository зафиксирован как `FU-2026-10-10-001`, затем исправлен в backend architecture. Agent memory не дублирует эти знания поверх спецификации и wiki.

Wiki lint имеет 37 прежних `missing_frontmatter` только в неизменяемых RAW Markdown files; новых проблем вне RAW нет. Это отдельное известное ограничение knowledge pipeline, не ошибка backend tests. `git diff --check` прошёл. Дополнительно проверены все 24 изменённых/новых файла на whitespace и conflict markers, локальные Markdown-ссылки sprint artifacts разрешаются.
