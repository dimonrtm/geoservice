# День 2 Sprint 2: анализ схемы первого сохранения

Дата анализа: 1 октября 2026 года. День календарного плана: вторник, 4 августа 2026 года.

Статус: исследование и обсуждение завершены, [спецификация Дня 2](2026-10-01-day-2-first-save-schema-design.md) принята, [план реализации](2026-10-01-day-2-first-save-schema-plan.md) выполнен. Результаты — в [отчёте](2026-10-01-day-2-first-save-schema-implementation-report.md). Остальной текст сохраняет ход обсуждения и состояние на момент исследования; актуальный контракт находится в спецификации.

## Цель и границы

Подготовить схему для первого synchronous Save: `draft_revision` в `EditVersion`, durable command registry, append-only change event history, ограничения, индексы и связи. Существующий current snapshot не получает отдельную колонку baseline geometry.

Календарь отделяет migration Дня 2 от SQLAlchemy models и проверки соответствия metadata Дня 3. Save transaction, fingerprint, API и UI относятся к следующим дням. В текущем обсуждении исследуется их влияние на схему; реализация не начата.

## Проверенные источники

- [ТЗ](2026-07-31-sprint-2-technical-requirements.md), разделы 4, 7–11 и 17.
- [Календарь](2026-07-31-sprint-2-calendar-plan.md), дни 2–8.
- [EditVersion](../../apps/backend/utility_service/infrastructure/postgresql/models/work_order/edit_version.py).
- [EditVersionFeature](../../apps/backend/utility_service/infrastructure/postgresql/models/work_order/edit_version_feature.py).
- [Исходная migration](../../apps/backend/utility_service/infrastructure/postgresql/alembic/versions/a8c1f2d3e4b5_edit_versions.py).
- [WorkOrderRepository](../../apps/backend/utility_service/infrastructure/postgresql/repositories/work_order_repository.py).
- [EditVersionService](../../apps/backend/utility_service/use_cases/services/edit_version_service.py).
- [Alembic env](../../apps/backend/utility_service/infrastructure/postgresql/alembic/env.py), [alembic.ini](../../apps/backend/alembic.ini).
- [Migration tests](../../apps/backend/tests/integration_tests/test_edit_version_migration.py).
- [Изоляция DB tests](../../apps/backend/tests/db_test_isolation.py), [объяснение ограничения](../agent-memory/bugfixes/2026-06-28-ci-smoke-401-seed-cleanup.md).
- [DDD aggregate](../../DDD_Wiki/aggregates/edit_version.md), [доменная команда](../../Wiki/commands/update_edit_version_feature_geometry.md).

## Что уже реализовано

| Область | Наблюдение в коде | Значение для схемы |
| --- | --- | --- |
| `EditVersion` | UUID PK, `base_network_revision` типа Integer с default 1 и положительным CHECK; `draft_revision` отсутствует | Network revision и draft revision имеют разный смысл; подмена существующего поля не соответствует ТЗ |
| Lifecycle | Единственное разрешённое состояние `open`; partial unique index ограничивает одну открытую версию на WorkOrder | Будущие lifecycle checks ещё не реализованы |
| Связи root | `work_order_id` имеет FK с `RESTRICT`; `default_state_id` и `owner_user_id` — UUID без FK | Наличие UUID в существующей модели не доказывает DB referential integrity |
| Current features | Составной PK `(edit_version_id, feature_id)`, FK к root с `CASCADE`; geometry, properties, network_version и operation | `feature_id` нельзя считать глобально уникальным ключом строки snapshot |
| Геометрия snapshot | PostGIS `GEOMETRY`, SRID 4326, CHECK для empty/valid/type и GiST index | Физический snapshot содержит разные типы features, хотя Save Sprint 2 ограничен линией |
| Создание версии | Repository копирует geometry и properties из DefaultState в current rows, сохраняя feature identity | Уже существующая начальная копия current geometry не является новой отдельной колонкой baseline |
| Открытие | Service использует transaction и блокировку WorkOrder; повторное открытие обновляет `last_opened_at` | Это готовая операция открытия, но не реализация Save и блокировки EditVersion |
| Workspace | SQL aggregate и repository mapping возвращают base network revision, features, associations; draft token в mapping отсутствует | Добавление колонки само по себе не расширит readback API |
| Alembic | Активный путь — `utility_service/infrastructure/postgresql/alembic`; по статической цепочке последняя revision — `f8a7b6c5d4e3` | Старые ссылки памяти на `app/alembic` не являются актуальным местом новой migration |
| DB tests | Migration tests используют upgrade/downgrade и проверяют constraints/indexes; isolation guard требует отдельный `TEST_DATABASE_URL` с `_test` | Эти проверки нельзя запускать против пользовательской demo-БД |

## Требования, уже заданные ТЗ

- `draft_revision`: положительный `BIGINT`, старт `1`, API token — opaque string.
- Content-changing Save/Revert увеличивает revision на 1. No-op и idempotent retry не увеличивают её.
- `commandId`: глобально уникальный UUID. Повтор того же содержимого возвращает сохранённый terminal result; другой fingerprint отклоняется.
- Registry содержит идентификаторы команды, версии и feature, actor, fingerprint, state `running|succeeded|rejected`, terminal result и timestamps.
- History содержит связь с версией и командой, type `change_set_persisted|change_set_cleared`, feature, actor, before/after geometry, base network revision, draft revisions и время.
- На одну команду приходится не более одного change event; no-op и retry событий не создают.
- Snapshot, revision, event и terminal result сохраняются атомарно.
- Baseline остаётся в `utility_network.default_state_features`; долгосрочная retention automation вне Sprint 2.

## Неоднозначности, влияющие на схему

1. **Граница durable rejection — уточнена для существования и доступа.** Если версия или feature отсутствует, пользователь считает команду невыполнимой, а не отклонённой: registry не записывается и `CommandId` не резервируется. Если объект существует, но недоступен пользователю, отказ сохраняется в registry. Это уточняет общее правило ТЗ о сохранении domain rejection после входа в use case. Публичная ошибка не должна раскрывать существование недоступного объекта; наличие внутренней записи не предоставляет доступ к нему.
2. **Порядок retry и stale check.** В последовательности ТЗ token проверяется до распознавания выполненной команды. После успешного Save исходный token уже устарел. Пользователь подтвердил: повтор уже успешной команды возвращает её исходный successful response без повторной mutation. Следовательно, устаревший token исходного запроса не должен мешать replay; проверка актуальности token остаётся необходимой перед новой mutation, включая повтор после отказа из-за прав.
3. **Append-only и удаление root — требования уточнены.** БД должна разрешать `INSERT` событий и запрещать обычные `UPDATE`, `DELETE` и `TRUNCATE` истории. Пользователь не допускает запрета физического удаления `EditVersion` из-за наличия истории. Совместное следствие требований: события должны переживать удаление root; обычный обязательный FK с `RESTRICT` или `CASCADE` не удовлетворяет обоим требованиям. Конкретный механизм связи и защиты пока не выбран; защита от администратора, способного изменить саму схему или отключить защиту, не заявлена. Current rows сейчас удаляются каскадно, а integration cleanup явно удаляет `EditVersion`.
4. **Точный terminal result — уточнён для error replay.** При повторе сохранённого отказа воспроизводятся HTTP-статус, `code` и `message`, а `correlationId` берётся из текущего HTTP-запроса. Идентификатор запроса не является неизменной частью результата команды. Для связи повторов в логах используется `CommandId`. Отказ из-за прав по-прежнему требует повторной проверки доступа.
5. **Расхождение wiki и ТЗ — разрешено для retry и stale.** Окончательное уточнение пользователя для retry успешной команды: возврат исходного successful response, включая исходные geometry и revision, в соответствии с ТЗ. Для новой команды с устаревшим token также сохраняется правило ТЗ: строгая ошибка `{code,message,correlationId}` с `DRAFT_VERSION_STALE`, затем отдельное чтение workspace. Актуальные geometry/token не добавляются в error body. Wiki пока не изменена.
6. **Состояние `running` — уточнено для сбоя.** Если backend падает посреди Save до commit, вся попытка откатывается, незавершённая запись `running` не остаётся. Повтор с тем же `CommandId` может выполнить команду заново. Для повторной попытки после уже сохранённого отказа rollback не удаляет ранее committed отказ; откатываются изменения текущей попытки.
7. **Целостность истории.** Нужно определить требуемый уровень DB-гарантий согласованности event с command: одна версия, feature и actor, successful state, последовательность revision. Отдельные FK сами по себе не обеспечивают все эти свойства.
8. **Fingerprint.** Wiki включает baseline identity, token, operation, vertex, structure hash и canonical geometry. Для invalid geometry/structure не определена граница вычисления fingerprint, хотя такие отказы должны быть воспроизводимыми.
9. **Обновление существующей БД — уточнено.** Migration сохраняет существующие `EditVersion` и их geometry, присваивая версиям начальный `draft_revision = 1`. Следствие для проверки: одного upgrade на чистой БД недостаточно; нужен upgrade с существующими версиями и проверкой сохранности данных. Начальный revision не означает фактическое изменение geometry и сам по себе не является Save.

## Что ещё предстоит определить

После ответов на вопросы можно конкретизировать nullability, PK/FK, delete policy, terminal result storage, CHECK/UNIQUE constraints, необходимые запросам индексы и защиту истории. Наличие GiST у current snapshot само по себе не обосновывает spatial indexes на исторических before/after geometry: для них пока не задан spatial query.

Migration upgrade на чистой БД доказывает применимость DDL, но не доказывает replay, атомарность Save или append-only поведение. Эти свойства потребуют соответствующих проверок на следующих этапах; границы проверки Дня 2 будут согласованы отдельно.

## Проверки и сохранение знаний

Выполнено статическое чтение кода, migration chain, тестов и требований. БД не изменялась, migration и тесты не запускались. Принятые уточнения сохранены ниже. Отдельная запись agent memory не нужна: основания, решения и открытые вопросы сохранены в этом документе.

## Принятые уточнения

- Registry сохраняется весь срок жизни `EditVersion`. При физическом удалении версии её записи registry тоже удаляются. Периодическая очистка в Sprint 2 не требуется; закрытие версии без физического удаления само по себе не согласовано как основание очистки.
- Если версия или feature отсутствует, команда считается невыполнимой и не сохраняется в registry. Такая попытка не резервирует `CommandId`; новое состояние `rejected` для неё не создаётся.
- Если версия и feature существуют, но недоступны пользователю, отказ сохраняется в registry.
- При повторе команды, ранее отклонённой из-за недоступности, права проверяются заново. Нельзя автоматически возвращать прежний отказ только на основании registry. Если доступ появился, команда с тем же `CommandId` выполняется при актуальном token и прохождении остальных проверок. Это исключение из общего требования ТЗ о неизменном terminal rejection при retry. Новый payload под прежним `CommandId` этим решением не разрешён.
- Registry хранит последний результат команды. Если после отказа из-за прав команда успешно выполнилась, предыдущий отказ не требуется сохранять для аудита. Отдельная история попыток не требуется; append-only history фактических изменений геометрии этим решением не отменяется.
- Append-only история защищается самой БД: добавление новых событий через `INSERT` разрешено, обычные `UPDATE`, `DELETE` и `TRUNCATE` запрещены. Revert добавляет новое событие, а не изменяет старое. Registry команд остаётся обновляемым. Это согласованное требование; migration ещё не реализована.
- Наличие событий истории не должно запрещать физическое удаление `EditVersion`. Запрет удаления самих событий не отменён. Следствие для дизайна: история должна сохраняться после удаления версии; способ сохранения ссылочной информации ещё не выбран.
- При физическом удалении `EditVersion` удаляется и её command registry, но события истории сохраняются. Следствие: связи history с root и command не должны блокировать их удаление, каскадно удалять события или изменять записанные события. Конкретная схема связей будет выбрана после уточнений.
- Повтор уже успешной команды возвращает её исходный successful response. Пример: A сохранила revision 2, B затем сохранила revision 3; retry A возвращает geometry A и revision 2. Current snapshot остаётся на geometry B и revision 3. Повтор не применяет payload A заново, не увеличивает revision и не добавляет событие. Это окончательное уточнение заменяет ранее обсуждавшийся возврат актуального состояния. «Последний результат команды» в registry не означает результат более поздней другой команды.
- Новая команда с устаревшим token получает `DRAFT_VERSION_STALE` в существующем формате `{code,message,correlationId}`. После ошибки клиент отдельно перечитывает workspace; актуальные geometry и revision не включаются в error body. Автоматический повтор Save после stale этим решением не разрешён.
- Migration сохраняет уже существующие `EditVersion` и их geometry, присваивая каждой версии начальный `draft_revision = 1`. Требуется проверить upgrade на чистой БД и на БД с существующими данными; эти проверки ещё не выполнялись.
- При падении backend посреди Save до commit вся попытка откатывается без зависшего `running`; повтор с тем же `CommandId` может выполнить команду заново. Ранее committed данные при этом сохраняются.
- При replay сохранённого отказа HTTP-статус, `code` и `message` воспроизводятся из registry, а `correlationId` соответствует текущему HTTP-запросу. Повторы связываются по `CommandId`; диагностический ID не входит в неизменный результат команды.
- Для отказов, не связанных с правами доступа, сохраняется правило ТЗ: тот же `CommandId` и тот же payload возвращают сохранённый отказ без повторной проверки; исправленная geometry или новый token требуют нового `CommandId`. Исключение для повторной проверки относится к отказу из-за прав, а не ко всем состояниям `rejected`.

## Сопоставление вариантов схемы

Основные требования к поведению уточнены. Пользователь выбрал вариант 1: самостоятельные события с проверкой ссылок при добавлении. Вариант 2 сохранён как рассмотренная альтернатива. Детальная структура ещё не согласована.

### Общее для вариантов

- Migration расширяет root положительным `BIGINT draft_revision NOT NULL DEFAULT 1`, сохраняя existing snapshot.
- Registry имеет глобальный PK `command_id`, связь с `EditVersion` с удалением вместе с версией, target feature, actor, fingerprint, state, response/rejection и timestamps. Требуется различать повторно проверяемый отказ из-за прав и остальные отказы.
- Обе новые таблицы располагаются в существующей PostgreSQL schema `work_order`: `work_order.edit_version_commands` и `work_order.edit_version_change_events`, как указано в ТЗ. Поле `draft_revision` добавляется в `work_order.edit_versions`. Baseline остаётся в `utility_network.default_state_features`; отдельная schema истории не вводится.
- History хранит исходные идентификаторы, before/after geometry и revisions. Добавление события выполняется в одной transaction с mutation и результатом команды. Один `CommandId` не должен порождать более одного события.
- Защитные triggers отклоняют изменение и удаление событий; отдельно запрещается `TRUNCATE`. Это защита от обычного DML, не от администратора, изменяющего саму схему.
- `ON DELETE SET NULL` непосредственно в history не соответствует требованию неизменности событий: оно изменяет записанное поле. `CASCADE` удаляет историю, а `RESTRICT` препятствует удалению версии. Поэтому постоянный FK из history прямо на удаляемые root/command не подходит.

### Вариант 1: самостоятельные события и проверка ссылок при добавлении — выбран

History сохраняет неизменные `edit_version_id`, `command_id`, `feature_id` и actor как исторические идентификаторы без постоянных FK на удаляемые строки. При добавлении события DB trigger проверяет существование и согласованность версии, команды и feature. После удаления версии и registry старые события остаются в прежнем виде.

Преимущества: две новые таблицы согласно объёму дня; нет дополнительных архивных сущностей; проверка корректности ссылок при записи остаётся в БД. Цена: часть целостности выражена trigger-кодом, а не обычными FK. В детальном дизайне необходимо определить порядок записи и блокировки, чтобы insert history и удаление root не создавали гонку. Проверка существования только обычным SELECT без согласования конкурентных операций недостаточна.

### Вариант 2: отдельные сохраняемые записи исторических идентичностей

Кроме registry и history вводятся архивные записи идентичности версии и команды. Они переживают удаление рабочих root/registry; history ссылается на них постоянными FK. Archive хранит идентификаторы и необходимый контекст, а не дополнительную копию baseline geometry.

Преимущества: постоянная ссылочная целостность history выражается FK. Цена: дополнительные таблицы и отдельные правила их создания и неизменности; объём Дня 2 растёт. Существование архивной идентичности само по себе ещё не доказывает корректность Save — согласованность с рабочей командой всё равно нужно обеспечивать.

Рекомендация: вариант 1 лучше соответствует ограниченному объёму Sprint 2 и разрешённому физическому удалению рабочих данных. Вариант 2 оправдан, если постоянные FK для архивных идентичностей являются самостоятельным требованием.

### Основания и последствия для проверки

В PostgreSQL действия FK, включая `ON DELETE SET NULL`, вызывают соответствующие triggers; `TRUNCATE` поддерживает statement-level trigger. См. [CREATE TRIGGER](https://www.postgresql.org/docs/current/sql-createtrigger.html) и [Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html).

Помимо fresh upgrade и upgrade с existing data, потребуются DB-проверки: допустимый INSERT события; запрет UPDATE/DELETE/TRUNCATE; удаление версии вместе с registry при сохранении событий; отказ при несовместимых идентификаторах события; отсутствие дубля события на `CommandId`. Lifecycle и конкурентные проверки Save относятся к последующим дням, но структура должна их поддерживать.

Существующий `infra/db-tests.cmd` запускает отдельный disposable Compose-проект. Текущие migration tests выполняют downgrade/upgrade, а cleanup ряда integration tests удаляет `EditVersion`. Новая история должна учитываться при изоляции тестовых данных: cleanup через DELETE history противоречит принятому контракту. Проверки migration/downgrade выполняются только на disposable БД.

## Следующий шаг обсуждения

Подход к связям history, все три раздела и цельная спецификация согласованы. План реализации подготовлен для просмотра и выбора способа выполнения. Migration пока не создана.

## Согласованный дизайн, раздел 1: root и registry

Статус раздела: согласован пользователем; реализация не начата.

### Revision root

В `work_order.edit_versions` добавляется `draft_revision BIGINT NOT NULL DEFAULT 1` и именованный CHECK `draft_revision >= 1`. Default сохраняется для будущих INSERT, в том числе выполняемых текущим кодом до добавления ORM-поля в День 3. Existing rows получают 1, snapshot и baseline не переписываются. Отдельный index по revision не нужен: Save находит и блокирует root по существующему UUID PK.

Увеличение revision выполняет Save transaction только при content-changing mutation. Не вводится trigger, увеличивающий revision при любом UPDATE root: существующий `touch_edit_version()` обновляет `last_opened_at`, что не должно изменять draft token.

### Поля `work_order.edit_version_commands`

| Поле | Тип и обязательность | Назначение |
| --- | --- | --- |
| `command_id` | UUID, PK | Глобальная уникальность среди записей registry |
| `edit_version_id` | UUID, NOT NULL | Владелец команды |
| `feature_id` | UUID, NOT NULL | Target feature внутри версии |
| `actor_user_id` | UUID, NOT NULL | Идентичность автора команды |
| `request_fingerprint` | TEXT, NOT NULL, непустое | Сравнение содержимого запроса; формат вычисления относится к Дню 4 |
| `state` | VARCHAR(16), NOT NULL, CHECK | `running`, `succeeded`, `rejected` |
| `retry_on_access_change` | BOOLEAN, NOT NULL, DEFAULT false | Только отказ из-за прав допускает повторную проверку |
| `response_status` | SMALLINT, nullable | HTTP-статус завершённой попытки |
| `response_payload` | JSONB, nullable | Исходный successful response целиком |
| `rejection_code` | TEXT, nullable | Код отказа |
| `rejection_message` | TEXT, nullable | Человекочитаемая причина отказа |
| `created_at` | TIMESTAMPTZ, NOT NULL, DEFAULT now() | Время первой регистрации |
| `completed_at` | TIMESTAMPTZ, nullable | Время завершения последней выполненной попытки |

`correlationId` не является сохранённым полем результата: error handler получает его из текущего запроса. Payload успешного ответа хранится ради replay исходного результата, включая geometry и token. Это копия результата команды, а не новая baseline geometry в current snapshot.

### Ограничения registry

- FK `edit_version_id -> work_order.edit_versions.id` с `ON DELETE CASCADE`.
- Составной FK `(edit_version_id, feature_id)` к существующему составному ключу `edit_version_features` с `NO ACTION`: нельзя записать команду для feature другой версии или отсутствующей feature. Самостоятельное удаление target feature с registry не является операцией Sprint 2. Удаление всего root должно удалить registry и snapshot; этот сценарий проверяется integration test с учётом существующих associations.
- `actor_user_id` сохраняется как UUID без нового cross-context FK, аналогично `owner_user_id` существующей версии. Проверка аутентифицированного actor остаётся на границе приложения.
- Идентичность команды — `command_id`, версия, feature, actor и fingerprint — не меняется при повторе. Другой actor не получает сохранённый ответ чужой команды по известному UUID; текущий доступ проверяется перед раскрытием результата.
- Для `running` результат и `completed_at` отсутствуют, `retry_on_access_change = false`.
- Для `succeeded` обязательны успешный HTTP-статус, JSON object payload и `completed_at`; rejection fields отсутствуют, `retry_on_access_change = false`.
- Для `rejected` обязательны HTTP error status, непустые code/message и `completed_at`; successful payload отсутствует. Признак повторной проверки допустим только для отказа из-за доступа. Точный набор access error codes закрепляется при согласовании error classification.
- CHECK-ограничения явно проверяют NULL/non-NULL для каждой ветки state. Нельзя полагаться только на SQL-сравнения nullable полей.
- PK обслуживает поиск по `command_id`. Дополнительный B-tree index `(edit_version_id, feature_id)` обслуживает связь с target и удаление registry вместе с root. Отдельные индексы на state, actor, timestamps и JSONB без сценария чтения не добавляются.

### Переходы и повтор

- Новая выполнимая попытка проходит `running -> succeeded|rejected` внутри одной transaction. Commit промежуточного `running` не входит в контракт; никакого отдельного commit для резервирования ID нет.
- Для ранее сохранённого отказа из-за прав при появлении доступа допускается новая попытка под прежней идентичностью команды. Она заменяет результат, сохраняя `created_at`; первоначальный отказ отдельно не архивируется. При rollback новой попытки прежний committed результат остаётся.
- Повтор `succeeded` возвращает исходный response и не выполняет mutation. Повтор обычного `rejected` возвращает прежний status/code/message с новым request correlation ID.
- Отказ в текущем доступе к уже успешной команде не должен стирать доказательство её выполнения или разрешать повторную mutation. HTTP-запрет на выдачу результата не переводит `succeeded` обратно в повторно выполняемое состояние.
- После физического удаления root registry больше не обеспечивает replay старых команд. История content-changing commands остаётся; обработка попытки повторного использования исторического `CommandId` должна учитывать её уникальность и будет описана вместе с events.

Предлагаемые поля и ограничения ещё не реализованы. DB-защита неизменности идентичности и допустимых переходов будет конкретизирована вместе с trigger-дизайном; таблица выше не означает, что обычные CHECK сами проверяют переходы между строковыми версиями.

## Согласованный дизайн, раздел 2: история событий

Статус раздела: согласован пользователем; реализация не начата.

### Поля `work_order.edit_version_change_events`

Все перечисленные поля обязательны; событие является полной записью фактического изменения geometry.

| Поле | Тип | Назначение |
| --- | --- | --- |
| `command_id` | UUID, PK | Идентификатор события совпадает с идентификатором единственной породившей его команды |
| `edit_version_id` | UUID | Историческая идентичность версии |
| `work_order_id` | UUID | Контекст рабочей задачи, сохраняемый после удаления версии |
| `default_state_id` | UUID | Идентичность baseline без копирования baseline geometry |
| `feature_id` | UUID | Идентичность изменённой feature |
| `actor_user_id` | UUID | Идентичность автора изменения |
| `event_type` | VARCHAR(32) | `change_set_persisted` или `change_set_cleared` |
| `before_geometry` | geometry(LINESTRING, 4326) | Current geometry непосредственно перед mutation |
| `after_geometry` | geometry(LINESTRING, 4326) | Current geometry после mutation |
| `base_network_revision` | INTEGER | Базовая network revision, соответствующая типу существующего root |
| `draft_revision_before` | BIGINT | Draft revision перед mutation |
| `draft_revision_after` | BIGINT | Draft revision после mutation |
| `occurred_at` | TIMESTAMPTZ, DEFAULT now() | Время события |

Отдельный `event_id` не нужен: контракт допускает не более одного события на `CommandId`, что выражается PK. `work_order_id` и `default_state_id` — предложенные дополнительные поля контекста, чтобы после удаления root не терялась связь истории с рабочей задачей и baseline. Имена пользователей и полные WorkOrder snapshots не копируются.

`before_geometry` — не обязательно baseline: после A команда B должна сохранить переход от geometry A к geometry B. Revert записывает переход от последнего current state к baseline. No-op, retry и отказ не создают события.

### Локальные ограничения и индексы

- CHECK на два допустимых `event_type`.
- Обе draft revisions положительны; `draft_revision_after > draft_revision_before` и их разность равна 1. Base network revision положительна.
- UNIQUE `(edit_version_id, draft_revision_after)` не допускает два события для одной новой revision версии и поддерживает чтение её истории по revision.
- PostGIS type фиксирует LineString и SRID 4326. CHECK запрещает empty/invalid/non-simple geometry с обеих сторон перехода.
- Before и after должны отличаться по сохранённым координатам. Для точного сравнения предлагается EWKB, а не топологическое равенство: topology equality не равнозначно совпадению последовательности координат.
- Пространственные индексы на before/after не добавляются: в Sprint 2 нет spatial search по history. Также не дублируется B-tree prefix `edit_version_id`, уже покрытый UNIQUE index.

### Проверка ссылок при INSERT

Постоянные FK из history на удаляемые строки отсутствуют. BEFORE INSERT trigger проверяет, что версия и команда существуют, команда имеет `succeeded`, её version/feature/actor совпадают с событием, target feature существует в этой версии. `work_order_id`, `default_state_id` и base network revision сверяются с root; `draft_revision_after` — с текущим revision root; `after_geometry` — с current snapshot.

Trigger сначала блокирует root, затем проверяет и блокирует связанную команду в согласованном с Save порядке. Блокировки удерживаются до завершения transaction. Это исключает разрыв между проверкой существования и конкурентным удалением рабочих данных. Детальные SQL lock modes и конфликтные сценарии проверяются при реализации.

Чтобы событие не ссылалось на `running`, порядок внутри будущей Save transaction уточняется: обновить snapshot и revision, записать successful result команды, добавить event, затем commit. Если event отклонён, откатываются и результат команды, и mutation. Этот внутренний порядок не делает success видимым раньше события. Для no-op success записывается без event.

Граница DB-проверки: insert trigger подтверждает контекст и состояние после mutation, но не может восстановить прежнюю geometry из уже обновлённого snapshot. Корректность `before_geometry`, полнота записи событий для каждого Save и геометрические бизнес-правила проверяются Save integration tests; данный trigger не заменяет реализацию Save и не обещает защиту от произвольного ручного изменения всех рабочих таблиц.

### Защита существующих событий

- BEFORE UPDATE и BEFORE DELETE row triggers завершают операцию ошибкой, не меняя событие.
- BEFORE TRUNCATE statement trigger запрещает очистку таблицы.
- Прямой INSERT остаётся возможным только при выполнении CHECK/UNIQUE и проверки контекста.
- Удаление root удаляет registry, current features и associations в согласованной операции. Оно не изменяет history: все исходные UUID и geometry события сохраняются.
- После удаления root/registry новый event для отсутствующей версии или команды не пройдёт INSERT guard. Старое событие по `command_id` остаётся уникальным.

Требование к жизненному циклу UUID: после удаления registry replay старой команды не поддерживается. История позволяет распознать повторное использование ID content-changing команды; новый запрос с таким ID не должен выполнять mutation и должен получить `COMMAND_ID_REUSED`. Удалённые no-op/rejected команды история не хранит, поэтому вечная проверка всех когда-либо использованных UUID невозможна в выбранной политике очистки. Клиент продолжает генерировать новый UUID для каждой новой логической команды; бессрочный реестр всех использованных UUID не вводится.

Защита действует для обычного DML при установленных triggers. Управляемый downgrade на disposable БД удаляет эти объекты схемы явно; это не операция приложения и не механизм очистки production history.

## Согласованный дизайн, раздел 3: защита registry и проверка migration

Статус раздела: согласован пользователем; реализация не начата.

### Защита registry

BEFORE UPDATE trigger защищает идентичность команды (`command_id`, `edit_version_id`, `feature_id`, `actor_user_id`, `request_fingerprint`, `created_at`). Для состояний действуют правила:

- `running` может завершиться в `succeeded` или `rejected`;
- `rejected` с `retry_on_access_change = true` может перейти в `running` для повторной попытки того же запроса;
- `succeeded` и обычный `rejected` не перезаписываются; replay не требует UPDATE registry;
- повторно сохранять неизменённый отказ из-за прав не требуется: при всё ещё отсутствующем доступе возвращается тот же отказ с correlation ID текущего запроса.

CHECK проверяет форму текущей строки. Отложенный constraint trigger проверяет финальное состояние записи к концу transaction: если запись всё ещё существует и имеет `running`, commit отклоняется. Проверяется текущая строка по PK, а не сохранённый `NEW.state` промежуточного INSERT, иначе допустимый переход `running -> succeeded` был бы ошибочно отклонён. Это отдельная DB-гарантия против ошибочного раннего commit, а не механизм восстановления после crash.

Признак `retry_on_access_change` ставится на основании причины отказа, а не одного только HTTP-статуса. В существующем API назначение проверяется после аутентификации/Editor guard. Для отказа из-за недоступного существующего объекта сохраняется `EDIT_VERSION_NOT_FOUND` с `retry_on_access_change = true`; отсутствующий объект не создаёт registry. Ошибки request/auth до входа в Save use case не резервируют ID. Точную маршрутизацию будущего Save endpoint предстоит реализовать в соответствующий день; migration не меняет auth API.

Известный уже завершённый `CommandId` другого запроса/actor не перезаписывается отказом `COMMAND_ID_REUSED`. Возвращаемая ошибка не уничтожает ранее сохранённый результат. Аналогично отказ в текущем доступе не стирает `succeeded`.

### Migration и границы работ

Новая revision следует за существующим head `f8a7b6c5d4e3`. Применённые старые migrations не редактируются. Новая migration добавляет колонку, две таблицы, именованные constraints/indexes и функции/triggers в schema `work_order`. Existing versions получают revision 1 без искусственных команд или событий и без изменения geometry.

День 2 реализует migration и проверки её основных гарантий через SQL. ORM-модели, их экспорт и подключение в Alembic metadata остаются в Дне 3. Save service/API/frontend не входят в реализацию Дня 2.

Downgrade на disposable БД удаляет новые triggers/functions/tables, затем draft column и её CHECK; существующие snapshot и baseline сохраняются. Новые command/event данные при таком schema rollback теряются. Это должно быть явно описано в migration и тестах, а не использоваться как обычная очистка истории.

### Матрица проверок

| Проверка | Ожидаемый результат | Этап |
| --- | --- | --- |
| Fresh upgrade до нового head | Обе таблицы, колонка, constraints/indexes/triggers созданы | День 2 |
| Upgrade с существующей версией, features и associations | UUID, geometry и исходные поля сохранены; draft revision 1; registry/history пусты | День 2 |
| Новая версия без явного draft revision | Server default даёт 1; NULL/0/отрицательная revision отвергаются | День 2 |
| Registry с некорректной формой результата или чужой feature | CHECK/FK отклоняет запись | День 2 |
| `running -> succeeded/rejected` в одной transaction | Commit допустим; отдельный commit с `running` отклоняется | День 2 |
| Попытка изменить идентичность или успешный результат | Trigger отклоняет UPDATE | День 2 |
| Повторная попытка после access rejection | Переход разрешён; обычный rejected возобновить нельзя | День 2 |
| INSERT корректного event и INSERT с несовместимым контекстом | Первый допустим, второй отклонён | День 2 |
| Повторный event для команды или revision; неверный шаг revision | PK/UNIQUE/CHECK отклоняют запись | День 2 |
| UPDATE/DELETE/TRUNCATE history | Запрещены; сохранённое событие не меняется | День 2 |
| Удаление версии с registry, features, associations и событием | Рабочие строки удалены; event сохранён без изменений | День 2 |
| Rollback mutation/result/event | Все изменения текущей transaction отменены | День 2, через SQL |
| Upgrade/downgrade/upgrade, metadata parity и отсутствие дублей индексов | Схема воспроизводима, ORM соответствует DDL | День 3 |
| Конкурентный INSERT history и удаление root | Нет event, вставленного без проверки существующего контекста; блокировки согласованы | День 3, DB integration |
| Save/no-op/retry/stale/Revert и before/after geometry | Поведение use case соответствует принятому контракту | Дни 5–8 |

Проверки выполняются только в отдельной disposable БД через `infra/db-tests.cmd` или эквивалентный isolated runner. Новые тесты используют уникальные UUID и rollback там, где это возможно. Для committed append-only data не вводится обходная production-функция DELETE; уничтожается disposable тестовая БД/схема в предусмотренном test lifecycle.

Прежний критерий «upgrade на чистой БД» расширяется осознанно: пользователь согласовал сохранение existing data и DB-enforced append-only, поэтому успешный DDL сам по себе не доказывает результат дня. Тесты перечислены как будущие проверки, они ещё не запускались.
