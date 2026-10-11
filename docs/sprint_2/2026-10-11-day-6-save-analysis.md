# День 6: анализ synchronous Save и идемпотентности

Дата анализа: 11 октября 2026 года. День 6 соответствует субботе, 8 августа, в исходном календаре Sprint 2.

Статус: требования D6-Q1–Q5, размещение ответственности, порядок отказов и проверки атомарности согласованы в обсуждении. [Письменная спецификация](2026-10-11-day-6-save-design.md) принята пользователем 11 октября 2026 года. Подготовлен [план реализации](2026-10-11-day-6-save-plan.md) для проверки. Реализация не начата. Основание исследования: HEAD `2f020a4`; до создания этого документа рабочее дерево было чистым.

## Цель и порядок обсуждения

Пользователь ожидает один synchronous Save, выполняющий mutation не более одного раза для одной логической команды. Требуются проверка `DraftVersionToken`, глобальная уникальность `CommandId`, воспроизведение сохранённого terminal result и отсутствие увеличения revision для no-op/retry. Обязательные сценарии: success, no-op, retry, command reuse.

Обсуждение идёт по архитектурному пути brainstorming: задача соединяет persistence, domain rules, concurrency и результат use case. Пользователь просит вопросы по одному в отдельных сообщениях и предложения только после устранения неясностей. Артефакты сохраняются в `docs/sprint_2`; код в рамках анализа не изменяется.

- [x] Прочитать инструкции репозитория и protocol; выполнить поиск релевантной agent memory.
- [x] Изучить календарь, ТЗ, согласованные контракты Дней 2–5 и текущие ключевые реализации.
- [x] Уточнить границу Дней 6–7 и оставшиеся требования отдельными вопросами.
- [x] После уточнений рассмотреть подходы и согласовать дизайн.
- [x] Оформить согласованную спецификацию и выполнить самопроверку.
- [x] Получить результат проверки письменной спецификации пользователем: «Принимаю».

## Что уже реализовано

Пути в таблице указаны относительно корня репозитория.

| Компонент | Факт текущего кода | Значение для Save |
| --- | --- | --- |
| `apps/backend/utility_service/use_cases/services/edit_version_service.py` | Реализует Open/reopen с `session.begin()`, проверкой Editor и assignment | Готового orchestration Save в этом сервисе нет. `get_visible_work_order()` берёт WorkOrder lock; его нельзя без анализа порядка блокировок переносить после root lock Save |
| `apps/backend/utility_service/use_cases/schemas/edit_version/geometry_save_in.py` | `GeometrySaveRequest` содержит UUID, строковый token и `GeometryValue` | Входная модель существует |
| `apps/backend/utility_service/web_api/parsers/geometry_save_request.py` | Строгий parser сохраняет Decimal; token проверяется только как непустая строка | Parser не проверяет актуальность token; формат и сравнение token относятся к следующему слою |
| `apps/backend/utility_service/domain_services/edit_geometry/fingerprint.py` | Fingerprint включает actor, адресуемые объекты, baseline, исходный token, policy и подготовленную geometry | Сравнение запросов уже определено шире простого сравнения JSON; новый token меняет идентичность |
| `apps/backend/utility_service/infrastructure/postgresql/repositories/edit_version_repository.py` | `lock_version()` блокирует root; `read_context()` делает отдельное чтение; есть prepare/validate/write | Boundary Дня 5 готова для включения во внешнюю транзакцию. `write_current()` меняет только geometry/operation, без revision, command и event |
| `apps/backend/utility_service/infrastructure/postgresql/repositories/edit_geometry_scope.py` | Handles связаны с session/transaction и поколением; вложенные savepoints после начала протокола инвалидируют scope | Способ разрешения конфликта уникальности CommandId должен учитывать этот запрет |
| `apps/backend/utility_service/infrastructure/postgresql/models/work_order/edit_version_command.py` | Глобальный PK по `command_id`; состояния running/succeeded/rejected; successful JSONB payload, поля отказа и access-retry flag | Структура хранения terminal result уже существует, orchestration reservation/replay отсутствует |
| `apps/backend/utility_service/infrastructure/postgresql/models/work_order/edit_version_change_event.py` | PK по command, уникальность version/revision, before/after geometry | История подготовлена, но production Save пока её не записывает |
| `apps/backend/utility_service/infrastructure/postgresql/geometry_codec.py` | Проверка обратимости Decimal → binary64, EWKB codec и `geometry_to_geojson()` | Есть средство формирования canonical geometry для ответа без произвольного округления |

## Ограничения существующей схемы

Источник: `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/b7d2e9f4a6c8_first_save_schema.py` и спецификация Дня 2.

- Команда должна вставляться в `running`. Финальное состояние перед commit должно быть terminal: deferred trigger запрещает committed running.
- У successful команды обязательны response status, JSON object payload и completed_at. Сохранённый success нельзя произвольно переписать.
- Идентичность команды и fingerprint неизменяемы. Исключительный переход rejected → running предусмотрен для согласованного access retry.
- Registry имеет FK на version/feature. Отсутствующий объект нельзя представлять обычной registry-строкой с несуществующими ссылками.
- Event insert проверяет существующие root/command/feature, successful command, context, актуальную revision, after geometry и operation.
- Trigger истории проверяет корректность вставляемого события, но не обеспечивает наличие события на каждую mutation. Это обязанность будущего Save.
- Отдельный commit reservation несовместим с terminal trigger и единой транзакцией.

## Уже согласованные требования, которые не следует спрашивать заново

Источник: [спецификация Дня 2](2026-10-01-day-2-first-save-schema-design.md), [Дня 4](2026-10-08-day-4-geometry-design.md), [Дня 5](2026-10-10-day-5-repository-context-design.md).

1. Replay успешной команды распознаётся до проверки её исходного token на актуальность для новой mutation. Проверка текущего доступа предшествует раскрытию результата.
2. Если A сохранила revision 2, а B — revision 3, retry A возвращает результат A с token 2. Current остаётся на результате B и revision 3.
3. Исправленный payload или новый token требуют нового CommandId. Численно и канонически эквивалентные запросы могут иметь одинаковый fingerprint несмотря на различия исходного JSON.
4. Infrastructure failure откатывает транзакцию и не превращается в durable domain rejection.
5. Ошибка воспроизводит status/code/message; `correlationId` относится к текущему HTTP-запросу.
6. После удаления registry replay не поддерживается. Сохранившийся history event блокирует reuse ID content-changing команды. Для удалённых no-op/rejected команд бессрочная дедупликация не обещана.
7. Revision увеличивается на один только при content change. No-op определяется сравнением текущей и предлагаемой geometry, а `operation` — отношением к baseline; no-op не обязательно означает `operation=unchanged`.
8. Baseline и AOI не изменяются Save. Допущение Дня 5: assignment/AOI/baseline неизменны на время Save.
9. Временный запрет нулевого соседнего сегмента D5-Q1 уже принят и действует до отдельного доменного уточнения; повторное согласование для этого этапа не требуется.

В ТЗ раздел 7 перечисляет token раньше reservation/replay. Более подробная принятая спецификация Дня 2 явно описывает replay раньше проверки актуальности token. При подготовке дизайна важно не потерять это уточнение.

## Что существующие тесты доказывают и чего пока не доказывают

- `test_geometry_fingerprint.py` проверяет canonical identity, изменение контекста, baseline/policy и отсутствие зависимости от verdict.
- `test_edit_geometry_concurrency.py` содержит ожидание root lock, свежее чтение после commit/rollback, независимость разных versions, совместимость с Open/reopen и запись repository с history trigger.
- `test_first_save_command_constraints.py` проверяет ограничения и переходы registry, включая rollback access retry.
- `test_first_save_event_constraints.py` и `test_first_save_event_concurrency.py` существуют для гарантий истории; полнота их покрытия в рамках текущего анализа ещё не перепроверена.
- Use-case tests `test_edit_version_service.py` относятся к Open/reopen. Полного production Save, который эти тесты могли бы вызывать, ещё нет.

Чтение тестов не означает их выполнение. В этом анализе тесты и БД не запускались, прежние отчёты не считаются результатом текущей проверки.

## Существенные места дальнейшего анализа

Это наблюдения и вопросы, а не выбранные способы реализации.

- Root lock сериализует команды одной версии, но не один CommandId, одновременно присланный для разных версий. Наличие глобального PK само по себе не задаёт безопасное восстановление SQL-транзакции после unique violation.
- Повтор A после B должен обходить transition validation относительно нового current, иначе корректный retry может быть отклонён правилами новой mutation.
- После `write_current()` scope потребляет context/prepared/validated handles версии. Дополнительная проверка `consume()` уточнила: root handles сохраняются (`generation=None`), однако их поле draft_revision является снимком и не обновляется автоматически. Revision orchestration должна учитывать это различие.
- Возвращаемый успех должен соответствовать тому payload, который стал durable после commit; ошибка commit не является success.
- Отрицательный terminal outcome должен переживать завершение use case, тогда как исключение внутри `session.begin()` обычно ведёт к rollback. Точная граница durable rejection зависит от согласованного объёма Дня 6.
- Success/no-op payload уточнён в D6-Q3–Q4, lifecycle — по канонической модели. Приоритет проверок будет явно представлен в дизайне; требования доступа и replay нельзя выводить только из порядка разделов старого ТЗ.

## Вопросы и ответы

### D6-Q1. Граница Дней 6–7

Календарь относит success/no-op/retry/reuse к Дню 6, а durable rejection, history и Revert — к Дню 7. При этом принятый контракт Save требует atomic snapshot + revision + terminal result + event для фактического изменения. Схема не запрещает commit mutation без события, поэтому вопрос нельзя решить только чтением DB constraints.

Вопрос пользователю: должен ли результат Дня 6 уже создавать событие истории в той же транзакции для каждого успешного изменения, или запись истории намеренно остаётся задачей Дня 7, а результат Дня 6 считается промежуточным внутренним этапом?

Ответ пользователя: «допустим промежуточный внутренний Save без события».

Зафиксированная граница: День 6 может сохранять geometry, revision и successful terminal result без history event. История остаётся на День 7. Это промежуточный внутренний этап, а не выполнение полного контракта Save Sprint 2. Полнота событий не является критерием приёмки Дня 6.

### D6-Q2. Durable rejection на промежуточном этапе

Календарь относит сохранение terminal rejection к Дню 7. При этом уже в День 6 необходимо отклонять stale token, command reuse и недопустимую geometry. Deferred trigger запрещает оставить новую команду в running после commit.

Вопрос пользователю: допустимо ли до Дня 7 отклонять новую неуспешную команду с полным rollback её транзакции, не сохраняя rejection и её CommandId, а durable replay в День 6 гарантировать только для success/no-op? При конфликте с уже существующим CommandId исходная запись сохраняется неизменной.

Следствие этой промежуточной границы: отклонённая новая попытка пока не закрепляет CommandId; стабильное воспроизведение отказа появится в День 7. Итоговый контракт Sprint 2 остаётся прежним.

Ответ пользователя: «Да».

Зафиксированная граница: День 6 сохраняет terminal success для content change и no-op. Новая неуспешная команда откатывается полностью, без durable rejection и без закрепления её CommandId. Уже существующая запись при command reuse остаётся неизменной. Durable rejection и access retry остаются на День 7.

### Проверка lifecycle по канонической модели

`Wiki/commands/update_edit_version_feature_geometry.md` явно ограничивает retry открытым lifecycle: после post/close/cancel/read-only/archive старый запрос отклоняется как закрытый save context. Это не требует нового продуктового решения. В текущем коде `EditVersionStatus` содержит только OPEN, а `WorkOrderStatus` — ASSIGNED и IN_PROGRESS; расширять lifecycle в рамках этого этапа пользователь не просил.

### D6-Q3. Successful payload при отсутствии изменения относительно baseline

ТЗ показывает successful Save response только для `operation=updated`: `basicValidation` содержит результаты geometry/AOI, предупреждение positional accuracy и `dirtyRelativeToBaseline=passed`. Для workspace без persisted change set ТЗ явно задаёт `basicValidation=null`. Форма успешного командного ответа для no-op на baseline отдельно не определена.

Сценарий: current совпадает с baseline; новая команда передаёт ту же geometry с актуальным token. Это successful no-op, revision не меняется, operation остаётся unchanged, hasPersistedChangeSet=false.

Вопрос пользователю: должен ли successful Save response в этом случае содержать `basicValidation=null`, как workspace без изменений, или результаты выполненных проверок geometry/AOI также должны возвращаться при отсутствии изменений?

Ответ пользователя: `null`.

Зафиксировано: successful no-op на baseline возвращает и сохраняет `basicValidation=null`. Это не отменяет проверки допустимости нового запроса. Решение касается no-op на baseline; поведение content-changing возврата к baseline уточняется отдельно в D6-Q4.

#### Дополнительная проверка Wiki по просьбе пользователя

`Wiki/specifications/edit_version_basic_draft_validation.md` описывает summary успешного Save: geometry/AOI — passed, topology — not_checked, positional accuracy — not_checked с POSITIONAL_ACCURACY_UNVERIFIED без evidence. `dirtyRelativeToBaseline` прямо назван информационным статусом отличия, а не критерием качества: passed при непустом diff, failed/false после Revert. Следовательно, отсутствие diff само по себе не отменяет смысл остальных результатов проверок.

`DDD_Wiki/state_machines/edit_version_persisted_change_set.md` явно допускает Unchanged → Unchanged при save(no-op baseline), но не задаёт форму basicValidation для этого перехода. `Wiki/commands/update_edit_version_feature_geometry.md` перечисляет basicValidation в командном ответе без отдельного правила null для no-op.

Вывод из источников: Wiki поддерживает трактовку «результаты проверок и признак наличия diff — разные сведения», однако точного JSON-контракта no-op на baseline не устанавливает. Распространение summary после Revert на no-op baseline является интерпретацией, а не явно принятым требованием. После этой проверки пользователь выбрал null и закрыл D6-Q3. Доменные имена полей Wiki отличаются от сокращённой API-формы ТЗ Sprint 2; их нельзя автоматически переносить в response как новые поля.

### D6-Q4. Возврат к baseline через общий Save

`validate_transition()` в `apps/backend/utility_service/domain_services/edit_geometry/structure.py` уже разрешает переход изменённого current к baseline: operation=unchanged, is_noop=false. Repository Дня 5 поддерживает этот переход, а `test_write_changes_only_target_and_revert_restores_exact_baseline()` проверяет восстановление исходной geometry. Request и fingerprint не различают UI-кнопки Save/Revert.

При этом календарь относит Revert к Дню 7. Неясно, означает ли это отсутствие отдельной приёмки Revert до Дня 7 или запрет этого перехода через внутренний Save Дня 6.

Вопрос пользователю: если в День 6 current уже изменён, а новый Save с актуальным token передаёт baseline geometry, допустим ли успешный возврат к baseline через общий Save, с увеличением revision на один, operation=unchanged, hasPersistedChangeSet=false и basicValidation=null, при том что история и полная приёмка Revert остаются на День 7?

Ответ пользователя: «Да».

Зафиксировано: общий внутренний Save Дня 6 разрешает content-changing возврат к baseline. Revision увеличивается на один, operation=unchanged, hasPersistedChangeSet=false, basicValidation=null. История и полная приёмка Revert остаются на День 7.

## Согласованное понимание этапа

### D6-Q5. No-op на изменённой линии

Вопрос пользователю: при no-op на уже изменённой линии сохраняем operation=updated, hasPersistedChangeSet=true и возвращаем validation summary?

Ответ пользователя: «Да».

Это закрывает различие между двумя successful no-op: на baseline basicValidation=null, на updated current — summary. Ни один no-op не увеличивает revision.

Внутренний синхронный use case соединяет существующие geometry rules и repository с глобальным registry. Его durable результат — successful command payload, включая no-op и возврат к baseline. Неуспешная новая попытка откатывается целиком. История, durable rejection, access retry, публичный endpoint, workspace extensions и UI не являются результатом этого этапа. Полный контракт Sprint 2 отложенными частями не отменяется.

No-op при current=baseline возвращает null validation. No-op при уже изменённом current сохраняет operation=updated и summary из successful response ТЗ: отсутствие новой mutation не означает отсутствие persisted change set. Retry возвращает исходный payload команды, а не заново вычисленное summary.

## Проверенные технические ограничения

- `EditGeometryScope.consume()` сохраняет root handles и удаляет зависимые context handles. Вложенная transaction после выдачи handles инвалидирует весь scope, даже если savepoint завершился успешно.
- `SessionFactory` использует `expire_on_commit=False`; это не делает ранее загруженные ORM-объекты свежими после ожидания lock. Repository Дня 5 уже использует column projections для этого случая.
- Open/reopen блокирует WorkOrder перед EditVersion. Save после получения root lock не должен брать конфликтующий WorkOrder lock.
- Единственная production state EditVersion сейчас OPEN; для WorkOrder предусмотрены ASSIGNED/IN_PROGRESS. Существующий workspace требует IN_PROGRESS + OPEN. Новые состояния lifecycle не нужны для этой задачи.
- Глобальный PK registry уже существует; добавлять другую таблицу уникальных идентификаторов для обычной reservation не требуется.
- Проверка PostgreSQL 16: при READ COMMITTED `INSERT ... ON CONFLICT DO NOTHING` может не вставить строку из-за конкурирующей transaction, не видимой snapshot самого INSERT. Последующий отдельный SELECT получает новый snapshot. Поэтому одно выражение INSERT+SELECT через CTE нельзя считать гарантией чтения победившей команды. Источники: [Transaction Isolation](https://www.postgresql.org/docs/16/transaction-iso.html), [INSERT](https://www.postgresql.org/docs/16/sql-insert.html).

## Граница сервиса и persistence

Уточнение пользователя: «Сервисы работают с агрегатом поэтому надо работать с EditVersionService».

Save реализуется методом существующего `EditVersionService`. Отдельный SaveEditVersionService не вводится. Различия последовательности locks Open и Save выражаются разными методами внутри сервиса агрегата, а не отдельными сервисами.

Проверка спецификации Дня 5 подтвердила, что там уже зафиксирован `EditVersionRepository` как persistence boundary всего агрегата, а geometry context/SQL/validation являются его внутренними частями. `DDD_Wiki/aggregates/edit_version.md` относит revision и idempotency record к той же consistency boundary.

Последнее уточнение пользователя: «Наверно для команд и событий не нужен отдельный репозиторий». Текущий дизайн использует единый EditVersionRepository; предыдущее разрешение на выделение дополнительных repositories не является требованием их создавать.

Исправленный вариант дизайна:

- `EditVersionService` владеет transaction, порядком actor/access/lifecycle/replay/token/validation и формированием результата use case.
- `EditVersionRepository` предоставляет операции root/context, geometry mutation, revision, registry lookup/reservation/finalization и проверку занятости ID, в том числе по сохранившейся history при отсутствии registry. Command row не становится самостоятельным агрегатом.
- Repository использует session сервиса, не открывает собственные транзакции и не делает commit/rollback. Глобальный поиск CommandId не требует загрузки или блокировки корня чужой версии для изменения.
- Отдельные repositories команд/событий не вводятся. В День 6 запись событий отсутствует; проверка существующего history ID входит в проверку занятости CommandId. Будущая запись истории также планируется через EditVersionRepository.
- При необходимости SQL и вспомогательные функции разделяются по внутренним файлам за единым интерфейсом EditVersionRepository, по существующему образцу geometry helpers.
- Geometry rules и fingerprint остаются в существующем чистом ядре.
- HTTP endpoint и расширение workspace response остаются вне Дня 6. Существующая сборка `get_edit_version_service()` сохраняет единую точку создания сервиса.

Текущее направление — Save в EditVersionService и persistence через EditVersionRepository. Варианты successful результата подтверждены D6-Q1–Q5; порядок отказов и проверки атомарности согласованы последним ответом пользователя. Детали протокола собраны в письменной спецификации для итоговой проверки.

## Первая часть предлагаемого дизайна: транзакционный протокол

1. Начать одну transaction; проверить active Editor, найти и заблокировать адресуемую EditVersion, прочитать context отдельным запросом, проверить assignment и допустимый lifecycle. Недоступный контекст не раскрывает чужой command payload.
2. Выполнить lookup CommandId. Очевидное несоответствие actor/version/feature означает reuse без раскрытия результата. Для сопоставимой команды подготовить canonical geometry и fingerprint на неизменном baseline/policy с исходным строковым token запроса.
3. Для существующего success с тем же fingerprint вернуть сохранённые status/payload. Не выполнять transition/spatial validation относительно более нового current и не проверять старый token как условие новой mutation. Иной fingerprint — COMMAND_ID_REUSED.
4. При отсутствии registry проверить history на этот ID. Для новой команды резервировать running через INSERT с конфликтом только по PK command_id и DO NOTHING. Если reservation проиграна, прочитать победившую команду отдельным SELECT и применить правила replay/reuse. Не обновлять чужую команду и не использовать savepoint. Сценарий удаления registry во время разрешения cross-version конфликта должен завершаться без mutation, если победителя уже нельзя надёжно прочитать.
5. Для полученной reservation сравнить token с текущей revision, затем вызвать geometry validation. При любом отказе откатить всю новую попытку согласно D6-Q2.
6. Записать current; увеличить revision ровно на один только при changed=true. Сформировать canonical success payload из записанного результата. При operation=unchanged validation=null; иначе summary по ТЗ. Финализировать command в succeeded и завершить transaction.
7. Возвращать успешный результат вызывающему коду только после успешного commit. Исключения SQL/commit не превращать в domain rejection. Повтор после неизвестного исхода commit использует тот же CommandId.

Точные signatures и расположение DTO будут оформлены в письменной спецификации. В День 6 не возникает собственных rejected registry rows; существующий rejected result не должен приводить к повторной mutation. Воспроизведение сохранённых status/code/message совместимо со схемой, а переход access rejection обратно в running остаётся на День 7.

## Вторая часть предлагаемого дизайна: результат и отказы

Сервис возвращает успешный результат use case со status=200 и payload согласованной формы ТЗ. Response не содержит признака replay, который делал бы повтор отличным от исходного ответа. Сохраняется весь payload, включая canonical geometry, token и basicValidation. Точность воспроизведения означает одинаковые JSON-значения; JSONB не обещает исходные пробелы или порядок ключей.

| Исход новой успешной команды | Revision | Operation | hasPersistedChangeSet | basicValidation |
| --- | --- | --- | --- | --- |
| Изменение линии, результат отличается от baseline | +1 | updated | true | Summary по ТЗ |
| No-op при уже изменённой линии | Без изменения | updated | true | Summary по ТЗ |
| No-op на baseline | Без изменения | unchanged | false | null |
| Возврат изменённой линии к baseline | +1 | unchanged | false | null |
| Replay | Без новой записи | Исходное значение | Исходное значение | Исходное значение |

Предлагаемая последовательность отказов:

1. Active Editor проверяется до раскрытия контекста; недопустимый actor получает ROLE_NOT_ALLOWED. Отсутствующая или недоступная version/feature — EDIT_VERSION_NOT_FOUND.
2. Недопустимый lifecycle — SAVE_CONTEXT_CLOSED, в том числе при retry, согласно канонической state machine.
3. Для доступного открытого контекста занятый ID с другим actor/target/fingerprint — COMMAND_ID_REUSED. Успешный matching replay распознаётся до проверки актуальности token и до новой transition/spatial validation.
4. Для новой команды token сравнивается как opaque string с `str(draft_revision)`: `01` не приравнивается к `1`, числовая нормализация не меняет fingerprint. Несовпадение — DRAFT_VERSION_STALE.
5. Затем применяются существующие domain/repository guards. Новая отклонённая команда полностью откатывается. HTTP-коды и сообщения отображаются централизованно в сервисе через существующий WorkOrderApiError; repository не формирует HTTP response.
6. SQL/protocol/commit failure не маскируется под отказ геометрии и не сохраняется как terminal rejection.

Подготовка fingerprint требует корректного baseline: повреждённый или отсутствующий baseline не подменяется выдуманными данными ради проверки reuse. Это отдельный отказ контекста. При очевидном несовпадении сохранённых actor/version/feature вычисление fingerprint для раскрытия чужого результата не требуется.

Таблица successful результатов отражает согласованные ответы D6-Q1–Q5. Порядок отказов согласован пользователем вместе с последней частью дизайна.

## Проверки предлагаемого результата

Use-case tests проверяют success, оба вида no-op, возврат к baseline, stale, reuse и replay A после B. Доказательство concurrency дополнительно требует PostgreSQL integration tests с отдельными session и реальными commits; mocks этого не доказывают.

| Сценарий | Проверяемый результат |
| --- | --- |
| Новый content-changing Save | Одна mutation, revision +1, одна successful команда с точным payload |
| No-op на baseline / на updated current | Revision и geometry не меняются; successful command сохраняется; validation null / summary соответственно |
| Новый Save к baseline из updated | Geometry восстановлена, operation unchanged, revision +1, validation null |
| A → B → retry A | Исходный payload A; current/revision B неизменны |
| Одновременный retry той же команды | Единственная mutation и одинаковый terminal result |
| Две новые команды одной версии с одним старым token | Только победитель меняет content; другая попытка stale и не закрепляет новый ID |
| Один ID для разных versions/actors/features/payload | Не более одного successful владельца; проигравший не получает чужой payload |
| Победитель reservation откатывается | Следующая допустимая попытка может зарезервировать ID; committed running не остаётся |
| Ошибка после geometry UPDATE / revision UPDATE / перед commit | Геометрия, revision и новая command row откатываются вместе |
| Потеря ответа после commit, новая session | Replay durable success без новой mutation |
| Повтор Open и Save | Нет обратного порядка конфликтующих WorkOrder/root locks |
| Registry удалён, event с ID остался | COMMAND_ID_REUSED, без новой mutation |

History event для собственных Save Дня 6 не ожидается по D6-Q1. Integration tests выполняются только в isolated test DB согласно существующему runbook. Проверки здесь пока перечислены как критерии будущей реализации, а не как выполненные тесты.

### Последняя часть дизайна для обсуждения: ошибки и приёмка

Предлагается сохранить в Дне 6 различимые domain errors, хотя их durable запись отложена: stale, reuse, lifecycle, invalid context, structure/geometry/AOI. Отказ новой команды откатывает reservation, mutation и revision. При reuse ранее committed запись сохраняется. Ошибки инфраструктуры остаются инфраструктурными; таймаут ожидания конкурентной команды не означает COMMAND_ID_REUSED.

Доказательство результата дня состоит из use-case tests и ограниченного PostgreSQL integration набора: конкурирующие одинаковые команды, одинаковый ID для разных versions, разные команды с одним token, rollback на этапах mutation/revision/finalization и replay из новой session после commit. Показатели проверяются независимым чтением committed состояния: geometry, revision, число и содержимое command rows, отсутствие оставшегося running. History events не входят в приёмку собственного Save Дня 6.

Ответ пользователя на порядок обработки и состав проверок: «Да». Эта часть согласована. Код и тесты на данном этапе не изменяются и не запускаются.

## Память проекта

Отдельная agent memory не создаётся: факты и открытые вопросы сохранены в этом анализе, а устойчивые контракты уже находятся в спецификациях Дней 2–5.
