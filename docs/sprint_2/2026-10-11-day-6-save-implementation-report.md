# День 6: отчёт реализации synchronous Save

Дата: 11 октября 2026 года. Основание: [принятая спецификация](2026-10-11-day-6-save-design.md) и [план](2026-10-11-day-6-save-plan.md). Все шесть задач выполнены; изменения оставлены unstaged в `first-edit-save`.

## Результат

`EditVersionService.save_geometry()` выполняет внутренний Save в одной transaction и возвращает success только после успешного commit. `EditVersionRepository` хранит geometry, revision и command result на общей session; отдельного command/event repository нет.

- Root lock сериализует изменения version. Новый запрос проверяет opaque `DraftVersionToken` перед validation/write.
- Глобальный `CommandId` резервируется через `ON CONFLICT DO NOTHING`; проигравший INSERT читает результат отдельным SELECT. Savepoints и committed running не используются.
- Matching retry возвращает сохранённый результат до stale-проверки и повторной spatial validation. Изменение identity/fingerprint даёт `COMMAND_ID_REUSED`, не изменяя исходную команду.
- Content change, включая восстановление baseline, увеличивает revision один раз. No-op и replay её не увеличивают. Новый no-op сохраняет terminal success.
- На baseline возвращаются `operation=unchanged`, `hasPersistedChangeSet=false`, `basicValidation=null`; no-op изменённого current сохраняет updated/summary.
- Новая неуспешная попытка откатывает geometry, revision и reservation. Проверены ошибки после write, increment, finalization и ошибка deferred commit.
- Доступ и lifecycle проверяются перед replay. Legacy rejected result воспроизводится без access resume; history-only ID отвергается.

## Проверки

Все команды ниже выполнены после последнего изменения production-кода, exit code 0. Общий префикс Compose: `docker compose -p geoservice-db-tests -f infra/docker-compose.test.yml`.

| Проверка | Команда после префикса | Результат |
| --- | --- | --- |
| Сборка текущего кода | `build backend_db_tests` | успешно |
| Атомарность, baseline вне grid, legacy rejection, отзыв доступа | `run --rm backend_db_tests python -m pytest tests/integration_tests/test_save_geometry_atomicity.py --tb=short` | 14 passed |
| Полный non-DB backend | `run --rm --no-deps -e RUN_DB_TESTS=0 backend_db_tests python -m pytest --tb=short` | 531 passed, 228 DB skipped, 2 warnings |
| Полный fresh DB | `down -v --remove-orphans`, затем `up --abort-on-container-exit --exit-code-from backend_db_tests` | 229 passed, 2 warnings |
| Black | `run --rm --no-deps -e RUN_DB_TESTS=0 backend_db_tests python -m black --check .` | 296 files unchanged |
| Ruff | `run --rm --no-deps -e RUN_DB_TESTS=0 backend_db_tests python -m ruff check .` | All checks passed |

`git diff --check` также успешен. Два существующих предупреждения относятся к deprecated `crypt` в passlib и `BlockingPortal` в Starlette. Числа non-DB и DB не суммируются как число уникальных тестов: наборы частично пересекаются.

Шесть конкурентных DB-сценариев включены в полный прогон: одинаковая команда, разные команды с одним token, одинаковый ID разных versions при commit/rollback победителя, Save/Open в обоих порядках. Отдельные sessions и `pg_blocking_pids` подтверждают реальные ожидания locks; проверена свежая revision при retained ORM root.

TDD evidence и промежуточные проверки находятся в [журнале исполнения](2026-10-11-day-6-execution-ledger.md). Дополнительные DB-проверки поверх уже работающего service были GREEN сразу; искусственный RED не создавался.

## Ревью и отклонения от плана

Независимый reviewer проверил реализацию против спецификации и пяти focus cases. Найденный P2 исправлен: `UserRepository.get_by_id()` теперь применяет `populate_existing=True`. Без этого SELECT возвращал retained ORM User со старой ролью/активностью при `expire_on_commit=False`, позволяя новый Save или replay после отзыва доступа между transactions.

Четыре реальных DB-регрессии (inactive/reviewer × fresh/replay) сначала упали из-за отсутствия ожидаемого отказа, затем прошли после исправления. Snapshot подтверждает отсутствие mutation при отказе. Повторное независимое review: блокирующих замечаний нет. Reviewer проверил код; полные suites запускал исполнитель.

Тесты сгруппированы по наблюдаемым сценариям, поэтому некоторые имена отличаются от плана. Root provenance и single-use revision проверяются реальной DB/session в `test_edit_version_command_repository.py`; отдельный mock-only `test_edit_version_command_protocol.py` не создавался. Policy snapshot проверяется fixture с отличающейся global policy. Несколько этапов full Save/no-op/revert/retry объединены в последовательный DB-сценарий.

Использован существующий пригодный checkout. Lifecycle штатного DB runner воспроизведён явными Compose-командами с тем же disposable project и isolation guard. Demo-БД не использовалась. Изменение `UserRepository` — единственное дополнительное production-исправление по результатам review; публичная signature сохранена, все callers покрыты полной регрессией backend.

## Границы результата

Это согласованный внутренний этап Дня 6: endpoint/UI не добавлены. Запись событий, новые durable rejections и rejected→running при изменении доступа остаются на День 7. Save Дня 6 не добавляет history events; это проверяется snapshot.

Сохраняются предпосылки: READ COMMITTED, сервис владеет внешней transaction, AOI/baseline/assignment неизменны во время Save. Временное правило D5-Q1 о нулевых соседних сегментах не изменено. После удаления и registry, и history бессрочная дедупликация не гарантируется.

Agent memory не дублирует эти материалы: решения и причина исправления уже сохранены в спецификации, коде и этом отчёте. `/ingest repository-change` не запускался: отдельной новой технической информации для Code_wiki вне сохранённых материалов в рамках этой задачи не выделено. Git staging, commit и push не выполнялись.
