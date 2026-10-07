# День 3 Sprint 2: результат реализации соответствия моделей схеме

Дата: 7 октября 2026 года. Основания: [принятая спецификация](2026-10-06-day-3-model-schema-design.md) и [план реализации](2026-10-07-day-3-model-schema-plan.md).

Статус: пять этапов реализованы и проверены. Независимое финальное ревью завершено; единственное замечание к автономному покрытию закрыто дополнительными tests.

## Реализация

- Добавлены `EditVersionCommand`, `EditVersionCommandState`, `EditVersionChangeEvent`, `EditVersionChangeEventType` и `EditVersion.draft_revision`.
- Подключены exports и активная Alembic metadata. UUID команды передаётся явно; nullable JSONB использует SQL NULL для Python None.
- Перенесены типы, defaults и именованные PK/FK/CHECK/UNIQUE/indexes из migration. History сохраняет независимые UUID без FK и spatial indexes.
- Добавлены проверки metadata, фактического каталога PostgreSQL, ORM round-trip/rollback, populated upgrade/downgrade/upgrade и обеих очередностей конкурентного INSERT history/DELETE root.
- Migration `b7d2e9f4a6c8`, production services, API и инфраструктурная конфигурация не изменены.

## Проверки

| Проверка | Результат |
| --- | --- |
| Новые metadata tests до реализации | 8 failed по ожидаемым отсутствующим моделям, revision и Alembic registration |
| Новые и существующие metadata tests после реализации | 44 passed до ревью; после ревью добавлены ещё 2 tests, включённые в полный успешный suite |
| Parity и ORM integration | 14 passed |
| Migration lifecycle и concurrency | 8 passed |
| Полный обычный backend pytest, `RUN_DB_TESTS=0` | 390 passed, 152 skipped, 2 warnings после закрытия замечания ревью |
| Полный `infra/db-tests.cmd` | 142 passed, 1 warning, exit code 0 |
| Black для всего backend | 254 files would be left unchanged |
| Ruff для всего backend | All checks passed |
| `git diff --check` | Exit code 0 |

Skipped в обычном pytest относятся к отключённым DB/условным проверкам; отдельный DB suite выполнен, не пропущен. Предупреждения — deprecated `anyio.abc.BlockingPortal` в Starlette и `crypt` в passlib. В DB suite остаётся только предупреждение passlib.

Все DB-проверки выполнены в отдельном Compose-проекте `geoservice-db-tests` с disposable `geo_test`. После полного прогона runner удалил контейнеры и сеть; `docker compose ... ps -a` показал пустой список. Demo-БД не мигрировалась и не использовалась для тестового cleanup.

После ревью изменились только автономные metadata tests, поэтому DB suite повторно не запускался: production mappings, migration и DB tests остались теми же, которые прошли 142 проверки. Обычный suite, Black и Ruff запущены повторно. Дополнительно в отдельном Python-процессе без БД и без изменения файлов намеренно заменено CHECK-выражение на `true`, затем удалён UNIQUE из metadata: оба новых теста обнаружили соответствующую ошибку; после восстановления обе проверки прошли.

## Независимое ревью

Read-only reviewer проверил tracked diff, новые Python-файлы, спецификацию, план и пять фокусных рисков. Critical/Important замечаний нет. Единственный Minor: первоначальные автономные tests фиксировали имена CHECK, а определения и event UNIQUE защищались только DB parity. Добавлены два автономных теста, проверяющие определения и точный UNIQUE `(edit_version_id, draft_revision_after)`; замечание закрыто, отложенных замечаний нет.

Reviewer отдельно исключил из оценки production Save/Revert/fingerprint/API/UI, создание triggers через `create_all` и глобальный аудит всей metadata. Это принятые пользователем границы Дня 3; они не расширялись. Полноценное приложение по-прежнему требует миграций Alembic; проверенный результат относится к моделям и схеме, не к будущему Save API.

## Что именно подтверждено

CHECK модели и migration сравниваются после parsing PostgreSQL на TEMP probe table; различия пробелов и casts не скрывают семантические расхождения. Проверки отделяют backing indexes PK/UNIQUE от явных indexes и проверяют deferred terminal trigger.

ORM-проверки используют настоящий commit и новую session для чтения, включая revision выше 32-bit integer, geometry EWKB/SRID, SQL NULL против JSON null, access retry и отказ commit running. Ошибка event откатывает root/snapshot/command целиком. Сохранённая история читается без родителей и защищена от ORM UPDATE/DELETE.

Lifecycle проверяет удаление и восстановление новых объектов и действие guards после повторного upgrade. Текущая geometry и baseline переживают downgrade; registry/history удаляются, revision при восстановлении снова равна 1 — согласно принятому контракту.

Конкурентные tests наблюдают реальные `pg_blocking_pids`. Fixture заранее сохраняет root/snapshot/command без history, чтобы ожидание было вызвано именно INSERT trigger. Проверены commit INSERT перед удалением и commit DELETE перед отклонением вставки.

## Решения при исполнении

- Использована текущая ветка `first-edit-save`, где находились согласованные документы; отдельный worktree не создан. Это сохраняет работу в текущем checkout, но не добавляет изоляцию отдельного worktree.
- Учёт выполнения ведётся PowerShell-ledger вместо bash helpers навыка: среда Windows, commit-range неприменим из-за запрета commit. Цена — ручной учёт шагов.
- Добавлен отдельный test-only `first_save_catalog_support.py`, чтобы lifecycle и parity использовали единые catalog assertions без импорта ORM tests. Цена — один дополнительный небольшой файл.
- Часть сценариев плана объединена параметризацией: revision 1/BIGINT, SQL NULL/JSON null states, ORM mutation/parent deletion и две конкурентные очередности.
- Minor из ревью закрыт, хотя навык исполнения рекомендует откладывать Minor: проверка определений CHECK и UNIQUE без БД была явным пунктом принятой спецификации. Цена решения — два дополнительных теста и повтор обычного regression; production код не менялся.

Отдельная agent memory и repository-change ingest не создавались: контракт, причины и operational constraints уже сохранены в документах Sprint 2 и существующей памяти об изоляции DB tests. Все изменения остаются unstaged; staging, commit и push не выполнялись.
