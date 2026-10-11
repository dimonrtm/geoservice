# День 7: результат реализации и проверка M2

Дата: 11 октября 2026 года. Статус: реализация завершена; M2 подтверждена для внутреннего backend Save/Revert.

Основание: [принятая спецификация](2026-10-11-day-7-rejections-events-revert-design.md) и [план](2026-10-11-day-7-rejections-events-revert-plan.md). Ход исполнения и RED/GREEN evidence — в [журнале](2026-10-11-day-7-execution-ledger.md).

## Реализованное поведение

Ожидаемые отказы существующего target сохраняются в command registry внутри общей transaction. API exception выдаётся после успешного commit. Stale, reused command, invalid structure, invalid geometry и ошибки AOI имеют отдельные исходы. Инфраструктурная ошибка откатывает transaction и не превращается в подтверждённый domain rejection.

Обычный terminal rejection воспроизводит первоначальные status/code/message, пока существует registry. Исправление исходных условий не даёт повторно исполнить ту же команду. Для раннего отказа с отсутствующим или непригодным baseline применяется отдельный `geom-contextless-v1:sha256:`; после ремонта baseline исходный формат сохраняется, grid-equivalent запрос остаётся тем же запросом. Старый `geom-v1` не изменён.

Текущее право доступа и lifecycle проверяются до раскрытия сохранённого результата. Только access rejection с соответствующим флагом может возобновиться после восстановления доступа; исходная identity сохраняется. Повтор проходит проверку исходного token и может закончиться success или ordinary rejection. Сбой попытки возвращает БД к прежнему committed отказу.

Каждый новый content-changing Save/Revert атомарно записывает ровно одно событие: current → revision → succeeded command → event → commit. No-op и replay не добавляют событие или revision. Revert восстанавливает точный baseline EWKB и возвращает `operation=unchanged`, `hasPersistedChangeSet=false`, `basicValidation=null`. История append-only; backfill для старых команд не выполняется.

Production-изменения находятся в `edit_version_service.py`, новом helper `edit_version_save_identity.py`, rejection DTO, новом domain-модуле `contextless_fingerprint.py` и существующих repository/SQL helpers. Schema, migrations и зависимости не менялись.

## Фактическая проверка

Команды выполнялись из корня репозитория на финальном backend-коде, после пересборки image.

| Проверка | Команда | Результат |
| --- | --- | --- |
| Backend regression без DB | `docker run --rm -e RUN_DB_TESTS=0 geoservice-db-tests-backend_db_tests python -m pytest --tb=short` | 555 passed, 257 skipped, 2 warnings; exit 0 |
| Полный isolated DB runner | `.\infra\db-tests.cmd` | 258 passed, без skipped, 2 warnings; exit 0; disposable project удалён |
| Форматирование | `docker run --rm geoservice-db-tests-backend_db_tests python -m black --check .` | 302 files would be left unchanged; exit 0 |
| Lint | `docker run --rm geoservice-db-tests-backend_db_tests python -m ruff check .` | All checks passed; exit 0 |
| Целевые проверки после review | Три suites: events, rejections integration, atomicity | 36 passed |

257 skipped относятся к отключённым DB-проверкам первого запуска; полный DB runner выполнил обязательные suites отдельно. Числа двух прогонов не следует складывать как количество уникальных тестов: часть integration tests выполняется и без БД. Два предупреждения — deprecation в Starlette/anyio и passlib/crypt.

Первый финальный DB runner прервался из-за параллельного unit-контейнера, обнаруженного Compose, и не считается успешной проверкой. Приведённый результат 258 passed получен отдельным повторным запуском без других Docker-проверок.

## Соответствие M2 тестам

Имена файлов ниже относятся к `apps/backend`. DB suites находятся в `tests/integration_tests`, unit suites — в `utility_service/use_cases/tests`, fingerprint suites — в `utility_service/domain_services/tests`.

| M2 | Доказательство |
| --- | --- |
| 01 | `test_save_geometry_events.py`: Save A → B → Revert, точные before/after EWKB, типы и revisions |
| 02–03 | Events, atomicity и `test_save_geometry_replay.py`: no-op baseline/current, replay после нового Save |
| 04–05 | `test_save_geometry_rejections_integration.py`, unit rejections/replay: durable outcomes, неизменное состояние и первоначальный отказ после ремонта |
| 06 | DB baseline provenance repair; unit missing/unreadable/wrong-type baseline; exact/grid-equivalent retry |
| 07–08 | `test_contextless_fingerprint.py`, `test_geometry_fingerprint.py`, unit replay/rejections: golden bytes/hash, границы округления, identity, unknown prefix |
| 09–10 | Unit service/replay/rejections и DB rejection matrix: role/access/lifecycle guards, ранняя непригодность baseline, stale и spatial validation |
| 11–12 | DB repair/access matrix и `test_successful_access_resume_rolls_back_to_original_rejection`: resume success/stale, immutable identity, rollback finalization/event/commit |
| 13–14 | `test_save_geometry_atomicity.py` и DB rejections: fault injection, реальные deferred commit failures, отсутствие partial writes |
| 15–18 | `test_save_geometry_concurrency.py`: одинаковые команды, stale проигравшего, глобальный ID между versions, commit/rollback, Save/Open; atomicity проверяет отозванный доступ |
| 19 | `test_first_save_command_constraints.py`, `test_first_save_event_constraints.py`, `test_edit_version_command_repository.py`: terminal/identity/provenance/append-only constraints |
| 20 | `test_off_grid_baseline_roundtrip_and_revert_preserve_storage`, events chain: точная геометрия и неизменность исходных данных |
| 21 | `test_old_revision_starts_history_without_backfill`: настоящая succeeded geom-v1 row без event, replay до/после нового изменения 5 → 6 |
| 22 | DB call helpers создают новые session/service для повторов; committed state читается независимо |
| 23 | Unit request/service/replay: request boundary и отсутствующий target не резервируют ID; occupied row неизменна. Нового HTTP endpoint в этом этапе нет |
| 24 | `test_history_id_survives_registry_deletion`: история препятствует повторной mutation старого CommandId |

Полный DB runner также проверяет существующие migration, metadata, repository и Open-контракты.

## Review и отклонения от плана

Независимое review не подтвердило production-дефекты P1/P2, но нашло три существенных пробела в тестах: настоящая старая команда без события, rollback успешного access resume и durable multiple-feature rejection на БД. Все три добавлены и проверены целевым и полным прогоном.

Дополнительные предложения review — явные assertions CommandId/base revision в цепочке и более широкие комбинации guard failures — оставлены как возможное усиление существующих provenance/guard проверок; изменения поведения для них не требуются.

DB rejection suite получила суффикс `_integration`, чтобы избежать совпадения имени с unit module. Повреждение baseline на БД моделируется несовпадающим provenance: geometry CHECK не отключается. Нечитаемые EWKB и неверный geometry type проверяются unit-тестами. Сценарии объединены в параметризованные suites; названия отдельных тестов могут отличаться от плана.

RED/GREEN проведён для новых production-интерфейсов и обнаруженного дефекта выбора fingerprint. Дополнительные DB acceptance tests после завершения этих интерфейсов сразу проходили; искусственное повреждение готовой реализации ради RED не выполнялось.

## Границы результата и передача

M2 подтверждает внутренний backend-контракт. HTTP endpoint/readback, correlationId integration, UI и реальный process restart остаются последующим этапам. Новая session не объявляется доказательством restart.

Для старого `geom-v1`, чей immutable baseline стал нечитаемым, возвращается context error без изменения старой row: сравнение через другой fingerprint не допускается. Terminal registry сохраняется до физического удаления EditVersion; history переживает его удаление. Полнота истории проверяется только для новых content-changing команд Дня 7.

Изменения оставлены unstaged в `first-edit-save`; staging, commit и push не выполнялись. Agent memory не дополнена: решения, причины и ограничения уже сохранены в артефактах этого дня. Repository-change ingest не запускался: отдельного нового знания сверх этих документов не выделено.
