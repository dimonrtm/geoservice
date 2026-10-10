# День 5: атомарный repository context

Дата: 10 октября 2026 года.

Статус: спецификация принята пользователем и реализована 10 октября 2026 года. M1 подтверждена; evidence и ограничения — в [отчёте реализации](2026-10-10-day-5-repository-context-implementation-report.md). [План](2026-10-10-day-5-repository-context-plan.md) выполнен.

## 1. Цель и основания

День 5 создаёт persistence boundary для будущего Save одной существующей line feature в EditVersion. Backend получает согласованный контекст под блокировкой версии, проверяет canonical geometry и записывает только current snapshot. Authoritative DefaultState не изменяется.

Основания:

- [Календарный план Sprint 2](2026-07-31-sprint-2-calendar-plan.md), День 5 и M1.
- [Технические требования](2026-07-31-sprint-2-technical-requirements.md), разделы 6–8 и 11.
- [Дизайн Дня 2](2026-10-01-day-2-first-save-schema-design.md): transaction, command registry, history и порядок locks.
- [Дизайн Дня 4](2026-10-08-day-4-geometry-design.md): Decimal, policy, structure guard, no-op, fingerprint и точное хранение.
- [Анализ и решения этого обсуждения](2026-10-09-day-5-repository-context-analysis.md).
- `Wiki/value_objects/aoi.md`, `Wiki/specifications/edit_version_basic_draft_validation.md`, `DDD_Wiki/invariants/edit_version_persisted_edit_invariants.md`.

Обозначение «День 5 — 7 августа» сохраняет место этапа в исходном календаре. Дата этой спецификации не переносит автоматически календарные даты спринта.

## 2. Границы результата

### Входит

- `EditVersionRepository` для агрегата EditVersion на существующей AsyncSession.
- Блокировка конкретной EditVersion и чтение контекста после получения lock.
- Типизированный контекст current/baseline/AOI/policy/revision.
- Проверки существования, согласованности target context и единственной изменяемой feature.
- Spatial validation в PostGIS и временный запрет нулевого сегмента D5-Q1.
- Запись только geometry/operation target current feature, включая no-op и восстановление baseline на уровне repository.
- Integration tests, регрессия предыдущего фундамента и доказательства M1.

### Следующие этапы

Полный Save use case, token/replay orchestration, резервирование и финализация CommandId, увеличение revision, запись history и durable rejection относятся к Дням 6–7. Публичный PUT, расширенный workspace response и UI относятся к последующим дням календаря.

Repository этого дня — внутренний компонент. Он не подключается как самостоятельный публичный Save, который мог бы committed geometry без обязательных revision/registry/history. Test-only orchestration не переносится в production как временный endpoint.

Новая migration не требуется выбранным дизайном. Существующие schema constraints и triggers сохраняются. Глобальная защита от произвольного SQL writer, repair повреждённых данных, topology/network validation и positional acceptance в задачу не входят.

## 3. Согласованные допущения

1. Конкурирующие Save одной EditVersion соблюдают этот протокол и сначала блокируют root.
2. AOI, baseline и assignment WorkOrder неизменны на время Save. Защита от конкурентного изменения этих данных отдельным writer не добавляется.
3. Конкуренция уже существующего Open/reopen учитывается: Save не вводит обратный порядок конфликтующих locks.
4. Geometry policy берётся из EditVersion; изменение global settings не меняет правила уже открытой версии.
5. Граница AOI включена: касание и прохождение вдоль неё допустимы при полном покрытии линии.
6. Совпадение соседних XY-координат после канонизации пока запрещено как схлопывание сегмента. Это временное правило D5-Q1, а не окончательно установленный доменный инвариант.

## 4. Компоненты и ответственность

Корень агрегата — `EditVersion`, как определено в `DDD_Wiki/aggregates/edit_version.md`. Geometry является значением внутри current feature рабочей версии, а не самостоятельным агрегатом. Поэтому repository называется `EditVersionRepository`; прежнее предложенное имя `EditGeometryRepository` заменено после замечания пользователя о границе агрегата.

Repository сохраняет состояние EditVersion в пределах её consistency boundary. Geometry-specific context, SQL и validation helpers — внутренние части этого сценария. Ограниченная запись одной feature не превращает её или geometry в отдельный агрегат: блокировка, revision и инвариант единственной изменённой feature относятся ко всей EditVersion. WorkOrder задаёт assignment/AOI и условия открытия версии; baseline остаётся внешним неизменяемым источником чтения, его подключение к context не передаёт владение им EditVersionRepository.

| Компонент | Ответственность |
| --- | --- |
| Будущий Save service | Владеть transaction; проверить actor/access/lifecycle; организовать replay/token, command, revision и event; сформировать HTTP response |
| `EditVersionRepository` | Persistence агрегата EditVersion: root lock, context и ограниченная mutation дочерней feature; использовать spatial helpers и сообщать внутренние исходы |
| Чистое ядро `domain_services/edit_geometry` | Canonicalization, structure/transition checks, operation/no-op и fingerprint; без SQL и global settings |
| `geometry_codec.py` | Точная граница EWKB ↔ Decimal geometry и проверяемое кодирование candidate |
| PostGIS | Проверки геометрии, нулевых сегментов и покрытия AOI на сохраняемом storage представлении |

Repository не импортирует HTTP response schemas, не вызывает commit/rollback и не открывает независимую session. Существующий WorkOrderRepository продолжает обслуживать Open/workspace.

## 5. Протокол транзакции и locks

Владелец вызывает `session.begin()` до получения контекста. Контракт рассчитан на READ COMMITTED; integration tests подтверждают фактический isolation level. Переход на REPEATABLE READ/SERIALIZABLE и retry serialization failures не вводятся как побочный эффект этого дня.

Последовательность:

1. Найти EditVersion по `edit_version_id` с проверкой `work_order_id` и получить `FOR UPDATE` только на root.
2. После успешного получения lock выполнить новый SELECT current, baseline и AOI. Связанные значения читаются одной проекцией, отсутствующие ссылки сохраняются как диагностируемые исходы.
3. Проверить доступ и применимые guards в предусмотренных для них слоях. Подготовить candidate по persisted policy.
4. Проверить spatial properties exact candidate, затем записать current при фактическом изменении.
5. В Днях 6–7 в тот же transaction scope включить command/revision/event orchestration. Только владелец завершает transaction.

Нельзя совмещать ожидание root lock и чтение зависимых незаблокированных строк в один сложный SELECT и рассчитывать, что после ожидания все они автоматически перечитаются. Новый SELECT после lock обеспечивает чтение committed результата предыдущего Save при READ COMMITTED. Основание: [PostgreSQL transaction isolation](https://www.postgresql.org/docs/16/transaction-iso.html).

Root lock удерживается до завершения общей transaction. После него Save не берёт конфликтующий lock на WorkOrder, поскольку Open/reopen уже использует порядок WorkOrder → EditVersion. AOI и baseline читаются без дополнительных writer locks в рамках согласованного допущения.

При интеграции команд сохраняется порядок конфликтующих locks `EditVersion → command → feature`, установленный event trigger. Чтение current до command не должно заранее блокировать feature FOR UPDATE. Блокировка строки вследствие UPDATE происходит на этапе mutation после command reservation в будущем use case.

Разные EditVersion не сериализуются одной общей repository-блокировкой. Lock timeout, deadlock или ошибка соединения не превращаются в успешный результат или domain rejection.

## 6. Контекст и внутренние интерфейсы

Логические операции repository:

| Операция | Контракт |
| --- | --- |
| `lock_version(work_order_id, edit_version_id)` | Возвращает locked root handle либо отсутствие; не делает content mutation |
| `read_context(locked_version, feature_id)` | Читает свежую проекцию; возвращает `EditGeometryContext` или типизированные сведения об отсутствии/повреждении |
| `prepare_candidate(context, request_geometry)` | Вызывает чистое ядро Дня 4 с baseline/policy контекста и связывает PreparedGeometry с этим чтением; без mutation |
| `validate_candidate(context, prepared_geometry)` | Проверяет контекст и результат чистого ядра, вызывает spatial checks; возвращает `ValidatedGeometryChange` либо ожидаемый отказ |
| `write_current(validated_change)` | Проверяет происхождение результата и пишет ровно проверенные geometry/operation; возвращает no-op или before/after сведения о mutation без commit |

Названия фиксируют ответственность; детализация Python signatures и разбиение SQL оформляются в плане реализации. PreparedGeometry создаётся чистым ядром Дня 4 с baseline и policy из этого контекста. Независимо сконструированный PreparedGeometry не считается подтверждённым результатом подготовки: внутренний handle связывает его с context. Подготовка доступна отдельно от spatial validation для будущего fingerprint/replay. Repository не доверяет произвольным переданным operation/no-op: они выводятся через проверки структуры и перехода. Перед обращением к существующему `validate_transition` обеспечивается корректная структура candidate, включая соответствие counts/types: функция предполагает корректный PreparedGeometry и использует strict zip.

`EditGeometryContext` содержит:

- Идентичность WorkOrder/EditVersion, lifecycle и assignment для сервисных guards.
- `draft_revision`, `default_state_id`, `base_network_revision`, GeometryPolicy из root.
- Current target: составной ключ, feature type, operation, network_version, исходные EWKB и декодированную geometry.
- Baseline target по `(root.default_state_id, feature_id)`, соответствующий DefaultState и сведения для проверки WorkOrder/base revision/type.
- AOI WorkOrder в исходном представлении БД для SQL validation; display GeoJSON не является источником проверки.
- Сведения о других изменённых features всей версии без AOI-фильтра workspace.
- Внутреннюю связь с session, активной transaction и конкретным чтением context.

AOI не декодируется существующим Point/LineString codec. Polygon/MultiPolygon сохраняется на SQL boundary. Данные root/current возвращаются свежей проекцией, а не потенциально устаревшим объектом SQLAlchemy identity map.

### Время жизни

Handle, context и validated change привязаны к конкретной session и transaction, а не только к UUID версии. После commit/rollback они непригодны, даже если та же session начала новую transaction. Нельзя передавать их другому экземпляру repository с другой session.

Выдаваемые наружу значения immutable; write принимает validated result, а не независимые geometry и operation. Candidate bytes и target identity связаны с проверкой. Один context допускает одну попытку применения результата; для следующей mutation требуется новое чтение под продолжающим действовать root lock.

Вложенные savepoint-переходы между получением handle и его использованием не поддерживаются этим контрактом: rollback savepoint может отменить приобретённый lock. Такой протокол должен отклоняться как внутреннее неправильное использование. Общий Save остаётся одной внешней transaction.

Эти ограничения защищают от случайного неправильного использования application code; они не являются защитой от произвольного Python/SQL кода с доступом к session.

## 7. Чтение и проверка исходного состояния

### Существование и принадлежность

- EditVersion принадлежит переданному WorkOrder; target current ищется по составному ключу, без ST_Intersects-фильтра.
- DefaultState выбирается по ссылке root, а не как произвольный active aggregate WorkOrder.
- DefaultState существует, принадлежит тому же WorkOrder, имеет согласованный base_network_revision.
- Для baseline-backed target `unchanged/updated` baseline feature существует; identity и feature type соответствуют current.
- AOI существует и принадлежит контексту через WorkOrder.aoi_id; geometry допускает Polygon/MultiPolygon, XY и SRID 4326, non-empty/valid.
- Current и baseline имеют поддерживаемые координаты и согласованную структуру. Existing line для этого slice имеет минимум три вершины.

Point, двухвершинная line и created/deleted target относятся к `FEATURE_NOT_EDITABLE`. Отсутствие baseline у created feature само по себе не считается повреждением existing-feature snapshot: такая feature уже исключена из slice.

### Current, baseline и operation

Current может совпадать с baseline либо отличаться одной внутренней вершиной. Endpoints, число vertices и тип сохраняются. `operation=unchanged` соответствует numeric equality с baseline; `operation=updated` — допустимому непустому diff. Противоречие считается повреждённым контекстом, а не поводом молча исправить operation.

Для редактируемой линии baseline/current должны удовлетворять применимым spatial rules: конечные XY, географический диапазон, valid/simple/non-empty, отсутствие нулевых сегментов и полное покрытие AOI. Повреждённый current не исправляется через обычный Save/Revert. Проверка before также необходима для совместимости с уже существующими constraints history.

Проверка другой изменённой feature охватывает все строки current версии. Маркером существующего persisted change служит `operation != unchanged`; consistency operation проверяется для target. Полный аудит произвольных скрытых изменений сторонним SQL writer во всех features не добавляется. Это соответствует границе конкуренции и протоколу штатных writers.

Если другая feature помечена изменённой, target не сохраняется с `MULTIPLE_FEATURE_CHANGE_NOT_ALLOWED`. Репозиторий не ограничивается видимыми на карте объектами и не игнорирует changed feature вне AOI.

## 8. Candidate, spatial checks и точная запись

Canonicalization использует существующий `prepare_geometry` и policy root. Проверка структуры и перехода использует ядро Дня 4: разрешено менять только одну внутреннюю вершину; смена изменённой вершины требует отдельного возврата к baseline.

Spatial checks выполняются над EWKB, которое затем пойдёт в UPDATE:

1. Поддерживаемый LineString, XY, SRID 4326, конечные координаты в допустимом географическом диапазоне.
2. `NOT ST_IsEmpty`, `ST_IsValid`, `ST_IsSimple`.
3. Отсутствие совпадения любой пары соседних XY-координат по временному D5-Q1. Проверка проходит по упорядоченным vertices в PostGIS; signed zero не создаёт ненулевой сегмент.
4. `ST_Covers(aoi, candidate)` — вся линия покрывается AOI, включая boundary.

AOI predicate вычисляется только для допустимых входных geometry; нельзя полагаться на порядок вычисления частей произвольного SQL AND для защиты от invalid input. Допустим последовательный SQL либо явно безопасное разветвление.

Покрытие не подменяется ST_Intersects, bbox или проверкой только vertices. Линия, пересекающая hole либо выходящая за вогнутую границу между внутренними vertices, отклоняется. MultiPolygon проверяется как полная AOI geometry. Семантика boundary описана в [ST_Covers](https://postgis.net/docs/manual-3.4/ST_Covers.html).

### Storage

Для изменённого candidate используется существующий codec с проверкой обратимости Decimal → binary64. Если результирующая geometry равна baseline и это content change, записывается исходное baseline storage представление. Для no-op current не переписывается, в том числе ради изменения представления signed zero.

Numeric equality задаёт no-op и operation по Дню 4; топологическое равенство не заменяет сравнение координат. EWKB используется для точного переноса и доказательства неизменности storage. Нетронутые baseline ordinates сохраняются без округления.

`write_current` выполняет UPDATE ровно одной строки и только двух полей: geometry, operation. Если ожидаемая строка не обновлена, операция не выдаётся за success. Никаких ST_MakeValid, ST_SnapToGrid, удаления vertices или скрытой нормализации на записи нет.

`draft_revision`, properties, network_version, feature identity/type, associations, AOI и DefaultState не изменяются этим методом. Возвращаются before/after geometry и признак content change для будущей orchestration.

No-op проходит guards, но не выполняет UPDATE. Content-changing возврат к baseline проверяется здесь как repository capability; command/event semantics Revert остаются Дню 7.

## 9. Исходы и граница ошибок

| Ситуация | Публичное отображение будущим сервисом |
| --- | --- |
| WorkOrder/EditVersion/target current отсутствует или недоступна | 404 `EDIT_VERSION_NOT_FOUND` |
| Неподдерживаемая existing feature/type/count/operation | 422 `FEATURE_NOT_EDITABLE` |
| Потерян baseline у baseline-backed target, неверные связи/revision, повреждены исходные geometry или operation | 422 `WORK_ORDER_CONTEXT_INVALID` |
| Изменена другая feature | 409 `MULTIPLE_FEATURE_CHANGE_NOT_ALLOWED` |
| Candidate нарушает endpoints/parts/vertex count/одну внутреннюю вершину | 422 `GEOMETRY_STRUCTURE_CHANGED` |
| Candidate empty/invalid/non-simple/collapsed, включая D5-Q1 | 422 `GEOMETRY_INVALID` |
| Spatial-valid candidate выходит за AOI | 422 `GEOMETRY_OUTSIDE_AOI` |
| SQL/connection failure, ошибка кодирования корректного candidate или нарушение внутреннего протокола | Infrastructure/internal failure; rollback общей попытки |

Распознанное повреждение geometry, прочитанной из storage, относится к context-invalid; ошибка адаптера при кодировании заведомо допустимого candidate — internal failure. Нельзя одним общим перехватом ValueError/DBAPIError превратить любой дефект в domain rejection.

Отсутствие и недоступность различаются внутри для registry semantics Дня 2, но не раскрываются наружу. Repository не формирует HTTP response и не решает, раскрывать ли actor диагностическую причину. Проверки доступа предшествуют раскрытию внутренних ошибок и replay результата.

Внутри geometry boundary сначала классифицируются существование/eligibility и целостность context, затем другая изменённая feature, structure, spatial validity, AOI. Приоритет access/lifecycle/token/replay принадлежит будущему use case; replay не должен повторно выполнять spatial validation старой успешной команды.

Ожидаемые отказы определяются до UPDATE, без намеренного нарушения DB constraint. Transaction остаётся пригодной для записи terminal rejection на следующем этапе. При отсутствующей version/target feature registry record не требуется согласно Дню 2. Инфраструктурная ошибка не фиксируется как terminal domain rejection.

## 10. Совместимость с Днями 6–7

В будущей общей transaction сохраняются возможности:

- Прочитать immutable baseline/policy для fingerprint без изменения current.
- Проверить существование и доступ перед раскрытием stored response.
- Обработать replay до проверки исходного token на актуальность и до повторного применения geometry guards.
- Зарезервировать command после root lock и до feature mutation.
- При content change записать current, увеличить revision, сохранить success и добавить event до commit.
- При domain rejection оставить snapshot/revision неизменными и сохранить отказ; при infrastructure failure откатить всю попытку.

Методы Дня 5 не делают implicit revision increment и не создают synthetic command/event. Integration-проверка совместимости со schema может пользоваться существующими test-only helpers для command/event, но не реализует полный production use case.

## 11. Проверки и критерии M1

Тесты выполняются на реальном disposable PostGIS через `infra/db-tests.cmd` или эквивалентный isolated Compose runner с `TEST_DATABASE_URL` и именем БД `_test`. Общая demo-БД исключена. Полный повторный DB-прогон начинается с fresh test environment по существующему runner.

| Группа | Обязательное доказательство |
| --- | --- |
| Root lock | Две отдельные sessions одной версии; ожидание подтверждено через pg_blocking_pids, а не только sleep |
| Commit/rollback конкурента | После ожидания читается новый current при commit либо прежний при rollback; нет stale projection/identity-map state |
| Разные версии | Вторая версия завершает repository operation, пока root первой остаётся locked |
| Open/reopen | Пересечение с существующим reopen не создаёт обратный lock order; last_opened_at не теряется от repository UPDATE |
| Контекст | Missing target/root, чужая связь, отсутствующий/чужой baseline, несовместимая revision/type, created/deleted и Point корректно различаются |
| Current | Неверные endpoints/vertex diff/operation и spatial-invalid current дают context-invalid без repair |
| Вся версия | Changed feature вне workspace projection тоже блокирует новую feature |
| Spatial checks | Invalid и valid-but-non-simple проверяются раздельно; D5-Q1 включает совпадение после canonicalization |
| AOI | Касание и участок на boundary разрешены; outside, hole и выход сегмента между внутренними vertices отвергаются; MultiPolygon поддерживается |
| Точность | Off-grid baseline, signed zero, нетронутые ordinates, canonical round-trip и возврат baseline без потери storage values |
| No-op | Отсутствует content UPDATE, а не только равны значения после UPDATE |
| Mutation scope | Изменены только geometry/operation target; весь baseline выбранного DefaultState, его associations, соседние current features, current associations и metadata неизменны |
| Rollback | Исключение вызывающего кода после UPDATE откатывает mutation; другая session не видит uncommitted результата; locks освобождаются |
| Ожидаемый отказ | Нет mutation; после отказа в той же transaction успешно выполняется следующий допустимый SQL, подтверждая отсутствие aborted transaction |
| Протокол | Чужая/завершённая transaction, новая transaction той же session, повторно использованный context и подмена candidate не допускают запись |
| Registry/history compatibility | Порядок root → command → feature и constraints существующей history совместимы с новой boundary |

Примеры spatial-предикатов, недостижимые после более раннего structure guard, проверяются на уровне spatial helper отдельно. Это не основание менять приоритет ошибок полного пути.

Fixtures не ограничиваются `L-003` и индексом 1; проверяется линия с большим числом vertices. Конкурентные tests ограничены timeout и корректно закрывают/cancel ожидающие tasks и transactions.

M1 требует успешных новых repository tests, релевантных backend unit/regression tests Дней 1–4 и полного isolated DB suite. Результаты предыдущих отчётов не заменяют новый прогон. Новые результаты оформляются после реализации; до этого статуса M1 «пройдено» нет.

## 12. Затрагиваемые файлы

Пути относительно корня репозитория. Новые имена ниже обозначают планируемые модули.

| Область | Файлы |
| --- | --- |
| Repository | Новый `apps/backend/utility_service/infrastructure/postgresql/repositories/edit_version_repository.py` |
| Контекст и результаты | Новый `apps/backend/utility_service/infrastructure/postgresql/repository_rows/edit_geometry.py` либо соседний модуль внутренних contracts |
| SQL | Новые специализированные проекции/проверки в `apps/backend/utility_service/infrastructure/postgresql/sql/`; workspace projection не подменяет Save context |
| Числовое ядро и codec | Переиспользуются `domain_services/edit_geometry/` и `infrastructure/postgresql/geometry_codec.py`; допускаются необходимые локальные helpers без изменения согласованной семантики |
| Integration | Новые tests context/spatial/mutation/concurrency в `apps/backend/tests/integration_tests/` |
| Unit tests | Контракты repository/protocol и точечная регрессия существующих geometry helpers |
| Документация | Analysis, design, будущий plan/report и README в `docs/sprint_2/` |

Перестройка Open, generic feature CRUD, frontend, существующих HTTP schemas и глобальной session architecture не требуется.

## 13. Временное правило D5-Q1

**Принято временно; доменное уточнение остаётся открытым.**

Совпадение соседних XY-координат после канонизации считается collapsed segment и отклоняет Save с `GEOMETRY_INVALID`, даже если общая длина линии ненулевая и она valid/simple по PostGIS. Пример: `A → B → C` превращается в `A → A → C`.

Нужно уточнить, является ли запрет любого нулевого сегмента постоянным инвариантом либо существуют разрешённые случаи соседних vertices с одинаковыми coordinates. Ответственный и срок не назначены. До явного пересмотра реализация и тесты следуют временному запрету; уточнение не блокирует День 5.

Правило нельзя незаметно представить как окончательное при подготовке plan/report или последующей документации. Будущее изменение требует отдельного решения с пересмотром validation и regression cases.

## 14. Самопроверка и следующий этап

Спецификация проверена на согласованность с тремя принятыми частями дизайна, контрактами Дней 2–4, границами transaction и матрицей проверок. Проверены локальные Markdown-ссылки, отсутствие placeholders, конфликтных маркеров и trailing whitespace; `git diff --check` также выполнен для tracked изменений. D5-Q1 намеренно остаётся открытым доменным уточнением с однозначным временным поведением.

Этот документ не является отчётом реализации или прохождения тестов. Пользователь принял письменную спецификацию; следующий артефакт — подробный план реализации в `docs/sprint_2/`. Product code пока не меняется; staging/commit/push выполняет только пользователь.

Отдельная agent-memory запись не требуется: причины, ограничения и решения сохранены в analysis/design. Repository-change ingest при создании спецификации не запускается.
