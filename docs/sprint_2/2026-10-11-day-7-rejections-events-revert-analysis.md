# День 7: анализ отказов, событий и Revert

Дата анализа: 11 октября 2026 года. День 7 относится к календарному этапу 9 августа 2026 года; календарь не переносится.

Статус: исследование и уточнения завершены; [цельная спецификация](2026-10-11-day-7-rejections-events-revert-design.md) принята пользователем 11 октября 2026 года. [План реализации](2026-10-11-day-7-rejections-events-revert-plan.md) подготовлен для просмотра. Реализация не начата. Тесты в рамках этого анализа не запускались; ниже описаны прочитанный код и существующие проверки, а не результаты нового прогона.

## Цель и ход обсуждения

Понимание запроса: завершить контракт воспроизводимых положительных и отрицательных исходов Save/Revert и проверяемой истории изменений для M2. Сначала исследовать текущую реализацию, затем задавать вопросы по одному; варианты решения предлагать только после уточнения требований. Артефакты сохранять в `docs/sprint_2`.

Классификация brainstorming: архитектурная задача, поскольку меняются транзакционный контракт отказов и взаимодействие registry, snapshot и history. Текущий этап — просмотр плана реализации; production-код не изменяется.

Последовательность работы:

1. Изучить текущие контракты, сервис, repository, schema и тесты — первичный проход выполнен.
2. Уточнить неоднозначности по одному вопросу — выполнено, ответы D7-Q1–Q4 ниже.
3. После ответов сопоставить подходы и обсудить дизайн — выбран A, четыре раздела согласованы.
4. Сохранить цельную спецификацию и представить на проверку — выполнено, спецификация принята пользователем.

## Источники

- [ТЗ Sprint 2](2026-07-31-sprint-2-technical-requirements.md), разделы 6–11 и AC-03–AC-09.
- [Календарь](2026-07-31-sprint-2-calendar-plan.md): M2 и разделение Дней 7–8.
- [Схема Дня 2](2026-10-01-day-2-first-save-schema-design.md): terminal results, access retry, triggers и retention.
- [Контракт Дня 6](2026-10-11-day-6-save-design.md): порядок проверок и явно отложенные функции.
- `apps/backend/utility_service/use_cases/services/edit_version_service.py`.
- `apps/backend/utility_service/infrastructure/postgresql/repositories/edit_version_repository.py` и `edit_version_commands.py`.
- `apps/backend/utility_service/infrastructure/postgresql/repositories/edit_geometry_validation.py`.
- `apps/backend/utility_service/domain_services/edit_geometry/canonicalization.py` и `fingerprint.py`.
- `apps/backend/utility_service/web_api/parsers/geometry_save_request.py`.
- `apps/backend/utility_service/infrastructure/postgresql/models/work_order/edit_version_command.py`.
- `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/b7d2e9f4a6c8_first_save_schema.py`.
- `apps/backend/utility_service/use_cases/tests/test_save_geometry_service.py` и `test_save_geometry_replay.py`.
- `apps/backend/tests/integration_tests/test_save_geometry_atomicity.py` и `test_save_geometry_concurrency.py`.

## Что уже реализовано

| Область | Наблюдаемое поведение |
| --- | --- |
| Transaction | `save_geometry()` владеет внешней `session.begin()`; success возвращается после commit |
| Доступ | Проверяются actor, активная роль Editor, наличие target, assignment и lifecycle до раскрытия replay |
| Сериализация | Root `EditVersion` блокируется `FOR UPDATE`; используется свежая проекция колонок |
| Идентичность | Глобальный CommandId, canonical fingerprint, reservation через `ON CONFLICT DO NOTHING` |
| Success replay | Сохранённые status/payload возвращаются до проверки устаревшего token; повтор не меняет current |
| Rejected replay | Существующая rejected row воспроизводится через `WorkOrderApiError`; сервис сам такие rows пока не создаёт |
| Новые отказы | Исключение покидает transaction и откатывает reservation; durable rejection отсутствует |
| Revision | Увеличивается один раз только при content change; no-op сохраняет successful command |
| Revert | Обычный Save baseline geometry; возвращается точный baseline EWKB, operation становится `unchanged` |
| События | Есть ORM/schema/triggers и поиск CommandId в history; записи event из Save нет |
| Access retry | В schema есть `retry_on_access_change`; сервис не выполняет `rejected -> running` |
| API | Save endpoint не обнаружен в текущих API-модулях; календарь относит endpoint/readback к Дню 8 |

## Фактический порядок Save

`actor -> root lock -> read_context -> assignment -> lifecycle -> command lookup/target identity -> prepare_candidate -> fingerprint -> replay/history/reservation -> token -> validate_candidate -> write_current -> revision -> success finalization -> commit`.

Этот порядок важен для нескольких различий:

- Новая stale-команда резервируется, затем откатывается: сейчас CommandId не закрепляется отказом.
- `prepare_candidate()` требует пригодный baseline ещё до fingerprint и reservation. `FEATURE_NOT_EDITABLE` и некоторые `WORK_ORDER_CONTEXT_INVALID` возникают здесь.
- Структурно неправильная, но корректно разобранная request geometry может получить `PreparedGeometry.rejection_code` и fingerprint. Неверный endpoint или число вершин не обязательно препятствует идентификации команды.
- Повреждение baseline отличается от повреждения current: current не входит в fingerprint, но проверяется при новой mutation.
- Проверка текущего доступа и lifecycle может скрыть уже сохранённый результат. Это не даёт права перезаписывать исходную command row.

## Отказы и границы воспроизводимости

| Ситуация | Текущий путь | Уточнение контракта |
| --- | --- | --- |
| Неверный JSON, UUID, token, GeoJSON type, XY или диапазон | Parser отклоняет до use case | По существующему контракту CommandId не резервируется |
| Version/feature отсутствует | 404 до reservation | День 2 явно исключает новую registry row; FK требует существующий target |
| Target существует, но назначен другому Editor | 404 до fingerprint | День 2 требует access rejection с повторной проверкой доступа; День 6 это отложил |
| Stale token | 409 после reservation | Нет durable row в текущей реализации |
| Другой fingerprint/actor/target под занятым ID | 409 reuse | Исходная row неизменна; отдельный rejection под тем же PK сохранить нельзя |
| Неверная структура | 422, в том числе через подготовленный rejection code | Нужно учитывать приоритет token и identity при сочетании нарушений |
| Недопустимая candidate geometry | 422 `GEOMETRY_INVALID` | Отличается от повреждения исходных данных |
| Candidate вне AOI | 422 `GEOMETRY_OUTSIDE_AOI` | Проверяется покрытие всей линии |
| Отсутствующий/невалидный AOI либо исходная geometry вне AOI | 422 `WORK_ORDER_CONTEXT_INVALID` | Это проблема контекста, а не только candidate |
| Отсутствующий/повреждённый baseline | 422 до fingerprint | Формулировка «все доменные отказы» не согласована с потребностью fingerprint в baseline |
| Инфраструктурная ошибка/ошибка commit | Rollback | По Дню 2 не превращается в terminal domain rejection |

Согласно Дню 2, обычный rejection воспроизводится без повторной доменной проверки. Исключение — access rejection существующего объекта: после восстановления доступа тот же запрос может исполняться при актуальном token. При rollback такой повторной попытки прежний committed отказ сохраняется. Новый token или исправленная geometry требуют нового CommandId.

`correlationId` относится к текущему HTTP-запросу; точность replay отказа означает сохранение status/code/message, а не прежнего correlationId.

## История: существующие гарантии и пробел

Schema обеспечивает не более одного event на CommandId и на `(edit_version_id, draft_revision_after)`. Before/after должны различаться по EWKB, revisions — на единицу. UPDATE, DELETE и TRUNCATE history запрещены triggers.

BEFORE INSERT требует уже `succeeded` command, проверяет target/actor, root provenance, актуальную revision, after geometry и соответствие event type текущему operation. Следовательно, фактический DB-контракт требует finalization success до INSERT event внутри общей transaction.

Trigger не может восстановить прежнюю geometry из уже обновлённого snapshot и не проверяет наличие event при каждом UPDATE snapshot. Полнота истории и корректный before остаются обязанностью orchestration и integration tests. Repository уже возвращает `GeometryWriteResult` с before/after, operation и changed.

Повторный content-changing Save после первого должен описывать переход от предыдущего current, а не от baseline. Revert — переход от текущей geometry к baseline. No-op, replay и rejection не создают событий. Возврат к baseline уже работает без отдельного command type.

## Существующая тестовая база и последствия для M2

В прочитанных тестах есть Save/no-op/Revert/replay из новой session, точный off-grid baseline roundtrip, отказ commit, rollback на этапах mutation/revision/finalization, глобальная конкуренция CommandId и взаимодействие Save/Open.

Часть тестов намеренно закрепляет временные ограничения Дня 6:

- `test_stale_rolls_back_reservation` и `test_domain_rejection_rolls_back_new_registry` ожидают отсутствие registry после отказа.
- `test_invalid_geometry_leaves_no_command_or_mutation` ожидает отсутствие durable rejection.
- `test_existing_access_rejection_is_not_resumed` и DB-проверка `test_stored_rejection_is_replayed_without_resuming` запрещают возобновление даже при access retry flag.
- `test_save_noop_revert_and_retry_committed_results` проверяет неизменность history после Save/Revert.

Поэтому неизменённая зелёная регрессия Дня 6 не доказывает M2: часть ожидаемых результатов соответствует ещё не завершённому контракту.

В будущей матрице M2 должны быть прослежены по требованиям: durable rejection/replay; сохранность исходного результата при reuse; access recovery; различимые ошибки и их сочетания; один event на content change; before/after для нескольких Save и Revert; no-op/retry без нового event; rollback при ошибке INSERT event и commit; конкурентные success/rejection; отсутствие committed running. Это области проверки, а не утверждённый план реализации.

## Неоднозначности для последовательного обсуждения

### D7-Q1. Повтор после исправления baseline — ответ получен

Пользователь подтвердил: запрос «должен навсегда воспроизводить первоначальный отказ». Исправление отсутствующего/повреждённого baseline не разрешает исполнение той же команды. Для новой попытки нужен новый CommandId. Это согласуется с правилом обычного terminal rejection в ТЗ и спецификации Дня 2; техническое ограничение текущего fingerprint не отменяет требование.

### D7-Q2. Граница слова «навсегда» — ответ получен

Спецификация Дня 2 предусматривает удаление registry вместе с физически удаляемой EditVersion; после удаления registry replay не поддерживается. Rejected-команды не имеют change event, поэтому отдельного исторического результата после такого удаления сейчас нет. Автоматическая очистка registry и очистка при простом закрытии версии в Sprint 2 не предусмотрены.

Пользователь подтвердил сохранение прежней границы: отказ неизменен на протяжении существования registry. Физическое удаление EditVersion удаляет registry; replay после этого не требуется. Ответ D7-Q1 не вводит бессрочное хранение результатов вне registry.

### D7-Q3. Изменения Дня 6 без событий — ответ получен

Реализация Дня 6 могла сохранять geometry и повышать revision без history events: это явно разрешено её спецификацией и закреплено тестами. Текущий snapshot и terminal successful payload не сохраняют всю последовательность before/after для достоверного восстановления каждого пропущенного события.

Пользователь подтвердил: полнота истории проверяется только для новых команд после реализации Дня 7. Восстановление пропущенных событий Дня 6 в приёмку не входит. Это не разрешение на очистку или изменение существующих данных. Replay старой successful команды не является новой mutation и не должен создавать событие задним числом.

### D7-Q4. Эквивалентность запросов при недоступном baseline — ответ получен

День 4 различает две ветки fingerprint: `baseline_aligned` сравнивает canonical geometry, `unmatched_structure` — точные числовые значения без округления к grid. Записи числа `1`, `1.0`, `1e0` равнозначны в обеих ветках. Обе существующие ветки требуют baseline для общего fingerprint context; отсутствующий или нечитаемый baseline отдельно не описан.

Пользователь подтвердил: при одинаковых CommandId, token и остальных полях координаты, округляющиеся в одно значение по сетке версии, должны возвращать первоначальный отказ. Например, `65.525` и `65.52500001` при resolution `0.0000001`. Это правило относится к идентификации отказа при недоступном baseline; прежняя точная идентификация `unmatched_structure` при пригодном baseline не отменяется. Само по себе расстояние меньше шага не означает эквивалентность: важен одинаковый результат округления.

## Понимание требований после ответов

Продуктовые уточнения D7-Q1–Q4 получены. Оставшиеся технические решения рассматриваются ниже, без изменения уже принятых правил: request/auth errors до use case не занимают ID; отсутствующий target не создаёт registry; access/lifecycle gates предшествуют раскрытию результата; обычный terminal rejection не пересматривается; access rejection допускает возобновление по Дню 2; инфраструктурные ошибки откатывают transaction. При сочетании недоступности существующего target и повреждения baseline наружу не раскрывается ошибка скрытого контекста.

Техническое следствие D7-Q4: нельзя выбирать способ сравнения старой команды заново по текущей пригодности baseline. После ремонта это изменило бы fingerprint и нарушило D7-Q1. Для уже сохранённой команды способ сравнения должен определяться её сохранённой идентичностью.

## Рассмотренные подходы — выбран A

Пользователь согласовал точечное расширение (A) как основу подробного дизайна. Это согласование подхода; разделы дизайна и итоговая спецификация рассматриваются отдельно. Реализация не начата.

### A. Расширить существующий механизм точечно — рекомендуемый

Сохранить `EditVersionService`, `EditVersionRepository` и существующий `geom-v1` для запросов, чей baseline позволяет его построить. Для ранних отказов, где это невозможно, ввести явно версионированный формат fingerprint без geometry baseline: полная request geometry, округлённая по policy версии, адресуемые ID, actor, исходный token и стабильный контекст root. Не подставлять фиктивную baseline geometry или один error code вместо содержимого запроса.

При retry сначала читать существующую command row; её формат fingerprint определяет алгоритм сравнения и после восстановления baseline. Ветка без baseline сохраняет type, количество и порядок координат; изменение token, target или значимых координат остаётся reuse. Эта ветка не должна незаметно заменить старое правило `unmatched_structure`.

Достоинство: сохраняет правила и fingerprints уже выполненных команд, использует существующий TEXT столбец и не требует новой таблицы только ради ранних отказов. Цена: два явно различимых формата идентичности; нужны отдельные тесты выбора формата, ремонта baseline и access retry. Применимость к ранним отказам должна быть перечислена в спецификации, а не определяться произвольным catch-all исключением.

### B. Хранить контекст нормализации отдельно для каждой команды

Добавить persisted metadata о выбранном способе нормализации и необходимых исходных параметрах. Replay сравнивает запрос по сохранённому контексту. Это позволяет более явно отделить идентичность команды от текущего состояния домена и расширять протокол в будущем.

Цена: новая migration, immutable metadata, совместимость старых rows и более широкий persistence-контракт. Для текущих требований Дня 7 это существенно больше изменений, чем вариант A.

### C. Перевести все новые команды на новый общий fingerprint

Создать единый новый протокол идентичности, отдельно сохранив чтение старого `geom-v1`. Чтобы сохранить оба правила Дня 4 и D7-Q4, новый протокол всё равно должен различать способы нормализации.

Цена: затрагивает весь успешный Save и уже проверенные canonical equivalence cases; смешанные старые/новые команды усложняют приёмку. Для Дня 7 преимуществ перед A недостаточно.

## Общая основа будущего дизайна

Независимо от выбора fingerprint:

- Ожидаемый новый отказ завершается `running -> rejected` и commit; API-исключение, если интерфейс сервиса его сохраняет, выдаётся после успешного завершения transaction. Не сохранять инфраструктурные сбои как доменные отказы.
- Reuse не заменяет исходную row. Access retry использует разрешённый переход `rejected -> running` и при rollback сохраняет прежний committed отказ.
- Content-changing Save: mutation, revision, terminal success, INSERT event и один commit. Порядок success перед event обязателен из-за существующего trigger.
- Event получает фактические before/after из `GeometryWriteResult`. Тип определяется итоговым operation: `updated` — `change_set_persisted`, `unchanged` — `change_set_cleared`.
- Revert остаётся Save baseline geometry; no-op, rejection и replay событий не создают.
- Endpoint и workspace projection остаются границей Дня 8; M2 проверяет внутренний backend-контракт.

## Раздел дизайна 1. Владение транзакцией и атомарность — согласован

Пользователь подтвердил контракт транзакции, включая commit terminal rejection до выдачи API-исключения и атомарную запись success/event.

`EditVersionService` остаётся владельцем одной внешней transaction; `EditVersionRepository` выполняет persistence на той же session. Отдельные command/event repositories, независимые commits и savepoints не вводятся. Последнее соответствует существующему `EditGeometryScope`: nested transaction инвалидирует выданные handles.

Внутри transaction ожидаемый outcome представляется данными: success либо rejection со status/code/message. Новый сохраняемый rejection завершает command row в `rejected`. Только после успешного выхода из `session.begin()` сервис возвращает `SaveGeometryResult` или поднимает `WorkOrderApiError`. Так сохраняется внешний интерфейс сервиса, но ожидаемый отказ не уничтожает собственную запись rollback-ом.

Все ожидаемые доменные проверки новой mutation выполняются до `write_current()`. После начала mutation ошибки persistence, нарушения repository protocol и commit failure выходят как ошибки и откатывают transaction целиком; catch-all с преобразованием таких ошибок в terminal rejection запрещён. Если commit отказа не удался, сервис не сообщает его как успешно сохранённый terminal result.

| Исход | Committed результат |
| --- | --- |
| Новый content-changing Save/Revert | Current geometry и operation, revision +1, succeeded command и ровно один event |
| Новый no-op | Succeeded command, без изменения geometry/revision/history |
| Новый сохраняемый доменный отказ | Rejected command, без изменения geometry/revision/history |
| Replay | Исходный результат, без новых записей и mutation |
| Reuse занятого ID | Исходная command row сохраняется без изменений |
| Инфраструктурная ошибка | Ни одна запись текущей попытки не сохраняется |

Для content change порядок записи: `write_current -> increment_revision -> complete_command -> append_event -> commit`. Event trigger требует `succeeded` command, поэтому finalization precedes INSERT event, но не отдельный commit. Before/after берутся из `GeometryWriteResult`; повторно использовать consumed geometry handles после mutation нельзя. Locked root остаётся пригодным для revision/finalization/event в рамках той же transaction.

При возобновлении access-rejected команды её переход в running и новый terminal outcome выполняются в одной transaction. Ошибка этой попытки восстанавливает прежнюю committed rejected row через rollback. Ни новая команда, ни возобновлённая не могут остаться committed в running.

При сохранении общей схемы блокировок root удерживается до конца transaction; после него не добавляется конфликтующая блокировка WorkOrder. Предпосылки Дня 6 о неизменности assignment, AOI и baseline во время отдельного Save сохраняются. Ремонт baseline между попытками рассматривается отдельно в fingerprint/replay.

## Раздел дизайна 2. Идентичность команды — согласован

Пользователь подтвердил два формата fingerprint, выбор алгоритма по сохранённой команде и неизменность идентичности после восстановления baseline.

Существующие значения `geom-v1:sha256:...` и алгоритм их вычисления сохраняются. При пригодном baseline новые команды используют прежний протокол: `baseline_aligned` сравнивает canonical candidate, `unmatched_structure` сохраняет точные числовые значения без округления. Одного совпадения error code недостаточно для идентичности запросов.

Для новых ранних отказов при отсутствующем либо повреждённом baseline предлагается отдельный формат `geom-contextless-v1:sha256:...`. Он не требует чтения geometry baseline и не подставляет фиктивный baseline. Применение этого формата не разрешает mutation без baseline: это способ идентификации запроса, а не обход доменных проверок.

Envelope нового формата включает собственную версию, `replace_feature_geometry`, workOrderId/editVersionId/featureId/actorUserId, defaultStateId/baseNetworkRevision из root, исходный draftVersionToken, policy snapshot из EditVersion и полную geometry запроса. Каждая координата округляется существующим алгоритмом по policy версии; type, количество и порядок coordinates сохраняются. Отдельный vertexIndex не вычисляется: без baseline нельзя достоверно определить изменённую вершину.

Не включаются geometry или digest baseline, current geometry/revision, состояние доступа, lifecycle, причина отказа, timestamp и correlationId. CommandId остаётся ключом registry. Policy и root provenance берутся из существующей версии и считаются неизменными в рамках её lifecycle; исправление данных baseline не меняет эти поля.

При существующей command row алгоритм сравнения выбирается исключительно по сохранённому формату fingerprint. Команда `geom-contextless-v1` остаётся в этой ветке после ремонта baseline; fingerprint не обновляется. Неизвестный формат — ошибка протокола без mutation, а не разрешение исполнить команду заново. Для старого `geom-v1` не допускается fallback-сравнение вместо исходного алгоритма.

После действующих access/lifecycle guards и проверки identity:

| Повтор | Результат |
| --- | --- |
| Те же поля и одинаковая округлённая geometry у contextless-команды | Первоначальный terminal result |
| `1`, `1.0`, `1e0` | Эквивалентные числа |
| Координаты округляются одинаково, хотя записаны разными числами | Эквивалентны для contextless-команды |
| Другой исходный token | `COMMAND_ID_REUSED` |
| Другая geometry после округления, count или порядок координат | `COMMAND_ID_REUSED` |
| Другой actor/target | `COMMAND_ID_REUSED`, когда текущие guards разрешают раскрыть этот ответ |
| Baseline восстановлен после обычного contextless rejection | Исходный отказ; новая mutation требует нового CommandId |

Сохраняется исключение Дня 2 для `retry_on_access_change`: matching identity позволяет продолжить проверки после восстановления доступа, а не автоматически исполнить mutation. Формат fingerprint и identity при переходе `rejected -> running` остаются неизменными, как требует существующий DB trigger.

Новый формат хранится в существующем TEXT `request_fingerprint`; добавление столбца или смена старых значений для этого раздела не требуется. Обязательны golden vectors нового формата и проверки ремонта baseline, grid-equivalent retry, changed token/payload, сохранения правил `unmatched_structure` и неизвестного prefix.

## Раздел дизайна 3. Отказы, доступ и приоритет проверок — согласован

Пользователь подтвердил границы registry, порядок проверок, разделение ошибок и исключение для access retry.

### Граница registry

Для новой команды с существующими адресуемыми version/feature ожидаемый доменный отказ внутри use case сохраняется как terminal result. Это включает stale, structure/spatial/AOI errors, multiple-feature restriction, неeligible feature, повреждённый контекст, закрытый lifecycle и отказ роли, если проверка роли произошла внутри use case. До входа в use case request/auth errors не резервируют ID.

Физически отсутствующий target не создаёт registry row: нет допустимой FK-ссылки. Несоответствие пары workOrderId/editVersionId также не привязывает команду к версии по одному найденному UUID. Существующий, но недоступный по assignment target даёт сохраняемый 404 `EDIT_VERSION_NOT_FOUND` с `retry_on_access_change=true`.

Для записи раннего отказа разрешено внутреннее чтение root/target и построение fingerprint, но ответ не раскрывает скрытые context details. При доступном для fingerprint baseline используется `geom-v1`; если baseline отсутствует/повреждён и не позволяет построить прежний fingerprint, используется согласованный contextless-формат. Это применимо и к первичному access/lifecycle/role отказу, совпавшему с проблемой baseline; наружный приоритет ошибки от этого не меняется.

Занятый CommandId никогда не перезаписывается новым отказом. Если текущие guards запрещают раскрыть старый результат, возвращается текущий отказ доступа/lifecycle без изменения исходной command row. Если guards пройдены, другое содержимое занятого ID даёт `COMMAND_ID_REUSED`. При history без registry ID также не используется для новой mutation.

### Порядок наружных результатов

1. Проверка actor/активной роли: `ROLE_NOT_ALLOWED`.
2. Наличие и видимость адресуемого target: `EDIT_VERSION_NOT_FOUND`.
3. Lifecycle: `SAVE_CONTEXT_CLOSED`.
4. Идентичность занятого ID и replay сохранённого результата. Для matching обычного rejection не повторяется доменная валидация.
5. Для новой исполняемой команды — token: `DRAFT_VERSION_STALE`.
6. Проверки исходного контекста, ограничения одной feature и candidate geometry.

Как и в Дне 6, подготовка идентичности обычного `geom-v1` требует пригодного baseline. Новый протокол обеспечивает запись раннего отказа, но не вводит возможность исполнить mutation при непригодном baseline. Для новой команды обнаруженная на подготовке идентичности неeligible feature/непригодный baseline сохраняет ранний результат `FEATURE_NOT_EDITABLE`/`WORK_ORDER_CONTEXT_INVALID`, даже если token также устарел. Это исключение должно иметь отдельный тест, а не скрываться за общей схемой приоритетов.

В фазе domain validation сохраняется порядок текущего repository: целостность current/baseline/AOI, пространственная пригодность исходных данных, другая изменённая feature, структура candidate/перехода, spatial geometry, покрытие candidate AOI. Таким образом, недопустимая и одновременно выходящая за AOI candidate даёт `GEOMETRY_INVALID`; сломанный AOI даёт `WORK_ORDER_CONTEXT_INVALID`, а не ошибку пользовательской geometry.

### Возобновление после восстановления доступа

Только rejected row с `retry_on_access_change=true` допускает новую проверку той же команды; schema разрешает этот флаг только для 404 `EDIT_VERSION_NOT_FOUND`. Отказ роли, closed lifecycle, stale, geometry и context rejection являются обычными terminal results без такого флага.

Пока assignment не позволяет доступ, прежняя matching access-rejected row не переписывается. После восстановления доступа, при прохождении текущих role/lifecycle guards и совпадении fingerprint, выполняется `rejected -> running`, затем проверка исходного token и domain validation. Результат может быть success либо новый terminal rejection, например stale; если новая причина не access, retry flag сбрасывается. Новый token под прежним ID остаётся reuse.

Технический сбой такой попытки вызывает rollback к прежнему access rejection. Восстановление доступа не разрешает раскрыть или выполнить чужую команду: actor и target входят в immutable identity.

### Ошибки и точность replay

Сохраняются HTTP status, code и message; `correlationId` принадлежит текущему HTTP-запросу и не является частью immutable terminal result. Ошибка БД, lock timeout, сбой INSERT event, неизвестный fingerprint format или нарушение repository protocol не преобразуются в terminal domain rejection.

## Раздел дизайна 4. События, Revert и приёмка M2 — согласован

Пользователь подтвердил контракт событий, Revert и матрицу приёмки M2.

### События

Каждая новая команда Дня 7, фактически изменившая current geometry, добавляет ровно одно событие. Event type определяется итоговым operation, а не названием UI-кнопки: `updated` означает `change_set_persisted`, `unchanged` — `change_set_cleared`. Повторный Save изменённой линии создаёт новое persisted event, если отличается от текущей geometry.

Before — фактическая geometry непосредственно перед mutation, after — сохранённая geometry после неё; использовать baseline в качестве before для всех Save нельзя. Значения берутся из `GeometryWriteResult` в исходном EWKB. Событие также содержит CommandId, actor, feature, version/work order/default state IDs, base network revision, draft revision до/после и время БД.

Новая revision равна предыдущей +1. PK CommandId и UNIQUE `(edit_version_id, draft_revision_after)` обеспечивают верхнюю границу числа событий; integration tests подтверждают нижнюю границу — обязательное наличие события на каждую новую content-changing команду. Обычные no-op, rejection и replay не создают event и не повышают revision.

Сохраняются существующие append-only triggers и проверки provenance. История остаётся после физического удаления версии/registry; события не добавляются задним числом для команд Дня 6. Если в старой версии уже revision 5 без history, первое новое изменение создаёт event 5 -> 6; отсутствие событий 1 -> 5 само по себе не проваливает M2.

### Revert

Revert остаётся обычным Save с baseline geometry, новым CommandId и актуальным token. При отличающемся current восстанавливается точный baseline EWKB, включая исходные off-grid координаты, operation становится `unchanged`, `hasPersistedChangeSet=false`, `basicValidation=null`; revision увеличивается на один и создаётся `change_set_cleared`.

Если current уже равен baseline, запрос с новым ID и актуальным token является successful no-op без event/revision increment. Повтор первоначального успешного Revert возвращает его сохранённый результат, даже если последующий Save опять изменил geometry; replay не выполняет второй Revert. Новая Revert-команда со stale token сохраняет terminal stale rejection.

Revert не становится режимом ремонта повреждённого контекста: существующие проверки baseline/current/AOI и ограничения редактирования сохраняются. Baseline, properties, associations и network versions не изменяются.

### Матрица приёмки

| Группа | Обязательные наблюдаемые сценарии |
| --- | --- |
| Последовательность | Save A -> Save B -> Revert; точная цепочка before/after, типы persisted/persisted/cleared и revisions +1 |
| No-op/replay | No-op на baseline и updated current; повтор Save/Revert после более поздней команды; неизменность текущего состояния и истории |
| Rejections | Отдельные stale/reuse/structure/invalid geometry/outside AOI/context/multiple-feature/eligibility/role/lifecycle случаи; committed result и отсутствие mutation/event |
| Несколько нарушений | Приоритет role/access/lifecycle, replay до token, ранняя непригодность baseline до token, invalid geometry до outside AOI |
| Повреждённый baseline | Первый durable rejection; ремонт baseline; exact и grid-equivalent retry возвращают исходный отказ; changed token/geometry дают reuse |
| Access recovery | Отказ при чужом assignment; неизменный повтор; восстановление доступа с success или stale; rollback повторной попытки сохраняет прежний отказ |
| Атомарность | Ошибки после mutation, revision, finalization, INSERT event и при commit; независимое чтение подтверждает rollback; ошибка commit rejection не выдаётся как подтверждённый domain result |
| Конкуренция | Одинаковые success/rejection команды; разные ID с одним token; один глобальный ID разных versions; commit/rollback победителя; Save/Open без обратного порядка locks |
| Constraints | Невозможность committed running, изменения terminal identity, второго event, UPDATE/DELETE/TRUNCATE history; существующие migration/metadata гарантии |
| Совместимость | Старый geom-v1, unmatched_structure, off-grid baseline; старые успешные команды без event не создают history при replay |
| Долговечность | Replay success/rejection через новую session и новый service instance после commit; история содержит исходные значения и IDs |

На уровне unit проверяются orchestration и fingerprint vectors. DB-сценарии используют PostgreSQL/PostGIS и независимое чтение committed состояния через isolated test runner с отдельной `_test` БД; mock-only проверки не заменяют доказательство атомарности и конкуренции. Повторяются релевантные Open, geometry, command/event constraints и repository protocol tests. Существующие тесты временных ограничений Дня 6 меняют ожидаемые результаты на принятый контракт Дня 7.

M2 считается достигнутой только после реализации, успешного прогона этой матрицы и фиксации фактических результатов проверки. Текущее обсуждение M2 не закрывает. Endpoint/readback, HTTP correlationId integration, UI и сквозной browser/backend restart scenario остаются соответствующими следующими этапами календаря; новая DB session здесь не объявляется доказательством реального process restart.

Четыре раздела собраны в [принятую спецификацию](2026-10-11-day-7-rejections-events-revert-design.md). Подготовлен [план реализации](2026-10-11-day-7-rejections-events-revert-plan.md) для просмотра и выбора способа исполнения.

## Agent memory

Отдельная запись не создаётся: факты кода и незакрытые вопросы сохранены здесь; дублирование анализа в memory не добавляет устойчивого объяснения.
