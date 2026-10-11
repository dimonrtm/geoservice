# День 6: synchronous Save и идемпотентность

Дата: 11 октября 2026 года. Исходный календарный этап: суббота, 8 августа 2026 года.

Статус: письменная спецификация принята пользователем 11 октября 2026 года («Принимаю»). Реализация завершена; см. [отчёт](2026-10-11-day-6-save-implementation-report.md). Основание анализа кода: HEAD `2f020a4`.

## 1. Цель

Добавить внутренний synchronous Save в существующий `EditVersionService`. Один логический Save, идентифицированный `CommandId` и fingerprint, выполняет mutation не более одного раза. Повтор successful команды возвращает сохранённый результат, даже если current после неё менялся другой командой. Новая mutation требует актуального `DraftVersionToken`.

Пользователь уточнил границы промежуточного этапа:

- Save Дня 6 может сохранять content без history event; история остаётся на День 7.
- Новая неуспешная попытка откатывается целиком, без durable rejection и без закрепления CommandId; durable rejection и access retry остаются на День 7.
- Возврат изменённой geometry к baseline уже допустим через общий Save; отдельной команды для UI-кнопки Revert нет.
- Successful no-op на baseline и возврат к baseline возвращают `basicValidation=null`.
- No-op на изменённой линии сохраняет `operation=updated`, `hasPersistedChangeSet=true` и validation summary.
- Save принадлежит `EditVersionService`. Отдельные repositories команд и событий не нужны в выбранном дизайне; persistence остаётся в `EditVersionRepository`.

Эти ограничения не заменяют полный контракт Sprint 2. Реализация Дня 6 не объявляется готовым публичным Save всего спринта.

## 2. Источники и приоритет уточнений

- [Анализ и ответы пользователя](2026-10-11-day-6-save-analysis.md).
- [ТЗ Sprint 2](2026-07-31-sprint-2-technical-requirements.md) и [календарь](2026-07-31-sprint-2-calendar-plan.md).
- [День 2: schema/registry/history](2026-10-01-day-2-first-save-schema-design.md).
- [День 4: canonicalization/fingerprint](2026-10-08-day-4-geometry-design.md).
- [День 5: repository boundary](2026-10-10-day-5-repository-context-design.md).
- `Wiki/commands/update_edit_version_feature_geometry.md`, `Wiki/specifications/edit_version_basic_draft_validation.md`, `DDD_Wiki/aggregates/edit_version.md`, `DDD_Wiki/state_machines/edit_version_save_request.md`.

Приоритет replay над проверкой актуальности исходного token уже определён уточнённой спецификацией Дня 2. Повтор возвращает original command result, а не geometry последующей команды. Отдельные актуальные object/token не добавляются в response: конкретная форма Sprint 2 и уточнение Дня 2 уже отличаются в этой части от более раннего общего описания Wiki. Текущий доступ и lifecycle проверяются до выдачи сохранённого результата.

## 3. Scope

### Входит

- Метод Save существующего сервиса с одной внешней database transaction.
- Глобальная reservation CommandId, canonical fingerprint comparison, сохранение и replay successful результата.
- Проверка token под root lock.
- Существующие проверки geometry, запись current и увеличение revision только при фактическом изменении.
- Оба вида no-op и возврат к baseline.
- Различимые отказы use case с rollback новой попытки.
- Use-case tests и DB integration tests атомарности, конкуренции и durable replay.

### Не входит

- Создание событий для Save Дня 6; полнота истории будет обеспечиваться Днём 7.
- Сохранение новых terminal rejections и возобновление access-rejected команды.
- PUT endpoint, OpenAPI, UI, sessionStorage и расширение workspace response.
- Новые lifecycle states, изменение geometry policy, baseline/AOI, associations или attributes.
- Новая схема registry, вечный реестр всех когда-либо использованных UUID или общая платформа команд.

Schema migrations для штатного сценария не требуются: revision, registry, history и constraints уже существуют.

## 4. Ответственность компонентов

| Компонент | Ответственность |
| --- | --- |
| `EditVersionService` | Вход Save, transaction, actor/access/lifecycle, порядок replay/token/validation, mapping ожидаемых отказов и результат use case |
| `EditVersionRepository` | Root lock, context, command lookup/reservation/finalization, history-ID lookup, geometry mutation, revision |
| `domain_services/edit_geometry` | Существующие canonicalization, fingerprint, structure/transition rules |
| `geometry_codec.py` | EWKB и численно обратимое GeoJSON-представление результата |
| Save result schema/DTO | Типизированный успешный результат и сериализуемый payload по ТЗ |

Сервис и repository используют один `AsyncSession`. Repository не делает commit/rollback и не открывает новую session. Save начинает внешнюю transaction; вызов внутри уже начатой caller transaction не входит в контракт, как и существующий Open. Actor lookup выполняется внутри этой transaction, чтобы не создать неявный autobegin до `session.begin()`.

SQL команд и вспомогательные функции можно вынести в внутренние файлы, сохранив единый service-facing интерфейс `EditVersionRepository`. Новые методы не требуют переноса geometry rules в SQL или переписывания Open.

## 5. Вход и идентичность команды

Вход Save: `work_order_id`, `edit_version_id`, `feature_id`, `actor_id` и существующий `GeometrySaveRequest(command_id, draft_version_token, geometry)`.

Parser сохраняет Decimal и проверяет форму запроса до вызова сервиса. Прямые внутренние вызовы обязаны передавать эту типизированную форму; нарушение протокола не является успешной командой.

Fingerprint строится существующей функцией `command_fingerprint()` с policy из locked EditVersion, immutable baseline и исходным token запроса. Не вводится второй алгоритм hashing. В идентичность входят actor, адресуемые объекты, baseline identity/content, policy и canonical geometry по Дню 4.

Следствия:

- Изменение actor, target, token или canonical intent при том же ID — reuse.
- Различия JSON-форматирования и эквивалентная после canonicalization geometry сами по себе не означают reuse.
- Состояние current и результат новых spatial проверок не входят в fingerprint.
- Save и возврат к baseline используют один тип команды; отдельный discriminator Revert не добавляется.

Token opaque: новая команда сравнивает строку запроса с `str(draft_revision)`. `01` не считается token `1`. Парсинг произвольной строки в int для сравнения не применяется.

## 6. Транзакционный протокол

### 6.1. Доступ и блокировка

1. Начать внешнюю transaction. Проверить существующего active Editor.
2. Вызвать `lock_version(work_order_id, edit_version_id)`. Отсутствующая связь WorkOrder/version даёт `EDIT_VERSION_NOT_FOUND`.
3. Прочитать target context отдельным запросом после root lock, используя boundary Дня 5.
4. Проверить assignment и lifecycle. Недоступный target маскируется как `EDIT_VERSION_NOT_FOUND`. Рабочее состояние Save — WorkOrder IN_PROGRESS и EditVersion OPEN; иное состояние даёт `SAVE_CONTEXT_CLOSED`.

Root lock удерживается до завершения transaction. После него Save не берёт конфликтующий WorkOrder lock: Open уже использует порядок WorkOrder → EditVersion. Существующее допущение Дня 5 сохраняется: assignment, AOI и baseline не меняются конкурентным writer во время Save.

### 6.2. Replay и reservation

5. Найти command по глобальному CommandId. Если сохранённые actor/version/feature отличаются от запроса, отклонить reuse без выдачи чужого payload.
6. Для сопоставимой команды подготовить canonical candidate и fingerprint. Это подготовка на baseline; проверка перехода от текущего snapshot и spatial validation новой mutation здесь не выполняются.
7. Для существующего matching success вернуть сохранённые status/payload после завершения transaction. Исходный token не сравнивается с более новой revision. Иной fingerprint даёт `COMMAND_ID_REUSED`.
8. При отсутствии registry проверить history на этот ID. Сохранившийся event означает `COMMAND_ID_REUSED`: отсутствие registry не разрешает заново выполнять историческую команду.
9. Зарезервировать новую running command через `INSERT ... ON CONFLICT (command_id) DO NOTHING RETURNING ...`. Conflict target ограничен PK command_id; прочие нарушения БД не маскируются.
10. Если reservation не получена, выполнить отдельный SELECT победившей команды и применить правила identity/replay. Это не UPDATE существующего результата. Если после конфликтующей reservation строка исчезла из-за удаления другого root, повторно проверить history; при отсутствии достоверной записи завершить текущую попытку инфраструктурной ошибкой и rollback, без mutation и без ложного success/reuse.

Нет отдельного commit running, savepoints, polling по committed running или автоматического перезапуска mutation. Deferred trigger запрещает committed running; в штатном протоколе ожидание конкурента заканчивается его commit/rollback.

При READ COMMITTED конфликт INSERT может зависеть от строки, невидимой snapshot самого INSERT. Поэтому последующее чтение выполняется отдельным SQL statement, а не SELECT-веткой того же CTE. Основание: [PostgreSQL 16 Transaction Isolation](https://www.postgresql.org/docs/16/transaction-iso.html) и [INSERT](https://www.postgresql.org/docs/16/sql-insert.html).

Для разных versions root locks независимы, а глобальный PK разрешает конфликт одного CommandId. Проигравшая попытка не блокирует и не меняет чужой root. Гарантия at-most-once относится к committed mutation: rollback победителя позволяет другой допустимой попытке выполнить команду.

### 6.3. Новая mutation и commit

11. После успешной reservation сравнить token с актуальной revision locked root.
12. Выполнить existing repository validation: контекст, допустимый переход, spatial rules и AOI. Существующее временное правило D5-Q1 о нулевых соседних сегментах сохраняется.
13. Вызвать `write_current(validated_change)`. No-op не выполняет UPDATE geometry/operation.
14. Только при `changed=true` увеличить root revision ровно на один. Метод изменения revision требует root handle этой session/transaction и проверяет ожидаемую прежнюю revision; возвращает фактическое новое значение. Выход за BIGINT не возвращает success и не выполняет wraparound — transaction откатывается как инфраструктурная ошибка.
15. Построить canonical payload из фактически выбранной after geometry и итоговой revision. Сохранить status=200, payload, state=succeeded и completed_at в зарезервированной строке.
16. Завершить transaction. Вернуть success вызывающему коду только после успешного commit.

`write_current()` потребляет context/prepared/validated handles, но сохраняет root handles. Поле revision в root handle — снимок, а не автоматически обновляемый объект. Success использует значение, возвращённое операцией revision, либо исходное значение для no-op. Другие consumed handles не используются для повторной mutation.

При ошибке UPDATE/finalization/commit rollback отменяет новую reservation, geometry и revision вместе. После неизвестного клиенту исхода commit повтор с тем же CommandId либо воспроизводит committed success, либо выполняется как новая попытка, если commit не состоялся.

## 7. Successful result

Ответ use case содержит status=200 и payload согласованной API-формы ТЗ. Публичный route пока не добавляется.

Обязательные поля payload: `commandId`, `commandState=succeeded`, `draftVersionToken`, `operation`, `hasPersistedChangeSet`, `updatedFeature{id,geometry}`, `basicValidation`.

| Сценарий | Revision | Operation | hasPersistedChangeSet | basicValidation |
| --- | --- | --- | --- | --- |
| Content change с непустым diff к baseline | +1 | updated | true | Summary |
| No-op на updated current | Без изменения | updated | true | Summary |
| No-op на baseline | Без изменения | unchanged | false | null |
| Content-changing возврат к baseline | +1 | unchanged | false | null |
| Replay | Без новой записи | Исходное | Исходное | Исходное |

Summary имеет форму ТЗ:

```json
{
  "geometryStatus": "passed",
  "aoiStatus": "passed",
  "positionalAccuracyStatus": "POSITIONAL_ACCURACY_UNVERIFIED",
  "dirtyRelativeToBaseline": "passed"
}
```

Null означает согласованную форму ответа для отсутствующего diff, а не пропуск валидации нового запроса. Имена дополнительных доменных полей из Wiki не переносятся в этот сокращённый API-контракт.

GeoJSON строится существующим codec. Canonical storage geometry не подвергается новому округлению при формировании ответа. JSONB хранит весь successful payload; точный replay означает одинаковые JSON-значения, а не сохранение пробелов и порядка ключей. Отдельный признак replay не добавляется.

Пример: A создала revision 2, B — revision 3. Retry A возвращает geometry/token/summary A, а current и root остаются на результате B. Сборка ответа по текущему snapshot вместо сохранённого payload запрещена.

## 8. Отказы и приоритет проверок

| Условие | Status / code |
| --- | --- |
| Actor отсутствует, неактивен или не Editor | 403 ROLE_NOT_ALLOWED |
| WorkOrder/version/feature не найдены или недоступны | 404 EDIT_VERSION_NOT_FOUND |
| Lifecycle не допускает Save/replay | 409 SAVE_CONTEXT_CLOSED |
| CommandId занят другим intent/actor/target или только историей | 409 COMMAND_ID_REUSED |
| Новая команда содержит неактуальный token | 409 DRAFT_VERSION_STALE |
| Другая feature уже изменена | 409 MULTIPLE_FEATURE_CHANGE_NOT_ALLOWED |
| Feature не поддерживает редактирование | 422 FEATURE_NOT_EDITABLE |
| Повреждён исходный контекст | 422 WORK_ORDER_CONTEXT_INVALID |
| Недопустимая структура/переход | 422 GEOMETRY_STRUCTURE_CHANGED |
| Недопустимая geometry | 422 GEOMETRY_INVALID |
| Результат выходит за AOI | 422 GEOMETRY_OUTSIDE_AOI |

Общий приоритет: actor → доступ → lifecycle → command identity/replay → token новой команды → validation новой mutation. При этом fingerprint требует пригодного baseline: missing/corrupt baseline или неeligible target могут остановить подготовку до сравнения полного fingerprint/token. Нельзя выдумывать baseline ради сохранения этого формального порядка. Очевидное несовпадение сохранённых actor/version/feature обнаруживается без подготовки fingerprint.

Ожидаемые domain/repository rejections централизованно преобразуются сервисом в `WorkOrderApiError`. Repository сохраняет внутренние типизированные результаты. Неизвестные protocol/SQL/commit errors не перехватываются широким обработчиком как GEOMETRY_INVALID.

В День 6 новый отказ не сохраняется: исключение выходит из transaction boundary и вызывает rollback. При reuse исходная committed запись не меняется. Timeout ожидания competitor — инфраструктурная ошибка, а не доказательство reuse.

Schema допускает существующие rejected rows, хотя этот этап их не создаёт. Matching rejected row можно воспроизвести по сохранённым status/code/message, не выполняя mutation. Даже при `retry_on_access_change=true` автоматический переход rejected → running в День 6 не выполняется: поддержка этого исключения входит в День 7. Поведение явно обозначается как ограничение промежуточного внутреннего этапа.

## 9. История и предел уникальности

Save Дня 6 не создаёт event. Существующий append-only history используется только для обнаружения CommandId, пережившего удаление registry. Проверка существующей истории нужна уже для command reuse и не означает перенос записи событий из Дня 7.

Registry живёт вместе с EditVersion и может удаляться каскадно. Для команд Дня 6 без event после удаления registry не остаётся durable следа ID. Поэтому гарантия дедупликации сохраняется при существующем registry; бессрочная глобальная уникальность всех удалённых IDs не заявляется. Клиент генерирует новый UUID для каждого нового intent. Это дополнительный предел промежуточного этапа без истории, принятый в D6-Q1; production endpoint до завершения следующих этапов не подключается.

## 10. Проверки

### Use-case tests

- Content-changing success: правильный payload, mutation и увеличение revision ровно один раз.
- Оба вида no-op: без geometry UPDATE/revision increment, с successful command row и правильной validation.
- Возврат к baseline: точная geometry, unchanged, revision +1, null validation.
- Matching replay, включая A → B → retry A: исходный payload, без mutation и без проверки старого token как новой команды.
- Canonically equivalent request имеет одинаковую идентичность; изменение token/actor/target/intent даёт reuse.
- Stale, lifecycle, access и geometry errors откатывают новую попытку, не перезаписывают существующую команду.
- Status/code mapping, отсутствие раскрытия чужого payload и отсутствие успеха при commit failure.

### PostgreSQL integration tests

Тесты используют реальные concurrent sessions и независимое чтение committed состояния.

| Сценарий | Доказательство |
| --- | --- |
| Два одинаковых concurrent Save | Одна mutation, одна successful command, одинаковые результаты |
| Разные commands одной версии с одним token | После content change победителя проигравший stale; его registry row отсутствует |
| Один ID для разных versions | Только один committed владелец, другая version не изменена |
| Конкурирующий владелец ID откатился | ID доступен следующей допустимой попытке; committed running отсутствует |
| Ошибка после geometry/revision/finalization | Новая geometry, revision и registry откатились вместе |
| Deferred commit failure | Сервис не вернул success; независимое чтение подтверждает rollback |
| Commit завершён, ответ потерян, новая session | Исходный durable payload, без новой mutation |
| A → B → retry A | Результат A возвращён, storage остаётся на B |
| No-op обоих видов и возврат к baseline | Правильные geometry/revision/operation/payload; baseline неизменен |
| Save одновременно с Open/reopen | Нет обратного порядка конфликтующих locks |
| History ID без registry | COMMAND_ID_REUSED и отсутствие mutation |

Mock-тесты не заменяют эти проверки. Доказательство ожидания lock опирается на состояние PostgreSQL, а не на предположение после фиксированного sleep. Для падения commit используется воспроизводимая test-only fault injection; production hooks ради теста не добавляются.

DB tests выполняются только через `infra/db-tests.cmd` или эквивалентный isolated runner с отдельной `_test` БД по существующему runbook. Demo data не используются для destructive tests. Нужна релевантная регрессия Open, geometry, fingerprint, registry constraints и handle protocol, а также форматирование/lint изменённого backend-кода.

## 11. Затрагиваемые части кода

Пути относительно корня репозитория:

- `apps/backend/utility_service/use_cases/services/edit_version_service.py` — метод Save и orchestration.
- `apps/backend/utility_service/use_cases/schemas/edit_version/` — successful result/DTO.
- `apps/backend/utility_service/infrastructure/postgresql/repositories/edit_version_repository.py` — command/revision операции; возможные внутренние helpers рядом.
- `apps/backend/utility_service/infrastructure/postgresql/repository_rows/` — внутренние command rows/results при необходимости.
- `apps/backend/utility_service/infrastructure/postgresql/sql/` — SQL persistence, если вынесен из repository.
- `apps/backend/utility_service/use_cases/tests/` и `apps/backend/tests/integration_tests/` — проверки Save.

Точные signatures и разбиение файлов фиксируются в плане реализации после проверки этой спецификации. Существующие fingerprints, DB constraints и geometry algorithms сохраняются. Обнаруженный при реализации дефект этих компонентов требует явного описания и соответствующей проверки, а не скрытого расширения scope.

## 12. Критерий готовности и проверка документа

День 6 готов, когда новый внутренний Save доказал at-most-once committed mutation, актуальность token для новых команд, durable successful replay и атомарность rollback на реальной БД. Отчёт отдельно перечисляет отложенные history, durable rejection, access retry и публичный API. Успешные тесты не означают приёмку Дня 7 или всего Sprint 2.

Спецификация сверена с ответами D6-Q1–Q5, текущими service/repository/handle interfaces, schema transitions и ограничениями Дня 5. Вопросы размещения сервиса и repository разрешены последними уточнениями пользователя. Новые lifecycle states и самостоятельные repositories не вводятся.

Проверка спецификации не включает запуск product tests: код не изменялся. Отдельная agent memory не создаётся, поскольку решения и причины сохранены здесь и в анализе. Все изменения остаются unstaged; staging/commit/push выполняет только пользователь.
