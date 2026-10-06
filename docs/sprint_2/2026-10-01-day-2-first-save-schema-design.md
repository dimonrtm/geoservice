# День 2 Sprint 2: схема первого сохранения

Дата: 1 октября 2026 года. Календарный день спринта: вторник, 4 августа 2026 года.

Статус: спецификация принята пользователем 1 октября 2026 года; схема реализована. Проверки и границы реализации описаны в [отчёте](2026-10-01-day-2-first-save-schema-implementation-report.md).

## 1. Цель и границы

Подготовить PostgreSQL-схему для synchronous Save одной существующей line feature внутри `EditVersion`: revision token, durable registry команд и append-only история фактических изменений. Migration должна применяться к чистой БД и сохранять существующие версии и geometry при upgrade.

В День 2 входят новая Alembic migration, ограничения, индексы, функции/triggers и SQL integration tests основных гарантий. ORM-модели и metadata parity относятся к Дню 3; Save service, fingerprint algorithm, API и UI — к следующим дням. Они описаны здесь только в части требований к хранению.

Не входят: новая схема baseline, дополнительные архивные таблицы, история всех попыток, автоматическая retention cleanup, spatial search по истории, новые виды редактирования и защита от администратора, способного изменить схему БД.

Основания: [ТЗ](2026-07-31-sprint-2-technical-requirements.md), [календарь](2026-07-31-sprint-2-calendar-plan.md), [анализ кода и согласованные уточнения](2026-10-01-day-2-schema-analysis.md). Последний документ содержит рассмотренную альтернативу с архивными идентичностями; выбран вариант самостоятельных событий с проверкой контекста при INSERT.

## 2. Существующий код и размещение

Все новые объекты находятся в schema `work_order`:

| Объект | Изменение |
| --- | --- |
| `work_order.edit_versions` | Добавляется `draft_revision` |
| `work_order.edit_version_commands` | Новый registry |
| `work_order.edit_version_change_events` | Новая история |
| `work_order.edit_version_features` | Существующий current snapshot, без новой baseline column |
| `utility_network.default_state_features` | Существующий baseline, не изменяется |

Активная цепочка migration находится в `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/`; текущий head по исходникам — `f8a7b6c5d4e3`. Новая revision добавляется после него. Старые migrations не переписываются.

`EditVersionFeature` имеет составной ключ `(edit_version_id, feature_id)`. При открытии версии `WorkOrderRepository.create_open_edit_version()` уже копирует baseline в initial current snapshot. Это остаётся прежним: требование об отсутствии дублирования означает отсутствие дополнительного baseline geometry рядом с current geometry в той же строке.

`EditVersionService.reopen_edit_version()` обновляет `last_opened_at`. Это не content change и не должно увеличивать draft revision.

## 3. Revision root

Добавляется `draft_revision BIGINT NOT NULL DEFAULT 1` с именованным CHECK `draft_revision >= 1`.

- Existing rows получают значение 1 без изменения остальных полей и geometry.
- Server default остаётся для новых версий, включая INSERT текущего кода до появления ORM-поля.
- Начальная revision не создаёт synthetic command или event.
- Content-changing Save/Revert увеличивает revision на 1. No-op, retry и read/open — нет.
- Увеличение выполняется в Save transaction; trigger на любой UPDATE root не используется.
- Дополнительный index по revision не нужен: root выбирается и блокируется по UUID PK.
- API представляет revision строкой; клиент не вычисляет token самостоятельно.

## 4. Registry команд

### Поля

| Поле | Тип | NULL/default |
| --- | --- | --- |
| `command_id` | UUID, PK | NOT NULL |
| `edit_version_id` | UUID | NOT NULL |
| `feature_id` | UUID | NOT NULL |
| `actor_user_id` | UUID | NOT NULL |
| `request_fingerprint` | TEXT | NOT NULL, непустое |
| `state` | VARCHAR(16) | NOT NULL; `running`, `succeeded`, `rejected` |
| `retry_on_access_change` | BOOLEAN | NOT NULL DEFAULT false |
| `response_status` | SMALLINT | nullable |
| `response_payload` | JSONB | nullable |
| `rejection_code` | TEXT | nullable |
| `rejection_message` | TEXT | nullable |
| `created_at` | TIMESTAMPTZ | NOT NULL DEFAULT now() |
| `completed_at` | TIMESTAMPTZ | nullable |

`response_payload` содержит исходный successful response целиком, включая geometry и token. Это сохранённый результат команды, а не отдельная baseline column. Fingerprint algorithm относится к Дню 4; TEXT не фиксирует преждевременно длину или конкретный hash algorithm.

### Связи и индексы

- `command_id` уникален во всём registry, не только внутри версии.
- FK `edit_version_id -> work_order.edit_versions.id`, `ON DELETE CASCADE`.
- Составной FK `(edit_version_id, feature_id) -> work_order.edit_version_features(edit_version_id, feature_id)`, `ON DELETE NO ACTION`.
- Actor сохраняется как UUID без нового cross-context FK, аналогично существующему `owner_user_id`. Аутентификация actor выполняется приложением.
- B-tree index `(edit_version_id, feature_id)` обслуживает FK и доступ по версии. Отдельные индексы по state, timestamp, actor и JSONB не требуются.

Самостоятельное удаление feature с командами не является операцией Sprint 2. Удаление всей версии должно удалять registry и snapshot в согласованной операции. Проверка включает existing associations, чьи FK сейчас используют `RESTRICT`; сохранность истории не должна зависеть от порядка случайно выполняемых cleanup statements.

### Форма строки

Именованные CHECK явно проверяют NULL/non-NULL, чтобы SQL UNKNOWN не пропускал неполные результаты:

| State | Обязательные данные | Запрещённые данные |
| --- | --- | --- |
| `running` | Идентичность и fingerprint | Status, payload, rejection fields, completed_at; retry flag должен быть false |
| `succeeded` | HTTP status 200–299, JSON object payload, completed_at | Rejection fields; retry flag должен быть false |
| `rejected` | HTTP status 400–499, непустые code/message, completed_at | Successful payload |

Infrastructure failure не сохраняется как terminal domain rejection: текущая transaction откатывается. `retry_on_access_change = true` допустим только для `rejected` с `response_status = 404` и `rejection_code = 'EDIT_VERSION_NOT_FOUND'`, когда объект существует, но недоступен Editor. Приложение определяет существование объекта; CHECK сам не проверяет права.

### Неизменность и переходы

При INSERT команда начинает с `running`; отдельного commit для резервирования ID нет. BEFORE INSERT/UPDATE guard обеспечивает этот контракт и защищает неизменность `command_id`, `edit_version_id`, `feature_id`, `actor_user_id`, `request_fingerprint`, `created_at`.

Разрешены переходы:

- `running -> succeeded`;
- `running -> rejected`;
- `rejected` с `retry_on_access_change = true` -> `running` для повторной попытки того же запроса.

`succeeded` и обычный `rejected` не перезаписываются. Replay не выполняет UPDATE. Если доступ всё ещё отсутствует, уже сохранённый access rejection тоже не требуется переписывать. При новой попытке очищаются поля прежнего результата, при завершении заменяется `completed_at`; первая `created_at` сохраняется.

Отложенный constraint trigger на INSERT/UPDATE проверяет финальную строку по `command_id` к завершению transaction: существующая строка не может оставаться `running`. Проверяется состояние текущей строки, а не промежуточный `NEW.state`, запомненный при INSERT. Это позволяет `running -> succeeded/rejected` в одной transaction и запрещает ошибочный ранний commit.

### Поведение запросов

| Ситуация | Registry и ответ |
| --- | --- |
| Версия или feature отсутствует | Команда невыполнима; новая запись не создаётся |
| Объекты существуют, но недоступны Editor | Сохраняется access rejection; при повторе права проверяются заново |
| После access rejection доступ появился | Тот же ID и payload могут выполняться при актуальном token и остальных проверках |
| Тот же ID с другим содержимым/actor | `COMMAND_ID_REUSED`; исходная запись не перезаписывается и чужой результат не раскрывается |
| Retry успешной команды | Возвращается её исходный successful response без новой mutation/event/revision |
| Retry обычного rejection | Возвращаются исходные status/code/message без повторной доменной проверки |
| Исправленный payload или новый token | Новая логическая попытка требует нового ID |
| Новая команда со stale token | `DRAFT_VERSION_STALE`; клиент отдельно перечитывает workspace |
| Request/auth error до входа в use case | ID не резервируется |

Пример replay: A создала revision 2, B затем создала revision 3. Повтор A возвращает geometry A и token 2; current snapshot остаётся на geometry B и revision 3. Replay успешной команды распознаётся до проверки её исходного token на актуальность для новой mutation. Проверки текущего доступа предшествуют раскрытию ответа.

Если доступ к уже успешной команде потерян, HTTP-отказ не заменяет её `succeeded` и не разрешает последующее повторное выполнение. «Последний результат команды» означает результат именно этой команды, а не более поздний результат другой команды.

`correlationId` в error body формируется для текущего HTTP-запроса. Связь повторов в логах задаётся `CommandId`. Исходный correlation ID не является неизменной частью replay результата.

## 5. История событий

### Поля

Все поля NOT NULL.

| Поле | Тип и назначение |
| --- | --- |
| `command_id` | UUID, PK; одновременно идентификатор события |
| `edit_version_id` | UUID исторической версии |
| `work_order_id` | UUID рабочей задачи |
| `default_state_id` | UUID baseline |
| `feature_id` | UUID изменённой feature |
| `actor_user_id` | UUID автора |
| `event_type` | VARCHAR(32): `change_set_persisted` или `change_set_cleared` |
| `before_geometry` | geometry(LINESTRING, 4326) |
| `after_geometry` | geometry(LINESTRING, 4326) |
| `base_network_revision` | INTEGER, как существующий root |
| `draft_revision_before` | BIGINT |
| `draft_revision_after` | BIGINT |
| `occurred_at` | TIMESTAMPTZ DEFAULT now() |

Перед Save B after Save A `before_geometry` содержит geometry A, а не baseline. Revert создаёт событие перехода от текущей geometry к baseline. No-op, retry и rejection событий не создают.

### Ограничения

- PK `command_id`: не больше одного события на команду.
- UNIQUE `(edit_version_id, draft_revision_after)`: одно событие на новую revision; этот index также обслуживает историю версии в порядке revision.
- Base и обе draft revisions положительны; after больше before, разность равна 1.
- CHECK event_type ограничен двумя значениями.
- PostGIS type фиксирует LineString и SRID 4326; обе geometry не empty, valid и simple.
- Before/after отличаются по точному представлению координат, сравниваемому через `ST_AsEWKB`; топологическое равенство не используется как критерий отсутствия координатного изменения.
- Пространственные и дополнительные дублирующие B-tree indexes не создаются.

### Проверка контекста при добавлении

Постоянных FK history на root, registry или другие удаляемые строки нет. Исторические UUID после удаления объекта остаются исходными.

BEFORE INSERT trigger:

1. Находит root и блокирует его `FOR UPDATE`; отсутствие root — ошибка.
2. Находит и блокирует команду `FOR SHARE`, проверяет `succeeded` и совпадение version/feature/actor.
3. Находит и блокирует target feature `FOR SHARE`; она должна быть line внутри этой версии.
4. Сверяет work order, default state и base revision с root, after revision — с текущим draft revision, after geometry — с current geometry.
5. Сверяет event type с operation snapshot: `change_set_persisted` соответствует `updated`, `change_set_cleared` — `unchanged`.

Root блокируется первым; будущий Save соблюдает тот же порядок root -> command -> feature. Locks удерживаются до завершения transaction. Они защищают окно проверки и INSERT от конкурентного удаления/изменения проверяемых строк. Тесты конкурентности подтверждают это на реальном PostgreSQL.

Trigger не восстанавливает before geometry из уже изменённого snapshot и не доказывает все правила геометрического редактирования. Правильность before geometry, соответствие operation baseline и полнота событий на все content-changing Save остаются обязанностью Save transaction и её integration tests. Наличие trigger не означает защиту от произвольного ручного изменения всей рабочей модели.

### Append-only

- BEFORE UPDATE/DELETE row triggers завершают попытку ошибкой.
- BEFORE TRUNCATE statement trigger запрещает очистку.
- INSERT разрешён при выполнении всех проверок.
- Откат незавершённой transaction допустим: ещё не committed событие не является сохранённой историей.
- Защита относится к обычному DML при установленных triggers. Административный DDL не входит в эту гарантию.

## 6. Транзакция и удаление

Порядок content-changing Save: проверка контекста/доступа и replay, reservation/переход команды в running, проверки token и geometry, обновление snapshot и revision, запись successful result, INSERT event, единый commit. Точные fingerprint и validation алгоритмы реализуются в соответствующие дни.

Если event не проходит проверку или backend падает до commit, изменения текущей попытки откатываются целиком. При retry после ранее committed access rejection rollback оставляет прежний отказ, а не удаляет его.

При физическом удалении `EditVersion`:

- registry удаляется вместе с версией;
- current features/associations удаляются в согласованной операции;
- history остаётся неизменной, включая все UUID и geometry;
- baseline не удаляется как побочный эффект новой схемы.

Автоматической периодической очистки нет. Закрытие версии без её физического удаления не является основанием для очистки registry в этом спринте.

После удаления registry replay старой команды не поддерживается. Сохранившийся event блокирует повторное использование ID content-changing команды: будущий Save проверяет такой ID и возвращает `COMMAND_ID_REUSED` без mutation. Для удалённых no-op/rejected команд следа в history нет; бессрочная проверка всех когда-либо использованных UUID несовместима с согласованным удалением registry. Клиент не переиспользует UUID для новых логических команд.

## 7. Migration и проверка

Migration создаёт только новую колонку, registry/history, именованные constraints/indexes и trigger functions/triggers в `work_order`. Не меняет geometry, seed, API, ORM и алгоритмы Save.

CHECK-ограничения и индексы выражают свойства текущей строки/уникальность. Triggers используются для переходов состояний, проверки финального running, контекста INSERT history и append-only. Их нельзя заменить одним набором CHECK.

Основные SQL integration tests Дня 2:

1. Fresh upgrade создаёт объекты схемы.
2. Upgrade с existing versions/features/associations сохраняет UUID, geometry и остальные поля; revision равна 1; новые таблицы пусты.
3. Server default работает; NULL/0/отрицательная revision запрещены.
4. Registry отклоняет invalid FK, неполный результат, неверную state и несовместимый retry flag.
5. Commit с running запрещён; переход к success/rejection в одной transaction разрешён.
6. Изменение identity или final success/обычного rejection запрещено; access rejection можно повторить.
7. Корректный event принимается; неверные ссылки, actor, context, revision или after geometry отклоняются.
8. Повтор command/revision event и недопустимые geometry отклоняются.
9. UPDATE/DELETE/TRUNCATE history запрещены без изменения сохранённого события.
10. Удаление root с registry и associations сохраняет event и удаляет рабочие строки.
11. Ошибка INSERT event и явный rollback отменяют snapshot, revision и command changes одной попытки.

День 3: ORM models/exports/Alembic metadata, metadata parity, отсутствие дублей индексов, upgrade/downgrade/upgrade и конкурентный INSERT history против удаления root. Дни 5–8: полноценные Save/no-op/retry/stale/Revert tests, корректность before/after и аутентификации.

Все destructive DB tests выполняются только через `infra/db-tests.cmd` или эквивалентный isolated runner с `TEST_DATABASE_URL` отдельной БД `_test`. Demo-БД не используется. Нельзя добавлять обходной production DELETE для очистки истории в тестах: применяются rollback, уникальные IDs и disposable test lifecycle. Существующие cleanup helpers, удаляющие features до root, проверяются на совместимость с новым registry FK.

Downgrade удаляет новые triggers/functions/tables, затем draft column и CHECK. Existing current/baseline geometry остаётся. Command/history данные удаляемых таблиц при downgrade теряются; такой schema rollback проверяется на disposable БД и не является обычной retention-операцией.

## 8. Уточнения относительно прежних документов

- Domain rejection сохраняется только при существующем target; request/auth ошибки до use case и отсутствующие объекты не резервируют ID.
- Отказ из-за прав может быть заменён результатом повторной попытки; остальные terminal outcomes воспроизводятся.
- Replay success возвращает исходный response, а не актуальный snapshot после других команд.
- Stale возвращает строгую ошибку; актуальный workspace читается отдельно.
- Error replay сохраняет status/code/message, но correlation ID относится к текущему запросу.
- History переживает физическое удаление root и registry, поэтому постоянные FK на них не используются.
- Проверка Дня 2 шире fresh upgrade: она включает existing data и согласованные гарантии БД.

Эти уточнения собраны из решений пользователя. Исходные wiki и ТЗ не переписаны автоматически. После итогового просмотра спецификации ссылки и последующий план должны учитывать именно согласованный контракт этого документа.

## 9. Состояние проверки документа

При подготовке спецификации код и БД не изменялись. Последующая реализация и результаты integration tests описаны в [отчёте](2026-10-01-day-2-first-save-schema-implementation-report.md). Проверка документа охватывает соответствие согласованным решениям, согласованность удаления и append-only, переходов registry, replay, границ Дней 2–3 и ссылок на исходники. Отдельная agent memory не нужна: устойчивые решения сохранены здесь.
