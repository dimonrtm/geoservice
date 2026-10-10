# День 5: анализ атомарного repository context

Дата анализа: 9 октября 2026 года. День 5 — название этапа календарного плана от 31 июля; исходная дата этапа — 7 августа 2026 года.

Статус: 10 октября согласованы все три части дизайна и принята [письменная спецификация](2026-10-10-day-5-repository-context-design.md). Подготовлен [план реализации](2026-10-10-day-5-repository-context-plan.md) для проверки пользователем. Реализация не начата. Временное правило D5-Q1 требует последующего доменного уточнения, но не блокирует текущий этап.

## Цель обсуждения

Подготовить безопасную persistence boundary для Save: блокировать нужную EditVersion, читать current feature, immutable baseline и AOI в одной транзакции, проверять пространственную допустимость через PostGIS, изменять только current snapshot. Authoritative DefaultState должен остаться неизменным. Приёмка этапа — repository integration tests и M1; полный Save/retry/Revert относится к последующим дням.

Пользователь просит глубокий анализ текущего кода, последовательные вопросы по одному и предложения только после устранения неоднозначностей. Все артефакты обсуждения сохраняются здесь, в `docs/sprint_2`.

## Порядок работы

- [x] Прочитать repository instructions, memory protocol и релевантную память.
- [x] Изучить календарь, требования, контракты Дней 2–4 и основные persistence paths.
- [x] Уточнить требования отдельными вопросами; по ответам углублять проверку кода.
- [x] После уточнений сопоставить подходы и обсудить дизайн.
- [x] Сохранить согласованный в обсуждении дизайн в письменную спецификацию и проверить её непротиворечивость.
- [x] Получить одобрение письменной спецификации и перейти к отдельному плану реализации.

## Проверенные факты текущего кода

Исходная рабочая копия чистая; исследованный HEAD — `0c10e4e`. Пути ниже относительно корня репозитория.

| Область | Источник | Наблюдение и значение для Дня 5 |
| --- | --- | --- |
| Владение транзакцией | `apps/backend/utility_service/use_cases/services/edit_version_service.py` | Open использует `session.begin()` в сервисе; repository выполняет flush. Есть образец разделения транзакции и доступа к данным, но Save отсутствует. |
| Session | `apps/backend/utility_service/infrastructure/postgresql/session.py` | Engine не задаёт isolation level явно. Session dependency не делает автоматический commit; rollback при исключении и close выполняются при выходе. Фактическая серверная конфигурация isolation не проверялась. |
| Существующие блокировки | `apps/backend/utility_service/infrastructure/postgresql/repositories/work_order_repository.py` | `get_by_id_for_update` блокирует WorkOrder. Метода блокировки EditVersion для Save нет. Open/reopen сначала блокирует WorkOrder, затем создаёт/обновляет EditVersion. |
| Root | `apps/backend/utility_service/infrastructure/postgresql/models/work_order/edit_version.py` | Есть `draft_revision`, policy snapshot, `default_state_id`, owner и WorkOrder FK. `default_state_id` не имеет FK. Наличие UUID само по себе не доказывает существование и принадлежность baseline. |
| Current | `apps/backend/utility_service/infrastructure/postgresql/models/work_order/edit_version_feature.py` | Ключ `(edit_version_id, feature_id)`, geometry и operation уже есть. CHECK проверяет non-empty, valid, SRID и соответствие type; simple и покрытие AOI этим набором не гарантируются. Допустимы также created/deleted, хотя текущий сценарий — existing feature. |
| Baseline lookup | `apps/backend/utility_service/infrastructure/postgresql/repositories/default_state_repository.py` | Имеющийся метод читает active aggregate по WorkOrder для Open. Это не специализированное чтение конкретной baseline feature по ссылке заблокированной EditVersion. Геометрия возвращается через EWKT. |
| Workspace projection | `apps/backend/utility_service/infrastructure/postgresql/sql/workspace_aggregate.sql` | Один SQL читает WorkOrder, EditVersion, AOI и current features; baseline отсутствует, root не блокируется. Features фильтруются через ST_Intersects. Такое чтение не доказывает полное покрытие и может скрыть существующую feature вне AOI. |
| AOI | `apps/backend/utility_service/infrastructure/postgresql/models/work_order/aoi.py` | Polygon/MultiPolygon, valid, non-empty, SRID 4326. Есть самостоятельная строка geometry и updated_at; модель не закрепляет AOI snapshot внутри EditVersion. |
| Чистые правила | `apps/backend/utility_service/domain_services/edit_geometry/structure.py` | `validate_transition` различает no-op и operation, проверяет одну внутреннюю вершину относительно baseline и запрещает смену изменённой вершины без Revert. Это не spatial validation. |
| Точное хранение | `apps/backend/utility_service/infrastructure/postgresql/geometry_codec.py` | EWKB decoding/encoding, XY/SRID/type guards и обратимость Decimal → binary64 уже реализованы. Codec принимает Point/LineString; AOI Polygon нельзя читать этим codec как line. |
| История и locks | `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/b7d2e9f4a6c8_first_save_schema.py` | Event context trigger блокирует root, затем command и feature. Он проверяет согласованность вставляемого события; это не универсальный запрет изменения snapshot без события. Дизайн Дня 2 требует порядка root → command → feature внутри будущего Save. |
| Конкурентные тесты | `apps/backend/tests/integration_tests/test_first_save_event_concurrency.py` | Есть реальные отдельные connections и доказательство ожидания через `pg_blocking_pids`. Проверяется event insert против удаления root, а не будущий repository Save context. |
| Точность readback | `apps/backend/tests/integration_tests/test_geometry_roundtrip.py` | Есть PostGIS/HTTP regression для off-grid baseline. Он не заменяет проверку транзакционной границы нового repository. |

## Обязательные ограничения из ранее согласованных документов

1. Дизайн Дня 4 закрепляет geometry policy в EditVersion. Save использует её, а не текущие global settings.
2. Baseline не округляется и не нормализуется повторно. Revert должен сохранять исходные storage coordinates; ST_SnapToGrid как скрытый этап недопустим.
3. Дизайн Дня 4 относит spatial validity/simple/AOI и пространственно некорректный current к следующему этапу.
4. ТЗ ограничивает change set одной feature во всей EditVersion; чистый structure guard проверяет только переданную линию и не видит другие строки snapshot.
5. Дни 6–7 добавляют revision/token orchestration, registry, terminal rejection и history. День 5 должен быть совместим с ними, но готовность repository не означает готовый Save endpoint.
6. M1 охватывает фундамент Дней 1–5. M2 отдельно подтверждает полное транзакционное сохранение.
7. DB integration выполняется только в disposable PostGIS с test-БД через `infra/db-tests.cmd` или эквивалентный isolated runner. Общая demo-БД не используется.

## Уточнения пользователя

### 1. Граница конкуренции

Пользователь выбрал вариант 1: День 5 обеспечивает согласованность между конкурирующими Save одной EditVersion. AOI, baseline и назначение WorkOrder считаются неизменными на время сохранения. Защита от их конкурентного изменения другими writers не входит в требуемую гарантию этого этапа.

Неизменность authoritative DefaultState проверяется относительно действий Save; этот выбор не вводит новую глобальную защиту baseline от любых служебных writers. Совместимость порядка блокировок с существующим Open/reopen остаётся предметом технического анализа.

### 2. Недопустимая геометрия

Пользователь подчеркнул исходный инвариант: недопустимую geometry сохранять нельзя. Save обязан проверять результат до записи. Вопрос о восстановлении уже повреждённого current был сформулирован как гипотетический дополнительный сценарий и не является запросом на такую функциональность.

Рабочее понимание scope: восстановление повреждённых данных через Save не добавляется. Структурно повреждённый current уже отклоняется по спецификации Дня 4; точное отображение пространственно повреждённого контекста будет отражено в будущем дизайне без ослабления проверок candidate.

### 3. Граница AOI — правило уже определено

Повторный вопрос пользователю оказался избыточным: `Wiki/value_objects/aoi.md`, `DDD_Wiki/invariants/edit_version_persisted_edit_invariants.md` и `Wiki/specifications/edit_version_basic_draft_validation.md` явно разрешают касание границы AOI. Вся resulting line должна быть covered by AOI; граница включена. ТЗ Sprint 2, раздел 6, пункт 10, также требует полного покрытия.

Это существующее требование, а не новое решение обсуждения. Дальнейшие вопросы необходимо сверять с каноническими Wiki/DDD_Wiki, а не только с документами спринта и кодом.

## Результат проверки оставшихся вопросов

Оставшиеся пункты проверены по коду, ТЗ, спецификациям Дней 2–4 и каноническим Wiki/DDD_Wiki. Они не требуют повторного продуктового согласования; конкретные интерфейсы будут представлены в дизайне.

- **Граница Дня 5.** Calendar отделяет repository boundary от Save orchestration Дней 6–7. В День 5 нужны чтение контекста, spatial verdict и запись geometry/operation current; финализация команд, revision/event orchestration и публичный PUT не объявляются готовыми.
- **Повреждённый контекст.** Дизайн Дня 4 уже задаёт `WORK_ORDER_CONTEXT_INVALID` для corrupted current. Схема history дополнительно требует valid/simple не только after, но и before geometry: успешный Save не может служить неявным repair такого current. Пропавшую target feature нельзя смешивать с отсутствующим baseline у существующей current feature.
- **Пространственный контракт.** Boundary разрешена; holes и MultiPolygon следуют полному covered-by. Совпадение соседних вершин временно запрещено по D5-Q1.
- **Ошибки и транзакция.** Дизайн Дня 2 разделяет ожидаемый domain rejection и infrastructure failure. Repository не должен делать commit/rollback вместо владельца транзакции; ожидаемая spatial rejection должна определяться до UPDATE, чтобы не переводить SQL transaction в aborted state.
- **M1.** Календарь требует доказательства фундамента Дней 1–5. Предложение для приёмки: новые repository tests плюс релевантная регрессия предыдущих дней и полный isolated DB suite; фактические результаты фиксируются после реализации, не заимствуются из прежнего отчёта.

## Уточняемый пример: схлопывание отдельного сегмента

Повторно проверены canonical invariants, basic validation, precision policy и исходные материалы first-save/tolerance. Запрет collapsed geometry есть, но явного определения для совпадения двух соседних вершин при ненулевой длине всей линии не найдено. Источник `RAW_inputs/meetings/tolerance_rules.md` упоминает недопустимость схлопывания ребра в обосновании precision policy; это поддерживает строгую трактовку, но не задаёт явную приёмку такого случая.

Пример: baseline `[(0,0),(1,1),(2,0)]`, candidate `[(0,0),(0,0),(2,0)]`. Endpoints и число vertices сохранены, изменена одна внутренняя вершина; первый сегмент имеет нулевую длину, вся линия — ненулевую. Существующий `validate_transition` не содержит отдельного запрета совпадения соседних координат.

По [PostGIS Geometry Validation](https://postgis.net/docs/using_postgis_dbmanagement.html#OGC_Validity), validity LineString требует ненулевой длины всей линии и минимум двух различных точек. Поэтому project-specific запрет нулевого отдельного сегмента нельзя считать автоматически выраженным только через `ST_IsValid`. Для этого примера SQL в текущем окружении не запускался.

Ответ пользователя: пока считать такой результат схлопыванием, но сохранить необходимость дальнейшего уточнения.

### Временное правило и открытое уточнение D5-Q1

**Статус: временно принято пользователем; требует уточнения доменного правила.**

В рамках Дня 5 совпадение соседних XY-координат после канонизации считается схлопыванием отдельного сегмента. Save отклоняется с `GEOMETRY_INVALID`, даже если общая длина линии ненулевая и PostGIS считает её valid/simple. Автоматическое удаление дублирующей вершины или сдвиг в другое место не выполняются.

До отдельного уточнения это правило является рабочим основанием реализации и теста `A → B → C` → `A → A → C`. Уточнение не блокирует текущую задачу.

**Что уточнить:** является ли запрет любого нулевого сегмента постоянным доменным инвариантом или нужны исключения для соседних вершин с одинаковыми координатами при ненулевой длине всей линии. Ответственного и срок пользователь пока не назначал. При подготовке спецификации перенести D5-Q1 в её раздел временных решений/открытых вопросов, чтобы рабочее допущение не стало незаметно окончательным требованием.

## Дополнительные технические выводы

### Чтение после ожидания root lock

`session.begin()` само по себе не превращает несколько чтений в неизменный snapshot при READ COMMITTED. Предлагаемая последовательность — отдельный SELECT root FOR UPDATE, затем новый SELECT контекста. После ожидания конкурирующего Save второй SELECT должен видеть его committed current и согласованный revision. Не следует объединять ожидание root lock и чтение зависимых незаблокированных строк в один сложный запрос и считать результат автоматически согласованным.

Основание: [PostgreSQL Transaction Isolation](https://www.postgresql.org/docs/current/transaction-iso.html) описывает новый snapshot на каждый statement при READ COMMITTED и особенности SELECT FOR UPDATE после ожидания. Это основание дизайна, а не результат запуска текущей БД. В integration test нужно явно подтвердить используемый isolation level.

Возвращаемые значения должны быть свежими данными запроса, а не ранее загруженным состоянием SQLAlchemy identity map. Для нового projection предпочтительны typed rows; при использовании ORM требуется явное обновление загруженного состояния.

### Порядок блокировок и соседние операции

Существующий Open/reopen берёт WorkOrder lock и затем пишет EditVersion. Будущий Save не должен после root lock запрашивать конфликтующий WorkOrder lock: это создало бы обратный порядок. При согласованном допущении о неизменных assignment/AOI/baseline достаточно читать связанные строки без дополнительного writer lock. Отдельная проверка Save против reopen нужна, поскольку reopen уже существует и изменяет last_opened_at.

Чтение feature не означает немедленную FOR UPDATE-блокировку feature. Будущая command reservation должна сохранять согласованный порядок root → command → feature. Root lock удерживается владельцем транзакции до commit/rollback; выход из repository-метода не должен его освобождать. Основание поведения locks: [PostgreSQL Explicit Locking](https://www.postgresql.org/docs/current/explicit-locking.html).

### Существование и целостность

В `cross_context_checks.py` уже есть проверки наличия DefaultState и его принадлежности WorkOrder. Это offline/read-only checker, он не вызывается в Save автоматически и не заменяет проверки конкретного locked context. Baseline выбирается по `EditVersion.default_state_id` и `feature_id`; active aggregate по WorkOrder для этой цели недостаточен.

Дизайн Дня 2 уже разрешает отсутствие registry record, если version/target feature не существует. Это важно из-за FK registry: не следует обещать durable rejection для отсутствующей строки и затем упираться в невозможный INSERT.

### Проверка geometry и запись

`validate_transition` определяет operation и no-op, но не проверяет сохранённое поле operation на согласованность с baseline/current и не обнаруживает другую изменённую feature во всей версии. Новый контекст должен дать будущему сервису необходимые сведения по всей EditVersion, без workspace-фильтра ST_Intersects.

PostGIS spatial validation проверяет именно canonical candidate, который будет записан. Полное покрытие выражает [ST_Covers](https://postgis.net/docs/ST_Covers.html), включая boundary. Valid/simple/non-empty и D5-Q1 проверяются до mutation; AOI predicate не используется как замена validity.

Mutation ограничивается строкой `(edit_version_id, feature_id)` и полями geometry/operation. Properties, feature identity/type, network_version, associations и authoritative baseline не переписываются. Полноценная атомарность snapshot + revision + registry + event будет обязанностью общего Save use case Дней 6–7 в той же transaction; repository не делает самостоятельный commit.

## Рассмотренные варианты архитектуры

| Вариант | Преимущество | Цена и ограничения |
| --- | --- | --- |
| Отдельный `EditGeometryRepository` с typed context, на существующей AsyncSession | Явно отделяет mutation boundary от Open/workspace; можно тестировать locks, чтение и spatial checks независимо от будущего HTTP/use case | Новый небольшой repository и типы контекста; вызывающий сервис обязан сохранять общий transaction scope |
| Расширить `WorkOrderRepository` | Меньше новых файлов, знакомая точка DI | В одном классе смешиваются Open, workspace projection и протокол mutation; сложнее видеть обязательный порядок вызовов |
| Перенести Save в DB function | Транзакционный протокол можно централизовать в БД | Пересекается с orchestration следующих дней, усложняет использование уже реализованного Decimal-ядра и сопровождение migrations |

10 октября пользователь принял отдельный `EditGeometryRepository` и первую часть дизайна: transaction принадлежит сервису; repository блокирует root, затем отдельно читает контекст, spatial checks предшествуют записи; mutation меняет только geometry/operation current feature без самостоятельного commit. Revision, registry и history orchestration добавляются в Дни 6–7 в ту же transaction. Это согласование первой части, а не принятие ещё не написанной полной спецификации.

## Часть 2: согласованный контракт контекста и ошибок

Уточнение после проверки плана 10 октября: пользователь указал, что geometry не является агрегатом. Каноническая DDD-модель определяет root как EditVersion. Имя нового repository в design/plan исправлено на `EditVersionRepository`, planned file — `edit_version_repository.py`. Geometry context и spatial helpers остаются внутренними деталями сценария изменения этого агрегата. Историческое имя в сравнении вариантов выше не является актуальным именем реализации.

Статус: принят пользователем 10 октября 2026 года.

### Данные контекста

Repository возвращает типизированное значение с данными, прочитанными после root lock:

- Идентификаторы WorkOrder/EditVersion, lifecycle и assignment для проверок доступа вызывающим сервисом.
- `draft_revision`, `default_state_id`, `base_network_revision` и persisted geometry policy.
- Target current: составной ключ, feature type, operation и точная geometry в EWKB и декодированном Decimal-представлении.
- Baseline той же feature из DefaultState, указанного в root: geometry с исходным storage представлением и данные для проверки принадлежности/согласованности baseline.
- AOI соответствующего WorkOrder для проверки в PostGIS; display GeoJSON не используется как источник spatial validation.
- Сведения о других изменённых features во всей версии, без фильтра workspace по AOI.

Контекст используется только внутри породившей его transaction. Его нельзя сохранять между запросами или повторно использовать после commit/rollback. Конкретный API должен сделать это ограничение явным; одной проверки `session.in_transaction()` недостаточно, чтобы доказать происхождение старого контекста.

### Различение исходов

| Ситуация | Результат будущего use case |
| --- | --- |
| WorkOrder/EditVersion/target current отсутствует или объект недоступен actor | `EDIT_VERSION_NOT_FOUND`; отсутствие и недоступность различаются внутри, но не раскрываются наружу |
| Существующий объект не поддерживается first-save: Point, line без внутренней вершины, created/deleted operation | `FEATURE_NOT_EDITABLE` |
| У существующего baseline-backed current потеряна baseline feature; DefaultState отсутствует/принадлежит другому WorkOrder; контекст противоречив | `WORK_ORDER_CONTEXT_INVALID` |
| Сохранённый current противоречит baseline/operation или нарушает обязательные spatial rules | `WORK_ORDER_CONTEXT_INVALID`; Save не используется как repair |
| Уже изменена другая feature | `MULTIPLE_FEATURE_CHANGE_NOT_ALLOWED` |
| Candidate нарушает endpoints/count/ограничение одной вершины | `GEOMETRY_STRUCTURE_CHANGED` по ядру Дня 4 |
| Candidate invalid/non-simple/collapsed, включая D5-Q1 | `GEOMETRY_INVALID` |
| Допустимый candidate не покрывается AOI целиком | `GEOMETRY_OUTSIDE_AOI` |
| Ошибка соединения, SQL/codec failure или нарушение внутреннего протокола repository | Infrastructure/internal failure; rollback общей попытки, без превращения в domain rejection |

Отсутствующая baseline feature при `operation=created` не объявляется повреждением автоматически: такая операция сама по себе вне existing-feature slice. Для baseline-backed `unchanged/updated` отсутствие baseline является повреждённым контекстом. Существующая Point feature также является неподдерживаемым объектом, а не повреждением только из-за своего типа.

Repository возвращает внутренние данные/типизированные исходы, не HTTP response. Access checks и преобразование в публичные ошибки принадлежат сервису; до проверки доступа внутренние причины не раскрываются. Существующий lifecycle conflict и будущие token/replay checks остаются ответственностью use case.

Ожидаемый spatial отказ определяется SELECT-проверками до UPDATE и не приводит к SQL constraint violation. Transaction остаётся работоспособной для будущей записи terminal rejection. Registry допускает отсутствие записи при несуществующей version/target feature согласно Дню 2. Успешный no-op не вызывает content UPDATE; ошибка infrastructure не сохраняется как успешный или доменно отклонённый результат.

## Часть 3: согласованные ограничения записи и приёмка

Статус: принято пользователем 10 октября 2026 года. Все части дизайна согласованы в обсуждении; письменная спецификация требует отдельной проверки.

### Запись проверенного результата

На mutation boundary поступает результат проверки, связанный с конкретными context, target feature и canonical candidate. Нельзя проверить один candidate, а записать другой. Записывается то же storage представление geometry, на котором выполнены spatial checks. Повторная канонизация или автоматическое исправление geometry на записи не выполняются.

Контекст привязан к породившей его session/transaction. Запись вне этой transaction, после её завершения либо с контекстом другой session считается ошибкой внутреннего протокола. После content mutation прежнее представление current нельзя использовать для следующего изменения без нового чтения. Точные имена внутренних типов и методов определяются письменной спецификацией.

UPDATE адресует ровно `(edit_version_id, feature_id)` и меняет только geometry/operation. Отсутствие ожидаемой строки при записи считается нарушением контекста/протокола, а не успешным сохранением. Operation выводится из сравнения с baseline; клиент не выбирает её произвольно. No-op проходит необходимые проверки, но не выполняет content UPDATE. Возврат к baseline восстанавливает исходное storage представление, включая нетронутые off-grid coordinates.

Ни baseline, ни AOI, ни associations, ни attributes, ни network_version не изменяются. Repository не делает commit/rollback. Изменение draft_revision и полный registry/event workflow остаются общему сервису Дней 6–7.

### Проверяемая готовность M1

Repository integration tests выполняются на реальном disposable PostGIS с отдельными connections там, где проверяется конкуренция. Test-only orchestration вызывает repository внутри transaction; она не становится production Save service или новым endpoint.

Приёмка включает матрицу ниже, targeted backend regression Дней 1–4 и полный isolated DB suite. Успех M1 фиксируется только по новым результатам после реализации. Существующий отчёт Дня 4 не заменяет этот прогон. Для пространственных случаев используются самостоятельные fixtures, включая line с большим числом vertices; production boundary не привязывается к `L-003` или индексу 1.

Особенно проверяются: отсутствие content UPDATE на no-op; отказ до записи с сохранением работоспособности transaction; rollback после успешного repository UPDATE при последующем исключении вызывающего кода; невозможность использовать контекст другой/завершённой transaction. Сравнение до/после охватывает весь baseline выбранного DefaultState и associations, а не только geometry target feature.

Тесты для candidate отдельно различают invalid и valid-but-non-simple, нулевой сегмент D5-Q1, касание/прохождение по AOI boundary, выход сегмента за AOI при находящихся внутри вершинах, holes и MultiPolygon. Эти сценарии проверяют полное покрытие линии, а не только её vertices.

## Матрица будущих доказательств

| Группа | Что должна доказать проверка |
| --- | --- |
| Конкуренция одной версии | Вторая transaction действительно ждёт root lock; после commit видит новый current, после rollback — прежний; ожидание подтверждается через pg_blocking_pids |
| Независимость версий | Lock одной EditVersion не сериализует Save другой версии |
| Согласованный контекст | Baseline выбран по root-ссылке, feature по составному ключу; missing/mismatched context не выдаётся за готовый контекст |
| Точный storage | Off-grid baseline и нетронутые координаты сохраняются; Revert восстанавливает baseline; no-op не вызывает content UPDATE |
| Spatial rejection | Invalid/non-simple, схлопнувшийся сегмент и выход за AOI отвергаются до записи; boundary разрешена; holes и MultiPolygon проверяются на всю линию |
| Единственная feature | Проверяется вся версия, включая строки вне workspace projection; другая изменённая feature обнаруживается |
| Mutation scope | Меняются только geometry/operation нужной current feature; baseline, соседние features, properties, network_version и associations неизменны |
| Transaction ownership | После repository UPDATE нет самостоятельного commit; failure injection у вызывающего кода откатывает изменение и освобождает locks |
| Совместимость | Open/reopen и существующие history triggers не получают обратного порядка locks; точный EWKB readback остаётся рабочим |
| M1 | Новые repository tests и регрессия фундамента выполняются в isolated test environment; полный Save не выдаётся за результат Дня 5 |

## Проверки и память

Выполнен статический анализ исходников и существующих тестов. Тесты и запросы к работающей БД в этом обсуждении не запускались. Отчёт Дня 4 является историческим свидетельством предыдущего прогона, а не новой проверкой M1.

Отдельная agent-memory запись не создаётся: контекст и причины обсуждения сохраняются этим артефактом. Изменений product code, migrations и tests нет; staging/commit/push запрещены правилами репозитория.
