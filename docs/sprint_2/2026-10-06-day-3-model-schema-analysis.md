# День 3 Sprint 2: анализ соответствия ORM и схемы

Дата анализа: 6 октября 2026 года. Календарный день задачи: среда, 5 августа 2026 года.

Статус: анализ сохраняет исходное состояние до реализации и основания решений. [Письменная спецификация](2026-10-06-day-3-model-schema-design.md) принята 7 октября 2026 года; [план](2026-10-07-day-3-model-schema-plan.md) исполнен. Текущее состояние и проверки описаны в [отчёте реализации](2026-10-07-day-3-model-schema-implementation-report.md).

## Цель из запроса

Добавить SQLAlchemy models для command registry и change events, проверить PK, FK, CHECK/UNIQUE и spatial indexes, подтвердить upgrade/downgrade/upgrade. Результат — соответствие моделей и metadata миграции, подтверждённое migration integration tests и model metadata tests. Артефакты обсуждения сохраняются в `docs/sprint_2`.

## Основания анализа

- [Календарный план](2026-07-31-sprint-2-calendar-plan.md), День 3.
- [Принятая спецификация Дня 2](2026-10-01-day-2-first-save-schema-design.md).
- [Отчёт Дня 2](2026-10-01-day-2-first-save-schema-implementation-report.md).
- [Миграция b7d2e9f4a6c8](../../apps/backend/utility_service/infrastructure/postgresql/alembic/versions/b7d2e9f4a6c8_first_save_schema.py).
- [EditVersion](../../apps/backend/utility_service/infrastructure/postgresql/models/work_order/edit_version.py), [EditVersionFeature](../../apps/backend/utility_service/infrastructure/postgresql/models/work_order/edit_version_feature.py).
- [Экспорты work_order](../../apps/backend/utility_service/infrastructure/postgresql/models/work_order/__init__.py), [Alembic env.py](../../apps/backend/utility_service/infrastructure/postgresql/alembic/env.py), [alembic.ini](../../apps/backend/alembic.ini).
- [Metadata tests](../../apps/backend/utility_service/infrastructure/tests/test_network_model_metadata.py).
- [Migration tests](../../apps/backend/tests/integration_tests/test_first_save_schema_migration.py), [registry tests](../../apps/backend/tests/integration_tests/test_first_save_command_constraints.py), [history tests](../../apps/backend/tests/integration_tests/test_first_save_event_constraints.py).

Исходная рабочая копия чистая; HEAD при начале исследования — `1e88553`. Активная Alembic chain находится в `utility_service/infrastructure/postgresql/alembic`, что явно задано в `apps/backend/alembic.ini`. Старые пути `app/alembic` из file-map не являются основанием для выбора активной цепочки.

## Подтверждённые расхождения

| Область | Миграция | Текущая ORM / проверка |
| --- | --- | --- |
| Revision root | `draft_revision BIGINT NOT NULL DEFAULT 1`, CHECK `>= 1` | Поле и CHECK отсутствуют в `EditVersion` |
| Registry | Таблица `work_order.edit_version_commands` | Соответствующей модели нет |
| History | Таблица `work_order.edit_version_change_events` | Соответствующей модели нет |
| Подключение metadata | Новые таблицы создаются Alembic | Новых классов нет в exports и списке импортов `env.py` |
| Metadata regression | Новая схема содержит revision | Существующий тест проверяет точный старый набор полей `EditVersion` |

## Контракт registry по DDL

13 колонок: `command_id`, `edit_version_id`, `feature_id`, `actor_user_id`, `request_fingerprint`, `state`, `retry_on_access_change`, `response_status`, `response_payload`, `rejection_code`, `rejection_message`, `created_at`, `completed_at`.

- Именованный PK `pk_edit_version_commands` по `command_id`; UUID не имеет server default.
- FK `fk_ev_commands_edit_version`: `edit_version_id -> edit_versions.id`, `CASCADE`.
- Составной FK `fk_ev_commands_feature`: `(edit_version_id, feature_id) -> edit_version_features`, `NO ACTION`.
- Actor не имеет FK.
- Четыре CHECK: fingerprint, state, result shape, access retry.
- Один явный B-tree index `ix_ev_commands_version_feature` с порядком `(edit_version_id, feature_id)`; PK также создаёт индекс в PostgreSQL.
- `response_status` — SMALLINT; `response_payload` — nullable JSONB; даты — TIMESTAMPTZ.
- Server defaults: `retry_on_access_change=false`, `created_at=now()`; у `state` default отсутствует.
- Переходы и неизменность identity проверяет BEFORE trigger; запрет commit строки в `running` — deferred constraint trigger. Эти гарантии не представлены обычными `CheckConstraint`.

## Контракт history по DDL

13 колонок: `command_id`, `edit_version_id`, `work_order_id`, `default_state_id`, `feature_id`, `actor_user_id`, `event_type`, `before_geometry`, `after_geometry`, `base_network_revision`, `draft_revision_before`, `draft_revision_after`, `occurred_at`. Все NOT NULL; единственный server default — `occurred_at=now()`.

- PK `pk_edit_version_change_events` по `command_id`.
- UNIQUE `uq_ev_events_version_revision` по `(edit_version_id, draft_revision_after)`.
- **FK отсутствуют намеренно**, включая `command_id`: история сохраняется после удаления версии и registry.
- Шесть CHECK: тип события, base revision, последовательность draft revisions, обе geometry, фактическое различие EWKB.
- Geometry — `LINESTRING`, SRID 4326, `spatial_index=False` для обеих колонок.
- **GiST индексов истории нет намеренно**: принятый scope исключает spatial search по истории. Два индекса PostgreSQL обеспечивают PK и UNIQUE.
- Контекст события проверяется при INSERT с блокировками root `FOR UPDATE`, command и feature `FOR SHARE`.
- UPDATE/DELETE/TRUNCATE запрещены triggers. Сохранность истории нельзя оценить только по ORM relationships или FK.

## Spatial indexes и границы слова «полностью»

У существующего `EditVersionFeature.geometry` объявлен один явный GiST `ix_edit_version_features_geometry`; автоматическое создание индекса GeoAlchemy2 выключено. Это уже проверяется metadata test. Требование «проверить spatial indexes» не означает, что индекс необходимо добавить каждой geometry-колонке.

`Base` не задаёт naming convention. Поэтому проверка имён PK новых моделей отличается от простого указания `primary_key=True` без имени constraint.

Обычная declarative metadata и полный набор объектов PostgreSQL различаются: функции и triggers миграции существуют отдельно. Пользователь подтвердил ограниченный scope объектов Дня 2 и создание полноценной схемы только через Alembic; воспроизводимость защит через `Base.metadata.create_all()` не требуется.

## Что доказывают существующие тесты

- `test_fresh_upgrade_creates_first_save_objects`: downgrade до `base`, upgrade до `head`, наличие новых таблиц, свойства revision, отсутствие FK истории и ровно два B-tree индекса истории.
- `test_populated_upgrade_preserves_snapshot`: downgrade до предыдущей revision, заполнение контекста, upgrade, сохранение snapshot и начальная revision 1 без synthetic history/commands.
- Registry tests проверяют формы результатов, scoped FK, переходы, identity, commit незавершённой команды, повтор access rejection.
- History tests проверяют контекст, ограничения, уникальность, append-only, сохранность истории при последовательном удалении версии, rollback общей операции.

Вызовы downgrade/upgrade уже есть, но это не отдельное доказательство полного lifecycle новой migration: нет явной проверки удаления всех её функций/triggers/колонки между проходами и повторного действия защит после повторного upgrade. В просмотренных first-save tests нет конкурентного сценария INSERT history против удаления root. Эти пробелы согласуются с границами отчёта Дня 2.

Результаты 125 DB tests и 380 обычных tests приведены в предыдущем отчёте; в рамках текущего анализа тесты ещё не запускались. Статическое чтение не подтверждает работоспособность текущего окружения и отсутствие runtime-расхождений.

## Уточнения перед решением

1. Область parity согласована: объекты Дня 2 и их непосредственные зависимости. Аудит всей активной `Base.metadata` в задачу не входит.
2. Конкурентная проверка INSERT history против удаления `EditVersion` включена пользователем в обязательную приёмку Дня 3.
3. Согласовано: полноценная схема создаётся только через Alembic. ORM metadata отражает таблицы, колонки, ограничения и индексы; самостоятельное создание функций/triggers через metadata не требуется.
4. В приёмку включены integration tests записи/чтения через ORM и взаимодействия с triggers при `flush/commit`, без реализации Save service и API.

Ответы на четыре вопроса получены и зафиксированы ниже. Конкретный дизайн обсуждается отдельно от этих согласованных требований.

### Согласованные уточнения

- Пользователь подтвердил область соответствия: объекты Дня 2 и их непосредственные зависимости. Основные объекты — `EditVersion.draft_revision`, registry и history; связанные таблицы рассматриваются в части ключей, ограничений и индексов, необходимых для этого контракта.
- Пользователь подтвердил включение конкурентного INSERT истории и удаления `EditVersion` в обязательную приёмку Дня 3. Существующий последовательный тест удаления эту проверку не заменяет.
- Пользователь подтвердил Alembic как единственный способ создания полноценной схемы. Функции и triggers остаются в migration; эквивалентность `Base.metadata.create_all()` полной схеме не требуется. Поиск по Python-файлам backend не обнаружил вызовов `create_all` или `drop_all`.
- Пользователь подтвердил integration tests записи/чтения через ORM в дополнение к SQL migration tests и metadata tests. Save service и API остаются вне Дня 3.

## Дополнительные выводы для дизайна

### SQL NULL и JSON null

`ck_ev_commands_result` требует `response_payload IS NULL` для `running` и `rejected`. Существующие SQL fixtures передают SQL NULL через `CAST(:payload AS jsonb)`. Перенос этого контракта в ORM требует явной политики Python `None`: обычный JSON type различает SQL NULL и JSON null, а `none_as_null=True` задаёт преобразование `None` в SQL NULL. Источник: [SQLAlchemy 2.0 JSON](https://docs.sqlalchemy.org/en/20/core/type_basics.html#sqlalchemy.types.JSON).

Это выявленный риск будущей модели, а не воспроизведённый дефект: новой модели пока нет. В backend закреплена версия SQLAlchemy 2.0.36.

### Порядок записи

По исходникам migration INSERT terminal command сразу запрещён. Тест ORM должен сначала записать `running`, затем terminal state в той же transaction. Event context trigger читает уже сохранённые строки command/root/feature; помещение объектов в session само по себе не доказывает, что trigger увидит нужный порядок SQL. У history нет FK, задающего зависимость от registry. Дизайн должен явно определить границы `flush` перед вставкой history, не вводя промежуточный commit.

### Удаление с associations

В текущем SQL-тесте сначала удаляются `edit_version_associations`, затем root. Это существенно: associations имеют FK к features с `RESTRICT`. Конкурентная проверка должна учитывать этот реальный контекст, а не использовать только пустую версию. Подготовка полного удаления не означает создание нового production API удаления в День 3.

### Независимость проверок

Существующие metadata tests проверяют точные exports и колонки `EditVersion`, но многие ограничения проверяются только по наличию имени. Для новой приёмки наличия имени недостаточно: важны состав и порядок колонок, SQL CHECK, nullable/defaults, типы, параметры FK, geometry и индексов. Функции/triggers проверяются отдельно на migrated DB. Проверка ORM round-trip должна читать результат через новую session, чтобы не принять объект из identity map за доказательство сохранения.

## Подходы для обсуждения

1. **Явные declarative models и независимые проверки против migrated PostgreSQL — предпочтительный подход.** Продолжает текущую организацию моделей; различия metadata и реальной схемы выявляются тестами в узком согласованном scope. Цена — отдельное описание CHECK в модели и необходимость тестировать его соответствие DDL.
2. **Reflection/automap для новых таблиц.** Уменьшает дублирование DDL, но делает получение моделей зависимым от доступной БД, усложняет статическую типизацию, offline metadata tests и текущую схему импортов Alembic. Для двух моделей это существенная смена существующего подхода.

Общий runtime-модуль с импортируемыми из него CHECK для старой migration не предлагается: изменение такого модуля могло бы изменить поведение уже существующей revision. Migration остаётся самостоятельным историческим артефактом.

### Согласованная структура моделей

Пользователь согласовал явные declarative models, следующую структуру и порядок записи.

- Добавить `EditVersionCommand` и `EditVersionChangeEvent` отдельными файлами в `models/work_order`; подключить exports и импорты Alembic.
- Добавить `EditVersion.draft_revision` как BIGINT с server default 1 и именованным положительным CHECK.
- Явно перенести типы, nullability, server defaults, имена и определения PK/FK/CHECK/UNIQUE/indexes из migration; не добавлять новых DB defaults.
- Использовать `JSONB(none_as_null=True)` для nullable `response_payload`.
- Применить существующий стиль Python enum + non-native `SAEnum` к state/event type, сохранив VARCHAR длины 16/32 и явные CHECK без дополнительных enum constraints.
- Оставить UUID history обычными полями без FK и ORM cascade; не добавлять новые relationships без потребности сценария записи/чтения.
- Для geometry history сохранить `LINESTRING`, SRID 4326, `spatial_index=False`; существующий GiST snapshot проверить на отсутствие дублей.
- ORM-сценарий явно выполняет `flush` running-команды, затем terminal command и обновлённого snapshot/root, затем INSERT history и общий commit. Это тест использования моделей, не реализация Save service.

## Согласованная матрица приёмки

Пользователь подтвердил следующую матрицу после согласования структуры моделей.

### 1. Metadata без подключения к БД

- Новые модели доступны через `work_order` exports и зарегистрированы в активной Alembic metadata. Проверка подключения не должна случайно проходить за счёт импорта моделей другим тестом.
- Для обеих новых таблиц проверяются точный набор колонок, типы и размеры, nullable, server defaults, имена PK, состав и порядок колонок PK/FK/UNIQUE/indexes. Для `EditVersion` проверяется новая колонка и CHECK при сохранении прежнего контракта.
- Проверяются определения CHECK, а не только их имена. Пробелы SQL не являются частью контракта; смысл предиката является.
- Registry содержит ровно два согласованных FK с `CASCADE` и `NO ACTION`; history не содержит FK.
- State/event type имеют согласованные значения и длины VARCHAR, без дополнительных native enum или автоматически созданных CHECK.
- Geometry history имеет тип LINESTRING, SRID 4326, двумерность и выключенный автоматический spatial index; у history отсутствуют явные spatial indexes. Snapshot сохраняет один ожидаемый GiST.
- `configure_mappers()` проходит без ошибок новых mappings; существующие точные тесты exports и списка колонок обновляются.

### 2. Соответствие реальной схеме

На БД, созданной Alembic, проверяются catalog/Inspector-сведения о тех же объектах: колонки, defaults, PK/FK/UNIQUE/CHECK, индексы и geometry typmod. Различия форматирования PostgreSQL, например приведения типов в defaults, не должны давать ложный drift.

Для новых таблиц проверяется полный согласованный контракт. Для существующих зависимостей — только ключи и ограничения, обеспечивающие registry/context/deletion, и spatial index snapshot. Это не аудит всех таблиц `Base.metadata`.

Физический PostgreSQL index для PK/UNIQUE не считается лишним явным `Index` модели: сравниваются соответствующие категории объектов. Отсутствие лишних FK/GiST истории проверяется явно. Функции и triggers имеют отдельные проверки наличия и поведения; они не должны появиться в ORM metadata.

### 3. ORM integration

Проверки выполняют реальные записи через `AsyncSession`, а результат читают из новой session после commit.

| Сценарий | Доказательство |
| --- | --- |
| Новая `EditVersion` | Revision 1 получена из БД; повторное открытие не увеличивает её |
| `running -> succeeded` с событием | UUID, JSON object, TIMESTAMPTZ, обе geometry и revisions сохраняются и читаются корректно; выполнены промежуточные flush без промежуточного commit |
| `running -> rejected` | `response_payload=None` записывает SQL NULL; rejection fields и terminal state читаются корректно |
| Access retry | Согласованный переход `rejected -> running -> terminal` проходит через ORM с очисткой старого результата |
| Commit незавершённой команды | Flush `running` допустим, настоящий commit отклоняется deferred trigger; после rollback запись отсутствует |
| Ошибка события | Ошибка INSERT history и rollback не оставляют изменённый snapshot/revision/command |
| Сохранившаяся история | После удаления associations/root и registry событие читается новой ORM session без существующих родителей |
| Изменение истории через ORM | UPDATE/DELETE отклоняются БД; модель не обходит append-only guards |

Для geometry проверяются SRID и точные координаты/EWKB, а не только топологическое равенство. Для SQL NULL используется проверка в БД: одно Python `None` после чтения не отличает SQL NULL от JSON null. Save/Revert service, fingerprint и HTTP replay здесь не реализуются; SQL-тесты Дня 2 сохраняются как независимые проверки схемы.

### 4. Upgrade/downgrade/upgrade

Основной цикл закреплён на revision `f8a7b6c5d4e3 -> b7d2e9f4a6c8 -> f8a7b6c5d4e3 -> b7d2e9f4a6c8`. Проверки запускаются на disposable DB; отдельный fresh upgrade до текущего head сохраняется.

1. На предыдущей revision существует заполненный snapshot с associations и baseline.
2. Первый upgrade сохраняет данные, добавляет revision 1; затем создаётся корректная command/history transaction.
3. Downgrade удаляет новые таблицы, функции/triggers, CHECK и колонку revision, сохраняя остальные поля и геометрию текущего snapshot, associations и baseline. Сравнение идёт с состоянием непосредственно перед downgrade, а не с baseline до изменения geometry.
4. Повторный upgrade восстанавливает структуру без дублей индексов/triggers; registry/history пусты, revision снова 1. Потеря новых command/history данных при downgrade — уже принятый контракт Дня 2, а не rollback бизнес-операции.
5. После повторного upgrade проверяются реальные guards: запрет commit `running`, допустимый command/event commit, отклонение неверного event context и запрет изменения history.

### 5. Конкурентная вставка history и удаление root

Два независимых соединения и реальные transaction boundaries. Для выделенной проверки event trigger используются заранее committed корректные command/snapshot/root без event; иначе ожидание может быть вызвано более ранним UPDATE root, а не проверяемым INSERT history.

- **INSERT первым:** незавершённый INSERT history удерживает блокировку root; конкурентное удаление ждёт. После commit INSERT удаление завершается, history остаётся неизменной, registry/snapshot удалены.
- **DELETE первым:** удаление root ещё не committed; INSERT history ждёт. После commit удаления INSERT отклоняется с `ck_ev_events_context`, новая history не возникает.

Проверяется полный контекст с associations. Тестовая transaction удаления сначала блокирует root, затем удаляет associations и root, сохраняя согласованный порядок блокировок. Создание production операции удаления не входит в задачу.

Ожидание доказывается наблюдаемым blocking state PostgreSQL, а не только задержкой `sleep`. Все ожидания ограничены timeout; ошибки фоновой задачи передаются тесту, соединения и транзакции закрываются при любом исходе. Deadlock или timeout не считаются успешной проверкой корректного ожидания.

### 6. Итоговый прогон

Новые metadata tests и существующие связанные unit tests, обычный backend suite с DB-тестами отключёнными, полный isolated DB suite через `infra/db-tests.cmd`, принятые Black/Ruff checks и проверка diff. Результаты фиксируются только после выполнения; текущий анализ не является отчётом об успешной проверке.

## Ограничения исследования и дальнейшей проверки

Код, migration и тесты пока не изменяются. DB integration tests допускаются только в disposable `geoservice-db-tests/geo_test` через `infra/db-tests.cmd` или эквивалентную изоляцию. Обычная demo-БД для downgrade и committed cleanup не используется.

Отдельная agent memory не создаётся: факты и основания уже сохранены в исходниках и документах Sprint 2; этот анализ сохраняет основания и согласованные уточнения без дублирования в memory.
