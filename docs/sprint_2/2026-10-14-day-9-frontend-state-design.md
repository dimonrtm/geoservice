# День 9 — frontend contracts и состояние редактирования

Дата: 2026-10-14. Календарный день: вторник, 11 августа 2026 года.
Статус: цельная спецификация принята пользователем 2026-10-14. [План реализации](2026-10-14-day-9-frontend-state-plan.md) подготовлен для просмотра и выбора способа исполнения. Реализация не начата.

## 1. Цель и границы

Добавить frontend-основание для локальной правки геометрии одной существующей линии, Save, повторов неизменной команды и восстановления после refresh. Результат проверяется через API client и Pinia store без обязательного готового инструмента редактирования карты.

Источник требований — [ТЗ Sprint 2](2026-07-31-sprint-2-technical-requirements.md), [календарный план](2026-07-31-sprint-2-calendar-plan.md), [API Дня 8](2026-10-12-day-8-api-readback-design.md), [правила восстановления](2026-10-12-save-recovery-rules-decision.md) и прямые ответы пользователя в [анализе Дня 9](2026-10-14-day-9-frontend-state-analysis.md). Этот документ объединяет согласованные разделы, а не повторяет исторические варианты.

Сохраняются инварианты `DDD_Wiki/aggregates/edit_version.md`, `DDD_Wiki/state_machines/editor_save_recovery.md` и `Wiki/policies/editor_recovery_policy.md`: одна изменённая feature, одна внутренняя вершина относительно baseline, неизменные endpoints, immutable baseline, opaque draft token, прежняя identity при retry. Новые организационные возможности из FU-2026-10-13-004 автоматически в scope не входят.

В День 9 входят contracts, PUT client, localDraft/current/pending/result, sessionStorage recovery, ограниченные автоматические повторы, Cancel локальной правки, защита от устаревших ответов и unit tests. Backend, migrations и публичный API не изменяются.

День 10 подключает выбор/drag на MapLibre; День 11 — Save/Cancel/Revert controls, подтверждения и доступность; День 12/S2-X01 — расширенное восстановление, управляемую навигацию с выбором, relogin resume и сквозной restart. Действие Revert в День 9 не добавляется, но contracts и общий PUT client поддерживают его будущий запрос. Offline editing, автоматическое слияние, очередь команд разных нарядов и координация вкладок не вводятся.

## 2. Архитектура

`useWorkOrdersStore` остаётся единственным владельцем workspace и состояния его редактирования. API client, кодек sessionStorage и управление расписанием retry выделяются во вспомогательные модули. Второй store с копией current не создаётся. Существующий `stores/edit.ts` относится к legacy Polygon/layer API и не переиспользуется как utility draft.

API client выполняет один HTTP-запрос на вызов. Повторы запускает store через вспомогательный модуль; общий Axios client не получает глобальный retry interceptor. Новые зависимости не нужны.

Основные области изменения относительно `apps/frontend/src/`:

- `contracts/work-orders.ts` и небольшой модуль contracts/guards редактирования;
- `api/workOrders.ts` и новый API client unit suite;
- `stores/workOrders.ts`, вспомогательные модули draft/recovery/storage/retry и их tests;
- `stores/auth.ts` и auth tests — остановка работы при потере identity и сохранность recovery;
- fixtures существующих workspace tests;
- точечная интеграция существующего restore flow; новые map tools и controls сюда не входят.

## 3. API contracts

### 3.1. Workspace

В `WorkspaceResponse.workOrder.editVersion` добавляются обязательные поля:

| Поле | Контракт |
| --- | --- |
| draftVersionToken | Непустая opaque string |
| hasPersistedChangeSet | boolean |
| basicValidation | Summary либо null |
| changeSet | Объект изменения либо null |

Summary: `geometryStatus="passed"`, `aoiStatus="passed"`, `positionalAccuracyStatus="POSITIONAL_ACCURACY_UNVERIFIED"`, `dirtyRelativeToBaseline="passed"`.

changeSet: `featureId`, `vertexIndex`, `baselineGeometry` как полная XY LineString, `operation="updated"`. При отсутствии persisted diff summary и changeSet равны null. OpenEditVersionResponse остаётся отдельным контрактом: draft-поля в него не добавляются по предположению.

Readback проверяется перед использованием как current: ожидаемые workOrder/editVersion IDs, новые поля, nullable-согласованность, пригодная форма изменённой линии и changeSet. Неполный/несогласованный ответ не разблокирует mutation. Другие типы геометрии workspace сохраняются; весь workspace не сужается до LineString.

### 3.2. Save

```http
PUT /api/v1/work-orders/{workOrderId}/edit-versions/{editVersionId}/features/{featureId}/geometry
```

Body содержит только `commandId`, `draftVersionToken`, `geometry`. commandId — UUID; geometry — полная LineString из конечных XY-пар. Token не преобразуется в число, не сортируется и не заменяется token из нового GET при retry. Actor передаётся только существующей авторизацией, не полем body.

Success: `commandId`, `commandState="succeeded"`, `draftVersionToken`, `operation="updated"|"unchanged"`, `hasPersistedChangeSet`, `updatedFeature={id,geometry}`, обязательный nullable `basicValidation`. Перед фиксацией success проверяются форма, согласованность summary и соответствие commandId/featureId отправленной команде. Неверный ответ не считается подтверждением.

Ошибки PUT/GET используют существующий `{code,message,correlationId}`. HTTP status сохраняется для классификации. CorrelationId относится к запросу, а не identity команды. Клиент не вводит полей current geometry/token внутрь ошибки.

Canonicalization, fingerprint, spatial validation и окончательная проверка eligibility принадлежат backend. Клиент проверяет форму и допустимость локального изменения; серверное округление не воспроизводит. Baseline берётся из backend, без seed coordinates и искусственного восстановления.

## 4. Данные и состояния

| Роль | Содержание и правило |
| --- | --- |
| workspace/current | Последний согласованный GET snapshot. Единственный источник текущих token, persisted changeSet и baseline для Revert |
| localDraft | featureId, исходные current geometry/token, candidate geometry, vertexIndex. Независимая копия; жест не меняет workspace |
| pendingCommand | actorId, target IDs и неизменное тело PUT. Не редактируется после подготовки к отправке |
| commandResult | Достоверный результат конкретной команды. Success может быть историческим replay и не равен текущему workspace |
| phase/errors | Различают editing, sending, retry wait, unknown, readback, rejection, stale и остановку из-за доступа/storage/protocol |

Dirty означает отличие candidate от current, а не от baseline. Сохранённый changeSet может существовать при отсутствии local dirty. Если changeSet уже непустой, локальная правка остаётся в рамках той же feature/vertex; данные changeSet дают эту привязку. Для чистой версии исходная линия берётся из current; seed baseline не подставляется.

Store предоставляет начало/обновление localDraft, Cancel, Save, ручной retry, readback и восстановление. Точные имена actions фиксируются в implementation plan; их поведение задаётся здесь.

- Cancel не выполняет HTTP и не меняет persisted changeSet. Он допустим для неотправленной правки и сохранённой для сравнения отклонённой попытки; неизвестную отправленную команду не удаляет.
- Пока Save выполняется либо исход неизвестен, изменение localDraft и новые Save/Revert запрещены.
- После подтверждённого success candidate перестаёт считаться несохранённым. До успешного GET mutation всё ещё заблокирована.
- После stale исходная попытка хранится отдельно для сравнения. Прочитанный current не становится новым основанием этой попытки автоматически. В базовом срезе Cancel и новое начало редактирования дают явный новый intent.

## 5. Recovery record

Versioned record в sessionStorage привязан к actor и target. Содержит формат записи, actorId, workOrderId, editVersionId, featureId, точное request body и состояние восстановления. JWT, пароль, access/refresh credentials не сохраняются. draftVersionToken — версия данных, не credential.

Логические состояния record:

- запрос подготовлен/исход неизвестен — допускается восстановление прежнего PUT;
- success подтверждён — сохранён проверенный результат, требуется только current GET;
- достоверный отказ получен — повтор PUT не запускается автоматически; сохраняются данные отказа и при необходимости незавершённого stale readback;
- восстановление остановлено из-за identity/access/protocol — автоматической отправки нет.

Обычная локальная несохранённая правка линии отдельно не персистится. Данные команды записываются **до первого PUT**, поэтому refresh до наступления timeout тоже оставляет identity для восстановления. Даже если страница закрылась между записью и отправкой, повтор допустим: он исполняет то же уже подготовленное намерение с прежним ID.

Запись до отправки обязательна. Ошибка storage оставляет candidate в памяти и исключает PUT. При чтении проверяются формат, target, actor и payload; повреждённая/неподдерживаемая запись не удаляется молча с переходом к новому Save. Восстановление останавливается с явной причиной; разбор потери identity относится к расширенному recovery.

После результата record обновляется до очистки. Если обновление/удаление не удалось, результат в памяти остаётся известным, но новая mutation блокируется, чтобы не затереть прежнюю запись. Можно повторить storage cleanup/readback без нового PUT. После refresh старая запись unknown может привести к безопасному replay, если подтверждение не удалось сохранить; новый commandId автоматически не создаётся.

После success + GET и успешной очистки запись больше не нужна. При достоверном отказе без незавершённого readback cleanup освобождает место для явно исправленного intent; при неудаче cleanup действует та же блокировка. После удаления записи обычная отклонённая локальная попытка не получает дополнительной гарантии сохранности при refresh.

## 6. Последовательность Save и canonical response

1. Проверить доступность текущего workspace, local dirty, отсутствие блокирующего recovery и допустимую форму candidate.
2. Создать новый UUID commandId, независимую копию тела и записать recovery record.
3. Выполнить один PUT. До его исхода локальная правка заморожена.
4. При success остановить серию, сохранить commandResult и фазу подтверждённого результата в storage.
5. Получить свежий workspace GET и проверить ответ. Новый snapshot заменяет current согласованно целиком: geometry, token, changeSet, validation не смешиваются из разных ответов.
6. После readback и cleanup снять local candidate и разрешить редактирование.

Canonical merge означает приоритет серверных данных над локальным предположением, а не безусловную запись `updatedFeature` в карту. Canonical geometry PUT сохраняется в commandResult. Актуальная карта и baseline происходят из GET, который может отражать более позднюю команду другой сессии. Исторические geometry/token replay не накладываются поверх current.

При ошибке GET результат Save остаётся подтверждённым. State сообщает «сохранение подтверждено, актуальные данные не загружены» и позволяет повторить GET. Предыдущий snapshot можно показывать только как последнее известное состояние с признаком неактуальности. PUT retry из-за ошибки GET не запускается. После refresh record подтверждённого success тоже приводит только к GET.

Успешный no-op обрабатывается тем же путём; изменение token не используется как доказательство успеха или отсутствия успеха. Positional accuracy/topology не объявляются проверенными.

## 7. Retry

| Точка входа | Максимум PUT | Паузы перед запросами |
| --- | --- | --- |
| Неизвестный исход первоначального Save | 5 дополнительных повторов, исходный PUT не входит | 0, 2, 5, 10, 20 секунд |
| Refresh с unknown record и сохранившимся доступом | 5 запросов восстановления | 0, 2, 5, 10, 20 секунд |
| Ручное «Повторить» после остановки серии | 1 запрос | Без автоматического продолжения серии |

Пауза отсчитывается после неудачного завершения предыдущего запроса. Время ожидания ответа добавляется; существующий HTTP timeout остаётся 30 секунд. Одновременно в текущем store выполняется один PUT данной команды. HTTP timeout не гарантирует остановки предыдущей backend transaction; возможное пересечение на сервере защищено существующей идемпотентностью.

Автоматическая серия применяется к network failure, timeout и HTTP 5xx. 5xx не считается доказанным durable rejection. Success либо достоверный domain rejection останавливают серию. После исчерпания pending остаётся; нового intent нет. Следующий refresh запускает новую ограниченную серию, общий lifetime retry budget не вводится.

Неожиданный формат ответа, неизвестный 4xx и внутренние ошибки клиента сохраняют неопределённость, но останавливают автоматику. Cancel transport не равен отмене сохранения. Ошибка/отмена из-за смены actor или инвалидированного контекста не запускает повтор.

## 8. Ошибки и прекращение восстановления

| Ситуация | Поведение |
| --- | --- |
| Подтверждённый success | Фиксация receipt, затем current GET |
| Обычный документированный domain rejection | Остановка повторов, сохранение причины и candidate; исправление требует нового intent |
| DRAFT_VERSION_STALE | Сохранение попытки для сравнения, отдельный GET, без автоматического reapply/new Save |
| COMMAND_ID_REUSED | Остановка и удержание контекста; не создавать новый ID автоматически |
| AUTH_REQUIRED / USER_INACTIVE / ROLE_NOT_ALLOWED / EDIT_VERSION_NOT_FOUND / SAVE_CONTEXT_CLOSED | Остановка из-за доступа/контекста; нельзя сделать вывод об исходе предшествующей потерянной попытки |
| REQUEST_VALIDATION_ERROR | Ошибка формы текущего HTTP-запроса, не доказательство durable registry rejection; автоматические повторы прекращаются |
| Неизвестный/невалидный ответ | Protocol error, unknown сохраняется, автоматическая серия остановлена |
| Workspace GET failure после success | Success сохраняется; повторяется чтение |

Если REQUEST_VALIDATION_ERROR пришёл на первоначальный запрос без предшествующего неизвестного исхода, исправление request возможно как явное новое намерение. Если такой ответ пришёл при восстановлении уже неизвестного исхода, контекст удерживается для разбора: parser error сам по себе не доказывает судьбу прежнего запроса. Аналогично access/lifecycle guards могут не допустить чтение старого результата; не следует очищать unknown только по HTTP 4xx.

Классификация использует документированные status/code, а не текст message или один класс HTTP. ErrorPresentation и state reasons не заменяют identity команды.

## 9. Refresh, auth и гонки

Обычный refresh использует существующий flow: восстановление auth, assigned list и workspace. При том же actor, доступном target и unknown record запускается серия PUT. Исходный token и geometry record не меняются из-за нового GET. При confirmed result выполняется GET без PUT.

Потеря авторизации, смена пользователя и reset останавливают таймеры и инвалидируют callbacks. Visible workspace/localDraft очищаются по текущим требованиям изоляции, recovery record прежнего actor не уничтожается и не показывается другому actor. Известная потеря доступа помечает восстановление как требующее явного продолжения: обычный refresh не должен превратить этот случай в автоматический relogin resume. Если такую отметку сохранить нельзя, автоматический recovery нельзя считать безопасно подготовленным; это storage/access block, а не разрешение очистить pending.

Автоматическое возобновление после обнаруженной потери доступа в День 9 не реализуется. Полный UI явного продолжения остаётся Дню 12/S2-X01. При initial session restore failure, отсутствии target в assigned list или неуспешном workspace GET автоматический PUT не запускается.

Каждый async result/timer привязан к actor, workOrderId, editVersionId, commandId и поколению операции. Проверка выполняется перед отправкой и перед применением ответа. Более ранний GET, начавшийся до Save, не должен перезаписать readback после Save; sequence guards должны покрыть и этот порядок. Устаревший callback не очищает recovery record новой операции.

Поддерживаемый механизм восстановления — в пределах sessionStorage текущей вкладки. Перенос между устройствами, сохранность после уничтожения storage и синхронизация независимых вкладок не обещаются. Backend idempotency/token guards остаются обязательными при любой конкуренции; клиентской межвкладочной блокировки нет.

## 10. Управляемая навигация

До появления диалогов последующих дней store блокирует переключение/повторное открытие workspace, которое потеряло бы localDraft или незавершённый Save/readback. Возвращает причину блокировки, не имитируя успешный переход. Для неотправленной попытки явный Cancel снимает ограничение. Повторный выбор того же workspace, не очищающий данные, допустим.

Загрузка списка/restore/clear actions не должны обходить эту защиту и молча стирать pending. При фактической утрате назначения или доступа приватное представление скрывается, но identity удерживается, автоматика останавливается. Это forced access transition, а не успешная пользовательская отмена.

Независимая работа с сохранённым контекстом нескольких нарядов, выбор save/discard/stay при выходе и relogin resume реализуются отдельно. Базовый срез не объявляет соответствие всей S2-X01. Аварийное закрытие не гарантирует восстановления обычной неотправленной геометрической правки.

## 11. Матрица приёмки

| ID | Проверка | Ожидаемый результат |
| --- | --- | --- |
| D9-01 | PUT client, URL/body, opaque token | Один HTTP call; нет extras, token arithmetic и скрытых retries |
| D9-02 | Success/GET guards, nullable fields, mismatched IDs | Только пригодные ответы изменяют состояние; protocol failure не объявляется success |
| D9-03 | Local gesture, dirty, Cancel | Current не мутирует; Cancel не вызывает backend; dirty не равен persisted diff |
| D9-04 | Storage write failure до Save | Ноль PUT, candidate сохранён в памяти |
| D9-05 | Refresh до timeout/между записью и отправкой | Восстанавливается та же команда с исходным payload |
| D9-06 | Автоматическая серия после Save и после refresh | Fake timers доказывают точные лимиты, паузы и отсутствие перекрытия клиентских вызовов |
| D9-07 | Исчерпание и ручной retry | Pending остаётся, ручной retry одиночный, новый ID не появляется |
| D9-08 | Success/no-op → readback | Серверный snapshot заменяет current согласованно, canonical geometry не берётся из candidate |
| D9-09 | Успех PUT, ошибка GET, refresh | Сохранён known success; последующие вызовы — GET, не PUT |
| D9-10 | Старый replay A после более нового изменения B | Receipt A исторический; current из GET остаётся B, token не сравнивается численно |
| D9-11 | Rejection/stale/reused ID/access/format error | Правильная остановка; candidate при stale удержан; нет автоматического reapply/new intent |
| D9-12 | 5xx, network, timeout, malformed response, cancellation | Соответствие retry policy; отмена transport не объявляется rollback |
| D9-13 | Corrupt record, другой actor, storage cleanup failure | Нет автоматического нового Save, утечки pending или его перезаписи |
| D9-14 | Поздние PUT/GET/таймеры после reset и до/после readback | Не меняют иной target/actor/new generation; старое чтение не откатывает snapshot |
| D9-15 | Навигация, assigned refresh и auth reset | Нет скрытой потери pending; управляемый переход с правкой блокируется; private state очищается при access loss |
| D9-16 | Регрессия list/open/restore/auth | Существующие сценарии сохранены, fixtures отражают обязательные workspace поля |

Targeted Vitest покрывает API/store/helpers/auth; fake timers и deferred promises проверяют повторы и гонки без реальных ожиданий. После targeted checks выполняются полный frontend test suite, typecheck, lint и build штатными scripts `apps/frontend/package.json`. Контрактные fixtures сверяются с backend schema Дня 8; генератор contracts и новая библиотека runtime validation не требуются.

Реальный browser refresh/backend restart и готовый пользовательский Revert проверяются на последующих этапах. Unit test восстановления store не называется доказательством реального перезапуска браузера или сервера.

## 12. Статус и следующий этап

Спецификация описывает согласованный дизайн и уточняет технические следствия разделения operation result/current. Реализация завершена 15 октября 2026 года: [отчёт и проверки](2026-10-15-day-9-frontend-state-implementation-report.md). Изменения оставлены unstaged, без git add/commit/push.

Пользователь принял цельный документ и разрешил реализацию плана. Следующий этап — подключение выбора/drag на карте в День 10. Новая agent memory не нужна: решения сохранены в спецификации, анализе и отчёте, дублировать их не следует.
