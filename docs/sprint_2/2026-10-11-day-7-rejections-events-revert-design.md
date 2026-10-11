# День 7: terminal rejection, история изменений и Revert

Дата: 11 октября 2026 года.

Статус: цельная спецификация принята пользователем 11 октября 2026 года. [План реализации](2026-10-11-day-7-rejections-events-revert-plan.md) подготовлен для просмотра. Реализация и приёмка M2 ещё не выполнены.

## 1. Цель и границы

Завершить внутренний backend-контракт Save/Revert: воспроизводимые terminal outcomes, ровно одно append-only событие на фактическое изменение и атомарность snapshot, revision, command registry и history.

Сохраняются `EditVersionService`, единый `EditVersionRepository`, synchronous transaction и существующие таблицы. Отдельного command type или endpoint для Revert нет: это Save baseline geometry.

Входит в День 7:

- сохранение новых terminal rejections и их replay;
- ранние отказы при непригодном baseline и стабильная идентичность после его ремонта;
- возобновление access-rejected команды по правилам Дня 2;
- добавление событий для content-changing Save/Revert;
- backend-матрица M2, включая атомарность и конкуренцию.

Endpoint, workspace projection, UI, HTTP integration и сквозной restart-сценарий остаются последующим этапам календаря. Не добавляются исправление контекста через Revert, автоматическая очистка, восстановление старой истории, изменение baseline, properties, associations или network versions.

## 2. Основания и принятые уточнения

- [ТЗ Sprint 2](2026-07-31-sprint-2-technical-requirements.md).
- [Календарь и M2](2026-07-31-sprint-2-calendar-plan.md).
- [Схема Дня 2](2026-10-01-day-2-first-save-schema-design.md).
- [Geometry и fingerprint Дня 4](2026-10-08-day-4-geometry-design.md).
- [Repository Дня 5](2026-10-10-day-5-repository-context-design.md).
- [Save Дня 6](2026-10-11-day-6-save-design.md).
- [Анализ текущего кода и ответы пользователя](2026-10-11-day-7-rejections-events-revert-analysis.md).

Уточнения пользователя:

1. Обычный отказ при отсутствующем/повреждённом baseline остаётся исходным terminal result после ремонта baseline. Новое выполнение требует нового CommandId.
2. Гарантия replay действует пока существует registry. Физическое удаление EditVersion удаляет registry; replay после этого не требуется.
3. Полнота history обязательна только для новых команд после реализации Дня 7. Пропущенные события Дня 6 не восстанавливаются.
4. Для отказа при недоступном baseline одинаковое округление координат по policy версии означает тот же запрос. Например, `65.525` и `65.52500001` при шаге `0.0000001` возвращают исходный отказ при остальных одинаковых полях.

День 7 заменяет временные ограничения Дня 6: rollback всех новых domain rejections, отсутствие событий и запрет возобновления access rejection. Успешный Save, normal fingerprint, структура ответов, geometry rules и locking сохраняются с дополнениями ниже.

## 3. Компоненты и transaction boundary

| Компонент | Ответственность |
| --- | --- |
| `EditVersionService` | Orchestration, приоритет ошибок, outcome, replay/access retry, одна внешняя transaction |
| `EditVersionRepository` | Root/context, глобальная reservation, command transitions, snapshot/revision и INSERT event на общей session |
| `domain_services/edit_geometry` | Прежняя canonicalization/validation и два версионированных протокола fingerprint |
| PostgreSQL constraints/triggers | Immutable command identity, terminal state при commit, event provenance, уникальность и append-only |

Repository не выполняет собственный commit/rollback. Savepoints не вводятся: существующий `EditGeometryScope` инвалидирует handles при nested transaction. Root lock удерживается до завершения transaction; конфликтующий WorkOrder lock после root не добавляется. Сохраняются READ COMMITTED, свежие column projections и предпосылка неизменности assignment/AOI/baseline на протяжении отдельного Save.

Внутри transaction ожидаемый outcome представлен данными: success либо status/code/message отказа. После успешного выхода из `session.begin()` сервис возвращает `SaveGeometryResult` или поднимает `WorkOrderApiError`. Ожидаемый domain rejection не должен выходить из transaction как исключение до сохранения результата.

Все ожидаемые проверки новой mutation выполняются до `write_current()`. Неожиданные ошибки repository/БД/commit вызывают rollback целиком. Catch-all, который превращает инфраструктурную ошибку в terminal rejection, запрещён. Если commit отказа не удался, нельзя выдавать его как подтверждённый сохранённый результат.

| Исход | Committed состояние |
| --- | --- |
| Content-changing Save/Revert | Geometry, operation, revision +1, succeeded command, один event |
| Новый no-op | Succeeded command; snapshot, revision и history неизменны |
| Новый сохраняемый отказ | Rejected command; snapshot, revision и history неизменны |
| Обычный replay | Исходный результат; новых записей и mutation нет |
| Reuse занятого ID | Исходная command row неизменна |
| Инфраструктурный сбой | Все записи текущей попытки откатываются |

## 4. Идентичность и fingerprint

### 4.1. Существующий формат

`geom-v1:sha256:...` сохраняется без изменения алгоритма и существующих значений. `baseline_aligned` сравнивает canonical geometry; `unmatched_structure` сохраняет точные числовые значения без округления. Числа `1`, `1.0`, `1e0` равнозначны в обеих ветках.

Для идентичности baseline должен быть читаемым и соответствовать контексту root. Eligibility target и возможность вычислить fingerprint — разные проверки: например, читаемый Point baseline может участвовать в прежней `unmatched_structure` идентичности, хотя Save такой feature запрещён. Подготовка идентичности не разрешает mutation.

### 4.2. Новый формат для непригодного baseline

`geom-contextless-v1:sha256:...` применяется для новых ранних отказов, когда отсутствующий, повреждённый или несогласованный с root baseline не позволяет использовать обычный протокол. Не подставляются фиктивная baseline geometry или один error code вместо содержимого запроса.

Envelope содержит:

- собственную версию формата и command type `replace_feature_geometry`;
- workOrderId, editVersionId, featureId, actorUserId;
- defaultStateId и baseNetworkRevision из root;
- исходный draftVersionToken;
- policy snapshot версии: version, xyResolution, roundingMode, SRID и origin;
- полную request geometry с округлением каждой координаты по этой policy.

Сохраняются type, количество и порядок координат. Числа сериализуются детерминированно существующими Decimal helpers; hash вычисляется по canonical JSON. VertexIndex не вычисляется без baseline. Формат envelope и golden vectors фиксируются при реализации нового протокола и затем являются контрактом совместимости.

Не включаются baseline geometry/digest, current geometry/revision, access/lifecycle state, причина отказа, время, correlationId или CommandId. Последний остаётся ключом registry. Policy и root provenance неизменны в рамках lifecycle версии; ремонт baseline между попытками не меняет их.

### 4.3. Сравнение повторов

Для существующей row алгоритм определяется её сохранённым prefix. Восстановление baseline не переключает contextless-команду на `geom-v1`; fingerprint не обновляется. Для старого `geom-v1` не допускается сравнение через contextless fallback. Неизвестный prefix — ошибка протокола без mutation.

| Повтор contextless-команды | Результат после действующих guards |
| --- | --- |
| Те же поля, координаты одинаковы после округления | Исходный terminal result |
| Другой token | `COMMAND_ID_REUSED` |
| Другая geometry после округления, count или порядок coordinates | `COMMAND_ID_REUSED` |
| Другой actor/target | `COMMAND_ID_REUSED` |
| Исправлен только baseline | Исходный обычный rejection |

Расстояние меньше шага само по себе не гарантирует одинаковое округление. Новый формат не меняет точное сравнение `unmatched_structure` обычного протокола.

Оба формата хранятся в существующем TEXT столбце. Новые таблицы/колонки для этого не требуются. Внутреннее вычисление fingerprint для сохранения раннего role/access/lifecycle отказа не раскрывает пользователю скрытые данные.

## 5. Отказы и порядок обработки

### 5.1. Граница сохранения

Новая команда с существующей адресуемой version/feature сохраняет ожидаемый domain rejection внутри use case. Request/auth errors до use case не занимают ID. Отсутствие version/feature либо несовпадение workOrderId/editVersionId не создаёт registry row и не связывает команду с посторонним target.

| HTTP | Code | Сохранение новой команды при существующем target |
| --- | --- | --- |
| 403 | `ROLE_NOT_ALLOWED` | Обычный rejection, если проверка выполнена внутри use case |
| 404 | `EDIT_VERSION_NOT_FOUND` | При отсутствии assignment-доступа — access rejection с retry flag; при отсутствующем target записи нет |
| 409 | `SAVE_CONTEXT_CLOSED` | Обычный rejection |
| 409 | `DRAFT_VERSION_STALE` | Обычный rejection |
| 409 | `COMMAND_ID_REUSED` | Исходный ID не перезаписывается; дополнительная row под ним не создаётся |
| 409 | `MULTIPLE_FEATURE_CHANGE_NOT_ALLOWED` | Обычный rejection |
| 422 | `FEATURE_NOT_EDITABLE` | Обычный rejection |
| 422 | `WORK_ORDER_CONTEXT_INVALID` | Обычный rejection |
| 422 | `GEOMETRY_STRUCTURE_CHANGED` | Обычный rejection |
| 422 | `GEOMETRY_INVALID` | Обычный rejection |
| 422 | `GEOMETRY_OUTSIDE_AOI` | Обычный rejection |

Сохраняются status/code/message. CorrelationId формируется для текущего HTTP-запроса и не входит в terminal result. Внутреннее чтение root/target для записи раннего отказа допустимо; наружный ответ не раскрывает причины повреждения недоступного контекста.

### 5.2. Приоритет

Общий порядок наружных результатов: actor/активная роль → наличие и доступ к target → lifecycle → identity/replay → token новой mutation → domain validation.

Сохраняется исключение Дня 6: обнаруженные при подготовке identity неeligible feature/непригодный baseline дают ранний `FEATURE_NOT_EDITABLE`/`WORK_ORDER_CONTEXT_INVALID`, даже при stale token. Для существующей contextless row ремонт baseline не запускает эту подготовку заново вместо replay. Очевидное несовпадение actor/version/feature занятой команды определяется без baseline fingerprint.

Domain validation сохраняет порядок repository: целостность current/baseline/AOI → пространственная пригодность исходных данных → другая изменённая feature → структура candidate/перехода → geometry validity → покрытие candidate AOI. Недопустимая и одновременно выходящая за AOI candidate даёт `GEOMETRY_INVALID`; сломанный AOI или непригодная исходная geometry дают `WORK_ORDER_CONTEXT_INVALID`.

Текущие role/access/lifecycle guards могут запретить выдачу старого результата. Такой ответ не перезаписывает старую row. После восстановления условий matching обычный terminal result воспроизводится без повторной доменной проверки. Если для старого `geom-v1` исходный baseline стал нечитаемым, прежнее сравнение невозможно: возвращается ошибка контекста без изменения команды; новый формат не используется для обхода проверки identity. Подмена содержимого immutable baseline после normal Save не входит в штатный lifecycle.

### 5.3. Reservation и конкуренция

Сохраняется глобальная reservation через `ON CONFLICT DO NOTHING`. Проигравший INSERT читает row отдельным SELECT при READ COMMITTED и обрабатывает её по сохранённому fingerprint/state. Предварительный вычисленный отказ не даёт права заменить результат победителя.

Если registry отсутствует, но CommandId сохранился в history, возвращается reuse без mutation. Пропавший результат конкурентной reservation не считается разрешением выполнить команду заново; сохраняется существующая проверка history и ошибка протокола при невозможности достоверно определить исход.

Lock timeout и инфраструктурные ошибки не означают reuse и не становятся terminal domain rejection. Committed `running` запрещён существующим deferred trigger.

## 6. Access retry

Только rejected row с `retry_on_access_change=true` допускает возобновление. Schema разрешает этот флаг исключительно для 404 `EDIT_VERSION_NOT_FOUND` существующего, но недоступного по assignment target.

Пока доступа нет, row не переписывается. После восстановления доступа и прохождения role/lifecycle guards проверяется immutable identity; затем выполняется `rejected -> running` и новая проверка исходного token и domain rules. Результат может быть success или ordinary rejection, например stale. Для новой не-access причины retry flag становится false.

Fingerprint, actor, target и created_at сохраняются; старые result fields очищаются при переходе в running, затем сохраняется новый terminal outcome и completed_at. Если исходная команда contextless, её формат остаётся тем же и при возобновлении после ремонта baseline. Mutation всё равно требует полноценной текущей domain validation.

Новый token или другое содержимое под прежним ID — reuse. Инфраструктурный сбой возобновлённой попытки откатывает её к прежнему committed access rejection.

## 7. События и Revert

Порядок content-changing записи:

`write_current -> increment_revision -> complete_command -> append_event -> commit`.

Event trigger требует уже succeeded command, поэтому success finalization выполняется до INSERT event внутри общей transaction. Сбой event/commit откатывает snapshot, revision, command и событие вместе.

Before/after берутся из `GeometryWriteResult` в исходном EWKB. Before — фактический current до mutation, а не постоянный baseline. После `write_current()` нельзя повторно использовать consumed geometry handles; locked root остаётся доступным в пределах transaction для revision/finalization/event.

| Итог изменения | Event type |
| --- | --- |
| Geometry изменилась, operation `updated` | `change_set_persisted` |
| Geometry вернулась к baseline, operation `unchanged` | `change_set_cleared` |
| No-op, rejection или replay | Событие отсутствует |

Event содержит CommandId, actor, feature, version/work order/default state IDs, base revision, draft revisions до/после и время БД. Разность draft revisions равна 1. Сохраняются PK CommandId, UNIQUE `(edit_version_id, draft_revision_after)`, provenance checks и запреты UPDATE/DELETE/TRUNCATE history.

Revert — Save baseline с новым ID и актуальным token. Он восстанавливает точный baseline EWKB, включая off-grid coordinates, возвращает `operation=unchanged`, `hasPersistedChangeSet=false`, `basicValidation=null`. При content change добавляет одну revision и cleared event.

Revert уже unchanged geometry — successful no-op. Replay прежнего Revert после последующего Save возвращает прежний результат, не отменяя новый Save. Stale Revert сохраняет terminal stale rejection. Revert не исправляет повреждённый current/baseline/AOI и не отменяет существующие ограничения редактирования.

## 8. Совместимость и история до Дня 7

Старые registry rows продолжают читаться по `geom-v1`. Replay успешной команды Дня 6 не создаёт event задним числом. Если исходная версия имеет revision 5 без history, первое новое изменение создаёт event 5 -> 6; отсутствующие события 1 -> 5 не являются дефектом приёмки Дня 7.

Полнота history означает ровно один event на каждую новую content-changing команду Дня 7. UNIQUE/PK доказывают только отсутствие дублей; обязательное наличие event доказывается integration tests Save transaction.

Registry удаляется при физическом удалении версии; history сохраняется. Закрытие версии не является основанием для очистки. Новая retention automation и изменение append-only защиты не входят в задачу.

## 9. Матрица M2

| ID | Проверяемый сценарий | Ожидаемое доказательство |
| --- | --- | --- |
| M2-01 | Save A -> Save B -> Revert | Три event, цепочка baseline -> A -> B -> baseline, типы persisted/persisted/cleared, revisions +1 |
| M2-02 | No-op на baseline и updated current | Новая succeeded row, без event и изменения revision |
| M2-03 | Replay Save/Revert после более поздней команды | Исходный status/payload; current и history неизменны |
| M2-04 | Каждый documented domain rejection | Сохранённые status/code/message; неизменность geometry/revision/history |
| M2-05 | Обычный rejected replay после изменения условий | Исходный отказ; повторная domain validation не меняет результат |
| M2-06 | Отсутствующий/повреждённый baseline и его ремонт | Durable rejection; exact/grid-equivalent retry возвращает его после ремонта |
| M2-07 | Изменённый token/geometry/identity занятого ID | Reuse, исходная row неизменна; guards не раскрывают чужой результат |
| M2-08 | Fingerprint vectors | Старый geom-v1 неизменен; новые vectors; точный unmatched_structure; разные значения по разные стороны границы округления; неизвестный prefix |
| M2-09 | Role/access/lifecycle и сочетания нарушений | Приоритет guards; старые terminal rows не перезаписываются |
| M2-10 | Stale + непригодный baseline; invalid + outside AOI | Документированный приоритет ошибок |
| M2-11 | Access rejection -> доступ восстановлен | Success либо ordinary stale/domain rejection; immutable identity и сброс retry flag |
| M2-12 | Сбой возобновлённой access-команды | Независимое чтение подтверждает прежний committed отказ |
| M2-13 | Fault injection после mutation/revision/finalization/event и на commit | Полный rollback; допустимый повтор не создаёт partial history |
| M2-14 | Сбой commit нового rejection | Нет подтверждённого terminal domain result и committed running |
| M2-15 | Concurrent identical success/rejection | Один логический outcome, одна row и не более одного event; replay проигравшего |
| M2-16 | Разные ID с одним token | Одна mutation; другая команда получает durable stale |
| M2-17 | Один ID разных versions; commit/rollback победителя | Глобальная уникальность и корректное поведение после ожидания |
| M2-18 | Save/Open, свежесть root/actor после ожидания | Нет обратного порядка locks; не используются устаревшие ORM данные |
| M2-19 | Event/command constraints | Нет committed running, изменения identity, duplicate event или UPDATE/DELETE/TRUNCATE history |
| M2-20 | Off-grid Revert и неизменность исходных данных | Точный baseline EWKB; properties/associations/network versions и baseline не меняются |
| M2-21 | Старая команда без event и старая revision | Replay без backfill; новые события отражают реальные последующие revisions |
| M2-22 | Новая session/service instance после commit | Durable success/rejection replay и точные значения history |
| M2-23 | Request/auth до use case и отсутствующий target | Нет reservation; занятая чужая row не изменяется |
| M2-24 | History пережила registry | Reuse content-changing CommandId без повторной mutation |

Unit tests проверяют orchestration и fingerprint. Атомарность, constraints и concurrency проверяются PostgreSQL/PostGIS integration tests с независимым чтением committed состояния. Используется `infra/db-tests.cmd` либо эквивалентный isolated runner с отдельной `_test` БД; demo-БД не используется для destructive checks.

Регрессия охватывает Open, geometry/canonicalization, repository protocol, registry/event constraints и metadata/migration проверки, предусмотренные существующим runner. Backend format/lint также должны проходить. Тесты Дня 6, закрепляющие отсутствие rejection/event и запрет access retry, получают новые ожидаемые результаты.

Новая session не подменяет реальный restart process: сквозная проверка restart остаётся следующим этапам. M2 закрывается только по фактической реализации и успешным проверкам, не по согласованию документа.

## 10. Области реализации и ограничения

- `apps/backend/utility_service/use_cases/services/edit_version_service.py` — outcomes, ранние rejections, replay и orchestration событий.
- `apps/backend/utility_service/infrastructure/postgresql/repositories/edit_version_repository.py` и `edit_version_commands.py` — rejected finalization, access resume и event persistence.
- `apps/backend/utility_service/domain_services/edit_geometry/fingerprint.py` и соответствующие типы — contextless fingerprint без изменения geom-v1.
- Unit/integration tests соответствующих слоёв — матрица M2.

Точные signatures и разбиение helpers определяются планом реализации. Не вводится отдельный aggregate/context, не меняются таблицы только ради нового fingerprint, не отменяется D5-Q1 о нулевых соседних сегментах. Обнаруженный дефект существующих компонентов описывается отдельно; он не даёт основания незаметно расширить scope.

Все артефакты остаются в `docs/sprint_2`. Изменения оставляются unstaged. `git add`, `git commit` и `git push` не выполняются.

## 11. Проверка спецификации

Проверены согласованность transaction/DB triggers, различие normal/contextless identity, неизменность обычного rejection, исключение access retry, scope истории Дня 7 и соответствие матрицы этим правилам. Спецификация не заявляет реализованность функций или успешный прогон backend tests.

Реализация завершена по прямому разрешению пользователя; фактические результаты M2 приведены в [отчёте реализации](2026-10-11-day-7-rejections-events-revert-implementation-report.md). Дополнительная agent memory не создаётся: решения и их причины сохранены в этой спецификации и связанном анализе.
