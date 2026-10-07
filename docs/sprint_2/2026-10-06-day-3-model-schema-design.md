# День 3 Sprint 2: соответствие моделей схеме

Дата: 6 октября 2026 года. Календарный день спринта: среда, 5 августа 2026 года.

Статус: письменная спецификация принята пользователем 7 октября 2026 года. [План реализации](2026-10-07-day-3-model-schema-plan.md) исполнен; результаты проверок и статус финального ревью описаны в [отчёте](2026-10-07-day-3-model-schema-implementation-report.md).

## 1. Цель и границы

Отразить схему первого сохранения Дня 2 в SQLAlchemy models и доказать соответствие metadata реальной PostgreSQL-схеме. Область работы: `EditVersion.draft_revision`, `work_order.edit_version_commands`, `work_order.edit_version_change_events` и непосредственные зависимости этих объектов.

Результат предназначен для последующей реализации Save/Revert: модели позволяют корректно сохранять command и history в одной transaction, не ослабляя ограничения БД.

В задачу входят declarative models, exports, подключение Alembic metadata, проверки структуры и ORM round-trip, полный upgrade/downgrade/upgrade и конкурентный INSERT history против удаления версии.

Не входят аудит всей `Base.metadata`, Save/Revert service, fingerprint, API/UI, новые операции удаления, spatial search по истории, retention и изменение принятого контракта Дня 2. Полноценную схему создаёт только Alembic. `Base.metadata.create_all()` не обязан создавать функции и triggers.

Основания:

- [Календарь Sprint 2](2026-07-31-sprint-2-calendar-plan.md).
- [Спецификация Дня 2](2026-10-01-day-2-first-save-schema-design.md) и [отчёт реализации](2026-10-01-day-2-first-save-schema-implementation-report.md).
- [Анализ текущего кода и согласованные ответы](2026-10-06-day-3-model-schema-analysis.md).
- [Migration b7d2e9f4a6c8](../../apps/backend/utility_service/infrastructure/postgresql/alembic/versions/b7d2e9f4a6c8_first_save_schema.py).

## 2. Текущее состояние и выбранный подход

Миграция уже содержит обе таблицы, revision, четыре функции и пять triggers. В ORM новые таблицы и `draft_revision` отсутствуют. Существующий metadata test фиксирует старый набор колонок `EditVersion`; exports также проверяются точным набором.

Активная цепочка migrations задана `apps/backend/alembic.ini` и находится в `utility_service/infrastructure/postgresql/alembic`. `env.py` явно импортирует модели и использует `Base.metadata`.

Выбран существующий подход: явные declarative models с независимой проверкой против migrated PostgreSQL. Reflection/automap отклонён: для двух таблиц он вводит зависимость построения моделей от доступной БД и усложняет автономные metadata tests. Цена выбранного подхода — отдельное описание CHECK в моделях; соответствие защищают проверки.

Migration остаётся самостоятельной. Она не импортирует CHECK и другие определения из изменяемого runtime-модуля. Изменения существующей revision не являются частью запланированной работы; обнаруженное противоречие сначала воспроизводится и оценивается относительно принятого контракта.

## 3. Модели и размещение

Все пути таблицы ниже относительны `apps/backend/utility_service/infrastructure/postgresql/`.

| Файл | Назначение |
| --- | --- |
| `models/work_order/edit_version.py` | Добавить `draft_revision` и CHECK |
| `models/work_order/edit_version_command.py` | Новые `EditVersionCommand`, `EditVersionCommandState` |
| `models/work_order/edit_version_change_event.py` | Новые `EditVersionChangeEvent`, `EditVersionChangeEventType` |
| `models/work_order/__init__.py` | Экспортировать новые классы и enums |
| `alembic/env.py` | Импортировать новые модели для target metadata |

Новые пути и имена классов в этой таблице являются проектируемыми. Существующие модели зависимостей не перестраиваются. Новые ORM relationships и cascade не вводятся: для записи и чтения достаточно явных UUID и запросов.

### Revision

`EditVersion.draft_revision`: `Mapped[int]`, `BigInteger`, NOT NULL, server default `1`; CHECK `ck_edit_versions_draft_revision_positive` с выражением `draft_revision >= 1`. Автоматическое увеличение при произвольном UPDATE и `onupdate` отсутствуют. Обновление `last_opened_at` не увеличивает revision. Дополнительный index по revision не создаётся.

### Registry

Таблица `work_order.edit_version_commands` содержит ровно 13 колонок:

| Колонки | Тип и форма |
| --- | --- |
| `command_id`, `edit_version_id`, `feature_id`, `actor_user_id` | UUID, NOT NULL |
| `request_fingerprint` | TEXT, NOT NULL |
| `state` | VARCHAR(16), NOT NULL |
| `retry_on_access_change` | BOOLEAN, NOT NULL, server default false |
| `response_status` | SMALLINT, nullable |
| `response_payload` | JSONB, nullable |
| `rejection_code`, `rejection_message` | TEXT, nullable |
| `created_at` | TIMESTAMPTZ, NOT NULL, server default now() |
| `completed_at` | TIMESTAMPTZ, nullable |

`command_id` передаётся явно; UUID не генерируется моделью. State также задаётся явно. Новые client defaults, скрывающие обязательные данные команды, не добавляются.

`EditVersionCommandState` имеет значения `running`, `succeeded`, `rejected`. Используется существующий стиль non-native `SAEnum`: `native_enum=False`, `create_constraint=False`, `validate_strings=True`, значения enum сохраняются через `values_callable`, длина 16.

Ограничения и индексы:

- PK `pk_edit_version_commands(command_id)`.
- FK `fk_ev_commands_edit_version(edit_version_id)` к `work_order.edit_versions.id`, `ON DELETE CASCADE`.
- FK `fk_ev_commands_feature(edit_version_id, feature_id)` к одноимённым колонкам `work_order.edit_version_features`, `ON DELETE NO ACTION`.
- CHECK `ck_ev_commands_fingerprint`, `ck_ev_commands_state`, `ck_ev_commands_result`, `ck_ev_commands_access_retry` с определениями из migration, включая явные проверки SQL NULL.
- B-tree `ix_ev_commands_version_feature(edit_version_id, feature_id)`.

Actor не получает FK. У nullable `response_payload` используется `JSONB(none_as_null=True)`: Python `None` означает SQL NULL. JSON null не удовлетворяет контракту `response_payload IS NULL` для `running/rejected`. Источник поведения типа: [SQLAlchemy JSON](https://docs.sqlalchemy.org/en/20/core/type_basics.html#sqlalchemy.types.JSON).

### History

Таблица `work_order.edit_version_change_events` содержит ровно 13 колонок, все NOT NULL:

| Колонки | Тип |
| --- | --- |
| `command_id`, `edit_version_id`, `work_order_id`, `default_state_id`, `feature_id`, `actor_user_id` | UUID |
| `event_type` | VARCHAR(32) |
| `before_geometry`, `after_geometry` | Geometry LINESTRING, SRID 4326, dimension 2, spatial_index=False |
| `base_network_revision` | INTEGER |
| `draft_revision_before`, `draft_revision_after` | BIGINT |
| `occurred_at` | TIMESTAMPTZ, server default now() |

Других server defaults нет. `command_id` совпадает с ID команды и передаётся явно. `EditVersionChangeEventType` содержит `change_set_persisted`, `change_set_cleared`; non-native `SAEnum` настроен аналогично registry с длиной 32.

Ограничения:

- PK `pk_edit_version_change_events(command_id)`.
- UNIQUE `uq_ev_events_version_revision(edit_version_id, draft_revision_after)`.
- CHECK `ck_ev_events_type`, `ck_ev_events_base_revision`, `ck_ev_events_draft_revisions`, `ck_ev_events_before_geometry`, `ck_ev_events_after_geometry`, `ck_ev_events_geometry_changed` с определениями из migration.

History не имеет FK, в том числе по `command_id`. Это позволяет сохранять события после удаления версии и registry. История не получает ORM cascade и spatial indexes. Два физических B-tree индекса PostgreSQL обслуживают PK/UNIQUE; в модели им соответствуют constraints, а не дополнительные `Index`.

## 4. Транзакционный контракт использования ORM

В тестовом сценарии одного фактического изменения:

1. Выбрать и заблокировать существующий root. Для нового изменения сохраняется порядок root → command → feature.
2. Создать `running` command и выполнить `flush`. Прямой INSERT terminal state запрещён trigger.
3. Обновить snapshot geometry/operation, draft revision и command до `succeeded` с полным результатом. Выполнить `flush` до добавления history.
4. Создать history, выполнить INSERT и общий commit.
5. Прочитать результат новой session.

Event trigger должен увидеть уже записанные terminal command и snapshot. Нельзя рассчитывать на порядок добавления объектов в session: history не имеет FK к registry. Промежуточный commit недопустим, поскольку deferred trigger запрещает сохранённый `running`.

Rejected command завершается без history. Access retry очищает прежние result fields, записывает переход в `running` через flush, затем завершает попытку в той же transaction. Эти сценарии проверяют ORM-контракт, не реализуют production Save service.

После ошибки flush/commit выполняется rollback; проверка новой session подтверждает отсутствие частичного результата. Модель не перехватывает и не подавляет DB errors, не подменяет triggers Python-валидацией. Доменное отображение ошибок в HTTP остаётся последующим дням.

## 5. Metadata и соответствие PostgreSQL

Автономные tests проверяют точный состав новых таблиц, типы/размеры, nullable/defaults, определения CHECK, имена и порядок колонок PK/FK/UNIQUE/indexes, FK actions, параметры geometry и отсутствие лишних FK/spatial indexes. `configure_mappers()` должен проходить; точные tests exports и колонок `EditVersion` обновляются.

Подключение моделей в Alembic проверяется независимо от случайного порядка pytest imports: предварительный импорт модели другим тестом не должен скрыть её отсутствие в `env.py`.

На migrated DB catalog/Inspector-проверки сопоставляют те же свойства с metadata и контрактом. Проверка только имён constraints или пустой autogenerate diff не является полным доказательством. CHECK проверяются по определениям и существующим поведенческим SQL-сценариям. Нормализация SQL учитывает форматирование PostgreSQL, не стирая различия операторов, литералов или NULL-предикатов.

PK/UNIQUE backing indexes учитываются отдельно от явно объявленных indexes. Defaults сравниваются с учётом эквивалентных представлений PostgreSQL, например приведения литерала 1 к BIGINT; поведение default дополнительно подтверждает INSERT.

Для непосредственных зависимостей проверяются ключи, необходимые composite FK registry, ограничения удаления associations/features и существующий GiST `ix_edit_version_features_geometry`. Контекстные ссылки history на WorkOrder/DefaultState остаются значениями, проверяемыми trigger при INSERT; из них не выводятся новые FK.

Функции и triggers остаются отдельным migration-контрактом: четыре функции (`guard_edit_command_transition`, `ensure_edit_command_terminal`, `validate_edit_change_event`, `reject_edit_change_event_mutation`) и пять triggers (`tr_ev_commands_transition`, `tr_ev_commands_terminal`, `tr_ev_events_context`, `tr_ev_events_immutable`, `tr_ev_events_no_truncate`). Проверяется deferred-свойство terminal trigger. Эти объекты не добавляются в declarative metadata.

## 6. ORM integration tests

| Сценарий | Критерий |
| --- | --- |
| Создание версии | Default draft revision равен 1; обновление last_opened_at не меняет его |
| Success + history | После commit новая session читает UUID, JSON object, даты, geometry и revisions без потерь |
| Rejected | Python None сохранён как SQL NULL; terminal result читается корректно |
| Access retry | Переход rejected → running → terminal проходит с очисткой полей и сохранением identity |
| Незавершённая команда | Flush проходит, настоящий commit отклоняется deferred trigger; после rollback строки нет |
| Ошибка event | Snapshot/revision/command откатываются вместе; history не появляется |
| Удаление родителей | После удаления associations/root registry исчезает, history читается ORM и не меняется |
| UPDATE/DELETE history | БД отклоняет mutation через ORM; история сохраняется |

Не используется только identity map той session, которая записывала объекты. Для nullable payload выполняется SQL `IS NULL`: Python None при чтении не различает SQL NULL и JSON null. Geometry проверяется по SRID и точным координатам/EWKB, а не одному топологическому равенству. SQL-тесты Дня 2 сохраняются как независимое покрытие ограничений, включая TRUNCATE.

## 7. Migration lifecycle

Основной цикл фиксирован: `f8a7b6c5d4e3 → b7d2e9f4a6c8 → f8a7b6c5d4e3 → b7d2e9f4a6c8`. Отдельная проверка fresh upgrade до head сохраняется.

До первого upgrade создаются existing version, features, associations и baseline. Upgrade сохраняет данные и добавляет revision 1. Далее выполняется корректное изменение с command/history, и фиксируется состояние непосредственно перед downgrade.

Downgrade удаляет обе новые таблицы, их triggers, четыре функции, CHECK и колонку draft revision. Остальные поля root, текущий snapshot, associations и baseline сохраняются. Downgrade не возвращает geometry к исходному baseline.

Повторный upgrade восстанавливает объекты без дублей; registry/history пусты, revision снова 1. Это проверка принятой потери command/history при downgrade, а не восстановление удалённой истории.

После повторного upgrade проверяются: корректный command/event commit, запрет commit running, отклонение неверного event context и append-only. Новое событие использует актуальную geometry snapshot как before_geometry; нельзя повторять fixture так, чтобы before/after случайно совпали или описывали прежнее состояние.

Тест восстанавливает head при завершении и закрывает соединения до DDL. Новые migration tests не должны зависеть от порядка выполнения относительно ORM tests.

## 8. Конкурентный INSERT history и удаление версии

Два соединения выполняют независимые реальные transactions. Для выделенной проверки INSERT trigger заранее committed корректные root/snapshot/succeeded command без события. Это изолирует блокировку INSERT от более раннего UPDATE root внутри Save transaction; полноценная атомарная запись проверяется отдельно.

Fixture содержит associations. Удаляющая transaction сначала блокирует root, затем удаляет associations и root; существующие FK с RESTRICT учитываются явно.

| Очередность | Ожидаемое поведение |
| --- | --- |
| INSERT history первым | Незавершённая вставка удерживает root; удаление ждёт. После commit вставки удаление завершается, history сохраняется неизменной, root/registry/snapshot исчезают |
| DELETE root первым | До commit удаления INSERT ждёт. После commit удаления INSERT отклоняется с SQLSTATE 23514 и `ck_ev_events_context`; нового события нет |

Blocking state подтверждается PostgreSQL, например через `pg_blocking_pids`, с ограниченным ожиданием. Один sleep не доказывает блокировку. У каждой операции есть deadline; ошибки фоновых задач передаются тесту, transactions/соединения закрываются при любом исходе. Deadlock и timeout являются провалом проверки.

## 9. Размещение проверок и итоговая приёмка

Существующий `utility_service/infrastructure/tests/test_network_model_metadata.py` сохраняет проверки старых моделей и получает необходимые изменения exports/revision. Новое сфокусированное metadata-покрытие размещается рядом. DB parity, ORM и concurrency tests размещаются в `apps/backend/tests/integration_tests`; lifecycle расширяет существующий `test_first_save_schema_migration.py`. Общие SQL fixtures остаются независимыми от новых ORM models.

Приёмка требует всех следующих результатов:

1. Metadata отражает согласованный DDL новых объектов и связи с непосредственными зависимостями.
2. Новые модели загружаются активным Alembic env и работают через ORM с настоящим commit.
3. Lifecycle доказывает удаление и восстановление объектов и защит при сохранении snapshot/baseline.
4. Обе конкурентные очередности проходят без deadlock и ложного успеха из-за timeout.
5. Связанные metadata tests, обычный backend suite с DB-тестами отключёнными и полный isolated DB suite проходят; выполняются принятые Black/Ruff checks и проверка diff.

Все DB tests выполняются только через `infra/db-tests.cmd` или эквивалентный isolated Compose `geoservice-db-tests` с disposable `geo_test`. Demo-БД не используется для downgrade и committed cleanup.

## 10. Статус проверки документа

Выполнена самостоятельная проверка согласованности scope, defaults, FK/индексов истории, порядка flush, семантики downgrade и конкурентных ожиданий. Требования из обсуждения сохранены; продуктовый код и tests не изменялись и не запускались в рамках подготовки спецификации. Этот документ не подтверждает успешную реализацию.

Отдельная agent memory и repository-change ingest не нужны: решения и причины сохранены в документах Sprint 2. Изменения остаются unstaged; staging, commit и push выполняет только пользователь.
