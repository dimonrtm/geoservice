# День 8 — анализ API и durable readback

Дата анализа: 2026-10-12. Календарная задача: понедельник, 10 августа 2026 года.
Статус: цельная спецификация принята пользователем 2026-10-12; сохранена parsing boundary Дня 4. Подготовлен отдельный план реализации для проверки и выбора способа исполнения. Реализация не начата.

## Важная поправка после повторной сверки источников

2026-10-12 пользователь спросил: «А что про это сказано в Wiki возможно я что-то напутал». Повторная сверка выявила пропуск первоначального анализа: готовый `web_api/parsers/geometry_save_request.py`, его тесты и раздел 4 принятой спецификации Дня 4 не были учтены при Q2–Q3. Эта поправка имеет приоритет над прежней формулировкой, что граница таких ошибок не определена требованиями.

`docs/sprint_2/2026-10-08-day-4-geometry-design.md:86–97` явно относит другой geometry type, пустую/одноточечную LineString, Z/M и неправильные XY-пары к ошибкам ДО use case, без резервирования CommandId. Исправленный request может использовать тот же ID. Parser реализует эти ограничения, а `web_api/tests/test_geometry_save_request_parser.py` содержит соответствующие проверки. Точный Decimal parsing также уже реализован, а не требует создания с нуля.

`Code_wiki/архитектура/edit_geometry_determinism.md` ссылается на этот parser и описывает строгий XY LineString. `Wiki/value_objects/command_id.md` требует сохранять committed domain rejection, но не объявляет любую ошибку формы geometry доменным отказом. Для принятого запроса семантическая идентичность учитывает canonical geometry; различие сырых координат не всегда означает новое намерение. Для unmatched_structure спецификация Дня 4 уже задаёт точное числовое сравнение без grid-rounding.

Q2–Q3 и прежняя редакция раздела 2 фактически пересматривали границу Дня 4. После объяснения противоречия пользователь подтвердил сохранение прежнего parsing contract («Да»). Q2–Q3 заменены этим решением; readback и строгая форма ошибок остаются принятыми.

Предложение `geom-rejected-v1` снято: это не требование Wiki. Новый формат и обобщённое входное geometry-дерево не нужны. Вывод о пробеле кода для короткой линии был ошибочным относительно исходного публичного контракта: parser намеренно не допускает такой запрос внутрь Save.

Итоговое решение: подключить существующий parser к PUT и оставить доменный replay существующим протоколам. Цельный актуальный дизайн и матрица проверок приняты: [спецификация Дня 8](2026-10-12-day-8-api-readback-design.md). Дальнейшие шаги — в [плане реализации](2026-10-12-day-8-api-readback-plan.md).

## Цель и порядок работы

Предоставить UI публичный Save и устойчивое чтение current geometry, token, persisted change set, validation и baseline для Revert без знания seed coordinates. Пользователь запросил глубокий анализ кода, Wiki и DDD_Wiki, вопросы по одному в отдельных сообщениях и предложения решений только после устранения неоднозначностей. Все артефакты обсуждения сохраняются в `docs/sprint_2/`.

Порядок: исследование → последовательные уточнения → варианты решения → согласование дизайна. Изменение публичного контракта рассматривается как архитектурная задача. Этот документ является анализом, а не утверждённой спецификацией.

## Что установлено по коду

| Область | Текущее состояние | Значение для Дня 8 |
| --- | --- | --- |
| `web_api/api/work_orders.py` | Есть assigned list, open и workspace GET; geometry PUT отсутствует | Требуется публичная граница уже существующего Save |
| `use_cases/services/edit_version_service.py` | `save_geometry` владеет одной транзакцией; terminal rejection выбрасывается после commit; replay возвращает сохранённый payload | HTTP-обвязка не должна менять атомарность и смысл replay |
| `use_cases/schemas/edit_version/geometry_save_in.py` | `GeometrySaveRequest` — dataclass, принимает внутренний `GeometryValue` | Это ещё не строгая входная HTTP-схема |
| `domain_services/edit_geometry/types.py`, `web_api/parsers/geometry_save_request.py` | GeometryValue использует Decimal XY; готовый parser проверяет строгую форму LineString и сохраняет точные числа | Подключить parser к PUT без смены его правил |
| `use_cases/schemas/edit_version/geometry_save_out.py` | Есть dataclass результата и builder JSON payload, но не публичная Pydantic response model | Runtime JSON и документируемый OpenAPI contract ещё не соединены |
| `infrastructure/postgresql/sql/workspace_aggregate.sql` | Current features и associations читаются одним SQL; features ограничены AOI; геометрия передаётся через EWKB | Readback уже читает БД, но ещё не собирает полный контракт редактирования |
| `repository_rows/workspace.py`, `schemas/workspace/edit_version_workspace_out.py` | Нет draft revision/token, validation и changeSet | Изменение требуется по всей цепочке SQL → row → service → schema |
| `use_cases/services/workspace_service.py` | Проверяет активного Editor, assignment, состояния in_progress/open; формирует вложенный `workOrder.editVersion` | Guards существуют; новый контракт должен учитывать текущую вложенность |
| `web_api/api/exception_handlers.py` | AuthApiError и WorkOrderApiError имеют ровно code/message/correlationId; обработчика RequestValidationError нет | Строгая форма ещё не охватывает ошибки разбора body/path; legacy handlers также имеют другие формы |
| `web_api/api/auth.py` | Проверяет текущего пользователя из БД, активность и Editor role | Отказ до use case не резервирует CommandId; это отличается от доменного отказа внутри Save |
| `use_cases/services/auth_service.py` | `get_user_by_id` завершает собственную transaction до возврата DTO | Предварительное auth-чтение само по себе не оставляет открытую transaction перед Save |
| `apps/frontend/src/contracts/work-orders.ts` | Workspace содержит прежние поля; Save/readback расширения нет | TypeScript contracts и API client относятся к Дню 9 |

Пути backend в таблице даны относительно `apps/backend/utility_service/`.

## Уже принятые ограничения

- Endpoint задан ТЗ: `PUT /api/v1/work-orders/{workOrderId}/edit-versions/{editVersionId}/features/{featureId}/geometry`.
- Request содержит `commandId`, `draftVersionToken`, `geometry`; неизвестные поля запрещены. Token — непустая строка, CommandId — UUID, geometry — LineString.
- Revert — новая Save-команда с baseline geometry, текущим token и новым CommandId.
- Без сохранённых отличий `hasPersistedChangeSet=false`, `basicValidation=null`, `changeSet=null`; после Revert token не возвращается к первоначальному значению.
- При отличии changeSet содержит featureId, vertexIndex, baselineGeometry и operation.
- Baseline относится к исходному `default_state_id` версии, а не к новому активному Default и не к локальной fixture UI.
- Геометрия результата и baseline не должны получать дополнительное округление при сериализации readback.
- Ошибки request/auth до use case не занимают CommandId. Обычные domain rejections адресуемой команды сохраняются; access rejection имеет особое правило продолжения из Дня 7.
- CorrelationId относится к текущему HTTP-запросу; не является частью сохранённого terminal result.
- Сохранённый ответ старой команды может содержать историческую геометрию и token. Он не является обещанием актуального workspace.
- S2-X01 оформлена отдельно от календарных дней; её API/UI recovery доработки не следует автоматически считать частью Дня 8.

Основания: ТЗ Sprint 2; принятые спецификации Дней 6–7; `2026-10-12-save-recovery-rules-decision.md`; `2026-10-12-s2-x01-save-recovery-followup.md`.

## Сопоставление с Wiki и DDD_Wiki

1. `DDD_Wiki/aggregates/edit_version.md`: агрегат владеет current snapshot и aggregate token. Однако описание реализации как read-only устарело относительно существующего Save service. Поле token при open упоминается шире, чем явно поставленная задача workspace readback.
2. `Wiki/specifications/edit_version_has_persisted_change_set.md`: source of truth — baseline и full current snapshot, а не история операций. Следовательно, последний successful command сам по себе не доказывает актуальный change set.
3. `DDD_Wiki/state_machines/edit_version_persisted_change_set.md`: updated/unchanged отражают текущий diff; rejection не меняет persisted state. No-op/retry не создают событие и не двигают token.
4. `DDD_Wiki/state_machines/edit_version_save_request.md` уже уточнён 2026-10-12: running существует только внутри transaction, committed OutcomePending и polling не вводятся. Старый replay и текущие данные различаются.
5. `DDD_Wiki/state_machines/editor_save_recovery.md` и `Wiki/policies/editor_recovery_policy.md` отделяют неизвестность для редактора от серверного результата. Это ограничение смысла API, а не основание вводить новую серверную сущность.
6. `DDD_Wiki/invariants/edit_version_persisted_edit_invariants.md` всё ещё упоминает pending outcome; этот фрагмент расходится с обновлённой state machine.
7. Агрегат, инварианты и `Wiki/value_objects/draft_version_token.md` требуют current object/token в stale error. Это расходится со строгой формой из ТЗ и прямого запроса пользователя. В анализе приоритет имеет явно заданная форма из трёх полей; старые страницы автоматически не исправлялись.
8. `Wiki/specifications/edit_version_basic_draft_validation.md` описывает более широкий доменный summary, чем публичный контракт. Спецификация Дня 6 прямо сохраняет сокращённые API-поля и null при отсутствии diff; расширение до всех доменных полей не является неявным требованием Дня 8.
9. `Code_wiki/архитектура/edit_version_persistence.md` содержит stale-предупреждение: основной текст описывает repository до появления orchestration Дней 6–7. Фактическое наличие Save подтверждено кодом, а не старым описанием.

## Риски и пробелы, требующие уточнения

- Граница HTTP validation/domain rejection определена Днём 4 и подтверждена после повторной сверки: строгий XY LineString с минимум двумя вершинами; остальные format errors не резервируют ID.
- Область строгого error shape уточнена в Q1: новый PUT и workspace GET. Для request errors в разделе 2 принят код REQUEST_VALIDATION_ERROR.
- Readback validation относится к текущему сохранённому draft и должна воспроизводиться после restart (ТЗ AC-08, Wiki basic draft validation). Источник/способ построения summary остаётся техническим вопросом; нельзя подменять его результатом произвольной исторической команды. Новая проверка при каждом GET по изменившемуся внешнему контексту требованиями не задана.
- Повреждённый read context: несколько changed features, отсутствие baseline, несоответствие operation фактическому diff, изменённая feature вне AOI. Нельзя молча формировать нормальный пустой changeSet и терять отличие всей версии. Существующий контракт `Code_wiki/архитектура/api_and_realtime.md` определяет `WORKSPACE_CONTEXT_INVALID`, когда workspace нельзя сформировать из текущих данных; отдельный режим частичного просмотра требованиями не задан.
- Согласованность current geometry, token и baseline при одновременном Save/GET. Существующее чтение одним SQL — важная исходная характеристика.
- Точный JSON transport: Decimal-значения внутренней модели, координаты около midpoint и off-grid baseline; транспорт не должен незаметно менять результаты ранее утверждённой canonicalization.
- Граница результата дня: календарный план явно относит TypeScript contracts/API client к Дню 9; это не открытый вопрос Дня 8. Token в open response упомянут в общей доменной модели, но текущая задача явно требует его в workspace; необходимость расширения open не следует автоматически из задачи. Сквозной restart-сценарий относится к приёмке спринта и последующим этапам; API и service проверки Дня 8 должны подготовить его.
- Полнота API error mapping и OpenAPI: runtime responses и автоматически документируемые схемы могут различаться, особенно для 422.

## Наблюдаемое покрытие и будущие доказательства

Существующие `web_api/tests/test_work_orders_api.py` проверяют list/open/workspace, используют service doubles и auth dependency override. `use_cases/tests/test_workspace_service.py` проверяет projection, роль, assignment, lifecycle и отсутствие AOI. `infrastructure/tests/test_work_order_repository_workspace_aggregate.py` проверяет один SQL round trip и mapping.

Эти проверки сами по себе не доказывают HTTP Save → commit → workspace readback. Для приёмки предстоит определить покрытие: начальное состояние, Save, повтор Save, stale, Revert, no-op, потеря доступа, исторический replay после более нового Save, новая session и restart. OpenAPI review должен сверять реальную схему request, response и ошибок с runtime, включая nullable поля и запрет неизвестных полей.

В текущем анализе тесты не запускались; выводы основаны на чтении кода и документов. Продуктовый код, Wiki и DDD_Wiki не менялись. Отдельная agent memory не нужна: результаты исследования сохраняются здесь.

## Уточнения пользователя

### Q1. Область строгой формы ошибок

Ответ пользователя 2026-10-12: вариант 1. Строгая форма `{code,message,correlationId}` обязательна для нового geometry PUT и workspace GET, включая ошибки входных данных. Расширение этого требования на остальные work-order endpoints и legacy API в День 8 не входит.

### Q2–Q3. Короткая линия и неподдерживаемый тип — первоначальные ответы заменены

Первоначально пользователь выбрал durable rejection для короткой LineString и другого корректного GeoJSON type. После обнаружения явного противоположного правила Дня 4 агент объяснил расхождение, и пользователь подтвердил сохранение исходной границы. Действующее решение: эти запросы отклоняет parser до use case, registry не меняется; исправленный request может использовать тот же CommandId. Это не дефект Save service.

### Q4. Смысл basicValidation при readback — снят после проверки требований

На предложенный выбор между проверками в момент Save и новой проверкой при GET пользователь спросил: «Это есть в требованиях?» Повторная сверка показала, что такой продуктовый выбор был избыточным:

- `Wiki/specifications/edit_version_basic_draft_validation.md:17` задаёт синхронное вычисление summary после Save; summary подтверждает persisted draft.
- `docs/sprint_2/2026-07-31-sprint-2-technical-requirements.md:395` (AC-08) требует совпадения сохранённых geometry, token, validation и baseline change set после refresh, новой HTTP session и backend restart.
- `Wiki/commands/update_edit_version_feature_geometry.md:42` требует readback того же persisted state.

Из этих источников следует требуемая семантика: readback показывает validation текущего сохранённого draft. Повторная проверка по изменившемуся внешнему контексту на каждом GET не задана. Физическое хранение summary или его воспроизводимое вычисление источники однозначно не предписывают; это вопрос последующего технического дизайна, а не новое требование к пользователю. Вопрос снят по источникам, ответ пользователя за выбор варианта не выдаётся.

### Q5. Нечитаемая структура входной geometry

Ответ пользователя 2026-10-12: «Да». Отсутствующее поле coordinates или нечисловая координата относятся к request validation без регистрации CommandId. После итоговой сверки короткая LineString и неподдерживаемый geometry type также относятся к request validation. Публичный parser принимает только LineString; универсальный разбор остальных GeoJSON types не добавляется.

Основные продуктовые требования после Q1–Q5 понятны. Дальнейшие вопросы о построении readback, представлении отклонённого запроса, сериализации и OpenAPI рассматриваются как технический дизайн на основе этих требований, а не передаются пользователю как повторный выбор уже заданного поведения.

## Сводное понимание перед дизайном

День 8 завершает backend-контракт уже реализованного Save/Revert. Новый PUT возвращает результат конкретной команды; workspace GET возвращает актуальное сохранённое состояние версии. Readback содержит достаточные данные для Revert без seed coordinates. Формат ошибок строгий для этих двух endpoints, включая request validation. Request, не прошедший строгий parser Дня 4, не занимает CommandId; нарушения доменных правил принятой линии дают durable rejection по существующим правилам Дней 6–7.

Не добавляются UI recovery из S2-X01, TypeScript/API client Дня 9, новый серверный pending state, polling, отдельная команда Revert или повторная проверка качества по внешнему контексту при каждом GET. Существующие права, lifecycle, атомарность, no-op и replay сохраняются.

## Технические выводы дополнительного чтения

- `geometry_codec.py` предназначен для допустимой хранимой Point/LineString: EWKB → Decimal(repr(binary64)) и проверяемое обратное преобразование. Использовать его как парсер произвольной отклоняемой geometry нельзя: пустая/короткая линия и другие типы не представимы в этом контракте.
- `geometry_document` и fingerprint-протоколы рассчитаны на внутренний GeometryValue. Это соответствует строгому parser Дня 4; расширение representation и новый протокол сняты. Существующие `geom-v1` и `geom-contextless-v1` сохраняются.
- `edit_geometry_context.sql` уже показывает корректную связь baseline через `ev.default_state_id` и поиск changed features всей версии без AOI-фильтра. Это источник правил для readback, но Save repository использует transaction-bound handles и root lock; механически вызывать его mutation protocol из GET не требуется.
- Последний command payload не заменяет workspace: replay историчен, а no-op другой команды может иметь другой смысл относительно текущего diff. Current/baseline и revision должны относиться к одному согласованному снимку.

## Рассмотренные подходы

### A. Расширение существующего workspace aggregate — предпочтительный

Сохранить текущую цепочку `WorkOrderRepository.get_workspace_aggregate` → `WorkspaceService` → `WorkspaceOut`. Дополнить единый SQL snapshot revision и baseline/current данными для производного change set; проверить согласованность всей версии, независимо от AOI-фильтра отображаемых features. Вычислять vertexIndex из фактического diff, возвращать точный baseline через существующий codec, строить сокращённый validation summary для текущего допустимого persisted draft. Повреждение контекста не превращать в нормальный пустой changeSet.

Новый PUT использует готовый parser и существующий Save service. Строгие transport errors ограничены двумя согласованными endpoints. OpenAPI описывает строгий XY LineString, а не обобщённое GeoJSON-дерево.

Преимущества: сохраняется один SQL snapshot без read locks; меньше новых границ и зависимостей; нет основания для новой таблицы или дублирования baseline. Цена: более насыщенная workspace projection и проверки HTTP-интеграции.

### B. Выделенный репозиторий чтения draft workspace

Сделать отдельный read repository/projection для current, baseline, token и change set, с явным согласованным snapshot всех частей ответа. PUT, error contract и durable rejection такие же, как в A. Если projection собирается несколькими SELECT, согласованность нельзя считать обеспеченной одной лишь READ COMMITTED transaction: потребуется отдельно выбрать snapshot strategy.

Преимущества: ответственность чтения отделена от WorkOrderRepository, удобнее развивать более сложный read model. Цена: новая зависимость, перенос существующего mapping, больше регрессионной проверки и риск нарушения snapshot consistency при раздельных запросах. В пределах одной линии Sprint 2 потребность в таком выделении пока не выявлена.

Выбран подход A. Пользователь 2026-10-12 после объяснения назначения readback и состава расширения подтвердил: «Да принимаю расширение readback». Это согласование направления; точный контракт и технические разделы ниже ещё обсуждаются. Реализация не начата.

## Раздел дизайна 1 — контракт workspace readback

Статус раздела: принят пользователем 2026-10-12 («Да принимаем»).

Существующий `GET /api/v1/work-orders/{work_order_id}/edit-versions/{edit_version_id}/workspace` сохраняет вложенность и прежние поля. В `workOrder.editVersion` добавляются четыре обязательных поля:

| Поле | Контракт |
| --- | --- |
| `draftVersionToken` | Непустая строка, сейчас `str(draft_revision)`; клиент использует как opaque token |
| `hasPersistedChangeSet` | Boolean; отражает текущий diff всей версии относительно её baseline |
| `basicValidation` | Сокращённый summary ТЗ при допустимом непустом persisted diff; иначе null |
| `changeSet` | Объект для единственной изменённой линии либо null |

`changeSet` содержит `featureId` (UUID), `vertexIndex` (индекс с нуля в baseline), `baselineGeometry` (полная исходная LineString), `operation` (при непустом diff только `updated`). Текущая геометрия остаётся в существующем `features`; дублировать её в changeSet не требуется. Baseline относится к `EditVersion.default_state_id`, не к текущему активному Default. Координаты current и baseline сериализуются без дополнительной canonicalization.

Нормальные состояния:

- До первого изменения: false/null/null и текущий token.
- После Save непустого diff: true/summary/changeSet; summary содержит geometryStatus=passed, aoiStatus=passed, positionalAccuracyStatus=POSITIONAL_ACCURACY_UNVERIFIED, dirtyRelativeToBaseline=passed.
- После Revert: false/null/null; token отражает уже выполненный Revert, не сбрасывается на 1.
- No-op или повтор команды не меняет актуальный readback; отдельное чтение всегда отражает текущий snapshot, а не исторический payload retry.

Все части workspace строятся из одного SQL snapshot: геометрия, revision, исходная геометрия, assignment и lifecycle. Вычисление diff и проверка согласованности не должны ограничиваться только features, видимыми через AOI-фильтр. При этом прежний AOI-фильтр отображаемых features и правило включения associations сохраняются. Если изменённая feature скрыта фильтром или данные нарушают контракт единственной изменённой линии, workspace не выдаёт ложное отсутствие изменений.

Если нужный baseline отсутствует, фактический diff противоречит operation или превышает допустимый scope, возвращается `422 WORKSPACE_CONTEXT_INVALID` в строгой форме; данные не исправляются при чтении. Это проверка возможности достоверно сформировать readback, а не новая проверка качества по изменившемуся внешнему контексту.

Существующие проверки сохраняются: активный Editor; чужая/отсутствующая версия маскируется как `404 EDIT_VERSION_NOT_FOUND`; несовместимый lifecycle даёт `409 EDIT_VERSION_STATE_CONFLICT`. GET не пишет registry/history, не меняет revision и не использует mutation-lock protocol Save.

## Раздел дизайна 2 — публичный Save API и ошибки

Статус раздела: принят с последующей поправкой пользователя — сохранить parsing boundary Дня 4.

### Запрос

`PUT /api/v1/work-orders/{work_order_id}/edit-versions/{edit_version_id}/features/{feature_id}/geometry` принимает JSON object с обязательными `commandId`, `draftVersionToken`, `geometry`. Path IDs и commandId — UUID; token — непустая строка без приведения числа к строке и без изменения клиентского значения. Неизвестные поля запрещены. Actor определяется авторизацией, не принимается из body.

Используется готовый parse_geometry_save_request: только LineString, минимум две XY-пары, конечные JSON numbers в диапазонах EPSG:4326. Неизвестные/повторяющиеся поля, другой тип geometry, короткая линия, Z/M, неправильная вложенность и числовые ограничения проверяются до use case. Такие ошибки, неверные path UUID и прочие request validation errors отображаются в 422 REQUEST_VALIDATION_ERROR без registry row.

### Доменные отказы

Принятая parser линия проверяется существующим Save service: stale token, недоступный/неeligible target, нарушение структуры относительно baseline, самопересечение, нулевые сегменты, AOI и другие действующие guards. Их коды, приоритет, reservation и terminal replay сохраняются по Дням 6–7. Двухвершинный request проходит parser, но относительно eligible baseline из трёх вершин получает GEOMETRY_STRUCTURE_CHANGED; это отличается от одноточечного format error.

### Успех и replay

Успех возвращается с HTTP 200 только после commit. Payload сохраняет существующие `commandId`, `commandState=succeeded`, `draftVersionToken`, `operation`, `hasPersistedChangeSet`, `updatedFeature{id,geometry}`, `basicValidation`. Новый признак replay не вводится. No-op и Revert имеют тот же формат; при отсутствии diff basicValidation=null.

Matching retry возвращает прежние status/payload успешной команды либо прежние status/code/message обычного отказа при сохранении текущих access/lifecycle guards. CorrelationId формируется для текущего HTTP-запроса. Исключение access retry остаётся в рамках принятого Дня 7. Старый успешный replay может иметь более старый token, чем свежий workspace, и не заменяет readback актуального состояния.

### Строгая форма и авторизация

Для нового PUT и workspace GET ошибки имеют ровно `{code,message,correlationId}`. REQUEST_VALIDATION_ERROR документируется вместо стандартной FastAPI HTTPValidationError-схемы для этих операций. Ошибки auth, role, assignment, lifecycle, command identity, stale, geometry и internal error также должны быть отражены в API contract/OpenAPI; HTTP framework errors на этих маршрутах не должны выдавать дополнительный detail.

Невыполненная авторизация не входит в Save use case: AUTH_REQUIRED, USER_INACTIVE и ROLE_NOT_ALLOWED сохраняют текущие значения. Assignment проверяется сервисом; ошибка маскирует чужой target как EDIT_VERSION_NOT_FOUND. Новый request error handler ограничен двумя согласованными endpoints и не меняет формат остальных API.

Для stale сохраняется `409 DRAFT_VERSION_STALE` без current geometry/token в error body: актуальные данные доступны через workspace GET. Клиентские retries, refresh orchestration и UI относятся к последующим дням.

## Раздел дизайна 3 — итоговая техническая граница и проверки

Готовый parser, GeometrySaveRequest, Save service, transaction protocol и оба fingerprint-формата используются без расширения области входных геометрий. Предложение отдельного типа отклоняемого geometry-дерева и нового hash-протокола снято после сверки требований.

Для реализации остаются HTTP adapter и OpenAPI, локальный mapping ошибок, workspace SQL/row/service/schema projection и проверки. Матрица включена в принятую спецификацию: API contract, workspace unit/repository, HTTP + реальная БД, replay/no-op/revert, concurrency snapshot, точность чисел и повреждённый readback.

При подготовке плана в `web_api/main.py` обнаружено отсутствие PUT в CORS allow_methods. Разрешение метода для существующих origins и preflight test включены в план как необходимое условие работы согласованного Save из браузера. Существующий off-grid integration test изменяет только current geometry; для нового consistency contract план предусматривает создание согласованной baseline/current fixture вместо ослабления проверки.

Новая session не выдаётся за фактический restart процесса. Полный browser/backend restart smoke остаётся обязательным результатом спринта на предусмотренном календарём этапе. Тесты реализации в рамках анализа не запускались.
