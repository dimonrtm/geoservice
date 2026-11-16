# Углублённый аудит backend и frontend

Дата: 2026-11-14. Дополняет и уточняет [основной отчёт](architecture-review.md). Приложение, его конфигурация и тесты не изменялись; диагностические скрипты и результаты сохранены только в этой папке.

## Что добавлено к первому проходу

1. Построен граф статических импортов TypeScript/Vue с отделением явно type-only импортов.
2. Разобраны Python AST для всего production-пакета utility_service, включая относительные импорты.
3. Прослежены Save/replay/rejection, открытие версии, foreground/recovery readback, auth/HTTP, навигация и legacy polygon mutation.
4. Запущен весь frontend Vitest и typecheck.
5. На реальном legacy store и Pinia воспроизведены поздние Save/Delete, меняющие новую сессию редактирования.
6. Уточнена достижимость проблем: legacy UI не подключён из App; WorkOrderService.start_work_order не вызывается production-кодом по выполненному поиску.

Оценки ниже разделены: **дефект воспроизведён**, **архитектурное нарушение подтверждено**, **риск подтверждён кодом, воздействие не воспроизведено**. Проходящие тесты не снимают архитектурное замечание и не доказывают отсутствия непокрытого поведения.

## 1. Измеренный граф зависимостей

### Frontend

Проанализированы 88 production `.ts`/`.vue` файлов. Найдено 282 статических ребра, из них 218 не помечены явно как type-only. Одна сильно связанная компонента содержит 17 файлов:

- `api/auth`, `api/http`, `api/workOrders`, `api/editVersions`, `api/editVersionMap`, `api/editVersionChangeSet`, `api/featureBaseline`;
- `auth/browserSessionMonitor`;
- `composables/readEditVersionSnapshot`, `composables/useEditVersionEditor`;
- `stores/auth`, `stores/workOrders`, `stores/editorSession`, `stores/editorNavigation`, `stores/editVersionDraft`, `stores/editVersionCommands`, `stores/workspaceRecovery`.

Это означает взаимную достижимость по импортам, а не взаимный вызов каждой пары во время выполнения. Примеры коротких циклов:

```text
stores/auth → api/auth → api/http → stores/auth
stores/editorNavigation → stores/editVersionCommands → stores/editorNavigation
stores/editVersionDraft → stores/editVersionCommands → stores/editVersionDraft
stores/editorSession → stores/editVersionCommands → stores/editorSession
```

Общий HTTP-клиент соединяет функционально разные части в одну компоненту. Поэтому перенос stores по модульным папкам без изменения контрактов сохранит ту же связанность. Разрыв только одного цикла может не уменьшить всю компоненту: проверять нужно оставшиеся пути, а не число экспортов.

Метод: TypeScript compiler AST; imports/exports; для Vue — script blocks. Динамические импорты, вызовы и bundle после tree shaking не анализировались. Неявные импорты, используемые лишь как типы, могут быть удалены компилятором; краткие циклы выше проверены вручную и используют значения. Четыре unresolved-записи — CSS, исключённый из графа исходных модулей, а не отсутствующие файлы. Данные: [import-graph.json](import-graph.json).

### Backend

Разобраны 185 production Python-файлов `utility_service`, включая migrations и исключая tests. Синтаксических ошибок не найдено. В 14 модулях `use_cases/services` (без `__init__`) обнаружены прямые зависимости:

| Зависимость | Модулей | Значение |
| --- | ---: | --- |
| infrastructure | 12 | Долг B2 системный, но не требует одномоментной миграции |
| SQLAlchemy | 9 | Application управляет persistence-деталями напрямую |
| FastAPI/Starlette | 4 | HTTP/transport зависимость существует за пределами web API |

Проверенные прямые границы `domain_services → outer/frameworks`, `web_api → infrastructure`, `use_cases → web_api`, `infrastructure → web_api` не нарушены. Обработка AST учитывает относительные импорты, импорт имён из родительского пакета и TYPE_CHECKING. Динамические импорты и транзитивные пути не проверяются. Это отдельная диагностика, не запуск штатного pytest. Данные: [backend-imports.json](backend-imports.json).

**Вывод:** текущий код выполняет ранее установленные ограниченные guards. Новые требования AGENTS шире guards. Запрещать сразу все 12 infrastructure-импортов в CI без поэтапного изменения контрактов нецелесообразно.

## 2. Владельцы состояния и места нарушения границ

| Состояние | Фактический владелец | Потребители / особенности |
| --- | --- | --- |
| token, actor, sessionId, sessionEpoch | auth store | HTTP, monitor, editor; auth также координирует workspace cleanup |
| список и выбранный наряд | workOrders | editorSession/navigation; это уже небольшой store |
| открытая версия, read generation, open intent | editorSession | recovery callbacks и editor; snapshot вычисляется из read stores |
| map snapshot / changes / baseline | отдельные read stores + useEditVersionEditor | согласование по token; отдельные loading/error состояния |
| обычный локальный draft | editVersionDraft | commands и session изменяют его напрямую — F1 |
| навигационное подтверждение | editorNavigation | commands меняет navigation/commandId напрямую — F1 |
| sent command, outcome, durable recovery | workspaceRecovery | commands предоставляет RecoveryHost; record-проекция не второй владелец |
| comparison preview, результат команды | editVersionCommands | session сбрасывает внутренние поля напрямую — дополнительное подтверждение F1 |
| источники/слои карты | map adapters | в основном workspace являются отображением; не обнаружено основания объявлять их владельцем draft |

`editorSession.ts:307–340` сбрасывает несколько полей commands, draft и read stores. Это не просто «много импортов»: знание внутреннего состава соседа находится вне его владельца. Новое поле commands легко забыть в одном из внешних reset-путей. Предлагаемый контракт должен выражать завершение контекста, а не добавлять по setter на каждое поле.

При этом `applyWorkspaceRead` проверяет sessionEpoch, actor/context key и generation; `loadVersion` проверяет выбор и request sequence. Эти защиты нужно сохранить. Нельзя заменить их одним глобальным `isLoading`.

## 3. Прослеженные сценарии и ограничения рефакторинга

### Backend Save/replay

```text
web_api/work_orders.save_feature_geometry
 → raw JSON parser
 → EditVersionService.save_geometry: внешняя transaction
 → actor/access gate → lock_version → baseline/context → command identity
 → существующая квитанция/replay либо подготовка и проверка candidate
 → сохранение geometry/terminal command outcome
 → выход из transaction / commit
 → возврат результата или прикладная ошибка
 → JSONResponse / exception handler
```

`edit_version_service.py:174` проверяет текущий access gate до выдачи сохранённого результата. Строки 380–404 возвращают сохранённые status/payload либо rejection. Отказ поднимается после завершения транзакции (`save_geometry`), а не внутри неё. Это предотвращает rollback самой квитанции отказа.

Подтверждённые тестовые контракты по прочитанным тестам: `test_save_geometry_rejections.py` проверяет commit-before-error и отказ commit; `test_save_geometry_replay.py` — A-after-B и current access-before-replay; `test_save_geometry_service.py` — stale/commit failure. В этом окружении backend-тесты не запускались.

**Уточнение B1/B2:** `EditGeometryScope` не является произвольным усложнением. Он связывает handle с session/transaction, запрещает неподходящую nested transaction, отслеживает generation и потребление результата. `edit_version_repository.py:446–549` использует эти проверки при prepare/validate/apply. Перенос «всей валидации в domain» с удалением handles ослабит существующую гарантию. Чистая функция может вычислить решение, а repository должен продолжать проверять действительность выданного handle перед записью.

В `validate_candidate:490–505` repository также выбирает `MULTIPLE_FEATURE_CHANGE_NOT_ALLOWED` и вызывает чистый `validate_transition`. Это точнее первоначального B1: чистое правило частично уже выделено; нужно отделить оставшиеся решения, а не переписать алгоритм с нуля.

`version_change_projection.py:43–96` повторно проверяет допустимый набор изменений при чтении: один изменённый объект, одна внутренняя вершина. Это не повод убрать read validation: сохранённые повреждённые данные должны отклоняться. Можно переиспользовать чистые геометрические predicates, сохранив разные ошибки read corruption и rejected command.

### Открытие версии

HTTP вызывает `EditVersionService.open_for_work_order`, а не `WorkOrderService.start_work_order`. Путь открытия получает work order через `get_by_id_for_update`, создаёт/переоткрывает версию и восстанавливается после конкретного unique violation. B2 остаётся подтверждён, но гипотеза «start_work_order без блокировки ломает текущий open endpoint» не подтверждается.

### Foreground и recovery чтение

Оба пути собирают снимок из map/change-set/baseline и проверяют согласование токенов. Они выполняются через разные оркестраторы: `useEditVersionEditor.synchronize` и `readEditVersionSnapshot`. Второй умеет checkpoint/retry и переживает смену отображаемой версии, первый обновляет UI поэтапно. Поэтому механически объединять их в один универсальный reader нельзя; общая bounded reconciliation policy возможна, но lifecycle остаётся различным.

### Auth и cleanup

`api/http` получает auth store, проверяет readiness перед защищённым запросом, добавляет token и передаёт ошибки в auth. Auth вызывает собственный HTTP API и знает editor stores. Цикл реальный, но refresh recursion не заявляется: auth endpoints исключены из readiness-проверки. При развязке сохранить `authErrorHandling: "caller"`, epoch и локальную обработку старого 401.

### Legacy feature API

`layers_router` содержит `Depends(require_legacy_gis_editor)`. Guard проверяет feature flag и роль; по умолчанию `legacy_gis_api_enabled=False`. FeatureService сам actor не принимает. Это архитектурное замечание B5 о повторном использовании use case, а не незащищённый endpoint.

## 4. Новые замечания

### F5 — воспроизведённая гонка поздних ответов legacy edit store

**Правило:** frontend §3–§4 — контекст состояния и защита от поздних результатов.

**Код:** `apps/frontend/src/stores/edit.ts:118–168` (`saveEditing`), `:171–191` (`deleteEditing`), `:199–247` (обработка отказа/refresh).

Save захватывает session A, ждёт PATCH и затем пишет результат в текущее `this.edit` без сравнения identity/generation. Delete после ожидания безусловно ставит `idle`. Error path также обращается к текущей session, хотя ошибка относится к предыдущему запросу; последнее установлено статически, отдельно не воспроизводилось.

**Воспроизведено:**

1. Начать A, сделать dirty, запустить Save с отложенным ответом.
2. Отменить A и начать B.
3. Завершить PATCH A. Ожидалось B; фактически store содержит A, version 2.
4. В отдельном сценарии начать Delete A, открыть B, завершить Delete A. Ожидалось B; фактически `idle`.

Скрипт загружает реальный `edit.ts`, реальные contract-функции и Pinia, подменяет только HTTP. Данные синтетические. [Скрипт](reproduce-legacy-edit-race.cjs), [результат](legacy-edit-race.json). Это доказательство store-level дефекта, не браузерный E2E и не доказательство потери серверных данных.

**Достижимость:** `MapPageView.vue` включает `MapView mode="editing"`, но не импортируется из текущего production App-графа. App показывает EditorWorkOrdersView с empty/workspace режимами. Поэтому не переносить вывод на основной EditVersion editor. Исправить до возвращения legacy editing в UI либо при отдельной задаче legacy maintenance.

**Минимальное исправление:** generation/identity операции и контекста, проверяемые после каждого await и перед error handling; отдельный учёт изменения draft во время запроса. Одного сравнения featureId недостаточно, если пользователь заново открыл тот же объект. На результат старой операции не должен реагировать новый edit session. Не нужна новая библиотека состояний.

### F6 — риск бесконечного пересогласования revision без бюджета

**Квалификация:** отсутствие ограничения подтверждено кодом; длительное пользовательское зависание в реальной системе не воспроизводилось.

**Код:** `readEditVersionSnapshot.ts:93–113` содержит `for (;;)` и немедленный `continue` при несовпавших токенах; `useEditVersionEditor.ts:126–147` делает аналогичный цикл, пока generation текущий. Ограниченный retry отдельных сетевых ошибок не ограничивает число успешных ответов с несовпавшими revision.

**Следствие:** при постоянном изменении версии между двумя чтениями или устойчиво рассогласованном источнике запросы продолжаются до внешней отмены; явного результата «не удалось получить согласованный снимок» нет. Это прежде всего риск живучести и нагрузки, не установленная потеря данных. Cancellation/reset уже существуют и не должны удаляться.

**Минимальное исправление:** общий принцип ограниченного числа/времени пересогласований, пауза при повторном mismatch, явное retryable состояние UI/recovery. Конкретный бюджет определить отдельно. Не добавлять polling и не принимать несовпавшие снимки. Проверки: единичный drift сходится; постоянный drift заканчивается предсказуемо; abort прекращает цикл; recovery не повторяет PUT из-за read mismatch.

### F7 — непроверенные внешние ответы List/Open

**Квалификация:** нарушение runtime-границы подтверждено; некорректный ответ действующего backend не наблюдался.

**Код:** `api/workOrders.ts:4–7` возвращает `response.data` из `http.get<AssignedWorkOrdersResponse>`; `api/editVersions.ts:12–15` аналогично использует `post<OpenEditVersionResponse>`. Generic Axios не валидирует JSON. `stores/workOrders` принимает список; `editorSession.loadVersion` сразу использует `.editVersion.id`.

Для сравнения, `api/editVersionMap.ts` получает `unknown` и вызывает `parseEditVersionMap`, а Save использует `parseGeometrySaveResult` с target/commandId. Это существующий подход проекта, новый validation framework не требуется.

**Следствие:** ответ неверной формы проходит API-границу; TypeError или неверные идентификаторы появляются позднее в orchestration/UI и могут получить не соответствующее причине сообщение. Предлагается парсер реально используемых полей и допустимых статусов, проверка workOrderId в Open; не зеркалировать все backend DTO и не добавлять избыточную проверку каждого необязательного metadata-поля.

**Проверки:** отсутствующий editVersion/id, неверный workOrderId, неверный статус списка, null/не-array список; store не принимает некорректные данные, ошибка обозначена как нарушение протокола.

### B5 — авторизация legacy use cases закреплена только в HTTP

**Квалификация:** нарушение правила application-boundary подтверждено; HTTP обход доступа не установлен.

**Код:** `web_api/api/layers.py:28–32` — router guard; `web_api/api/auth.py:121–130` — flag и роль. `use_cases/services/feature_service.py` create/update/delete не принимают actor и не проверяют разрешение действия. Сервис можно вызвать внутренним потребителем без этого контекста.

**Правило:** backend §4 — право на прикладную операцию не защищается только одним endpoint. Guard на HTTP нужен, но не является контрактом самого use case.

**Минимальное исправление:** при развитии legacy-сценария определить явный прикладной actor/permission contract и проводить его проверку для mutation. Не протаскивать FastAPI Depends/Request в сервис и не изобретать RBAC engine. Feature flag может оставаться эксплуатационным ограничением адаптера; его не нужно автоматически превращать в доменный инвариант.

**Проверки:** внутренний mutation без требуемых полномочий не выполняется; рабочий HTTP Editor path и выключенный flag сохраняют ответы; не смешивать legacy layers с authoritative EditVersion.

## 5. Что было проверено и не повышено до нарушения

- `FeatureService` публикует realtime после выхода из transaction. Потеря best-effort уведомления после commit не доказывает необходимость Outbox; новый delivery SLA не задан.
- Дублирование проверок на записи и чтении не автоматически нарушение DRY: чтение должно обнаруживать несогласованный persisted snapshot. Общими должны становиться смысловые predicates, а не весь процесс и формат ошибок.
- Recovery хранит command/outcome отдельно от UI phase; это разные факты. Не сводить всё к одному enum только ради уменьшения полей.
- `attachRecoveryHost` кеширует detach, но production-вызов detach не найден. Потенциальная ошибка повторного bind после detach не включена как активный дефект без достижимого сценария.
- Основной workspace reader использует AbortController и generation; дефект legacy edit.ts не распространяется на него автоматически.
- Структура текущих больших UI-компонентов не потребовала рекомендации дробить их по лимиту строк. Критичнее явные границы состояния и I/O.

## 6. Проверки и повторяемость

| Проверка | Результат | Ограничение |
| --- | --- | --- |
| Полный `npm.cmd test -- --reporter=dot` в apps/frontend | 58 файлов, 501 тест прошли | Не браузерный E2E; F5 не покрыт текущим набором |
| `npm.cmd run typecheck` | Прошёл | Не проверяет runtime JSON и порядок async ответов |
| TypeScript AST import graph | 88 файлов; SCC 17 | Статические imports/exports, не bundle/call graph |
| Python AST imports | 185 файлов; 0 syntax errors; 0 проверенных boundary violations | Не pytest и не runtime/DB |
| Legacy Save/Delete probe | Оба проявления воспроизведены | Реальный store + Pinia, mocked HTTP, без UI |
| Backend pytest / DB integration | Не запускались | В найденном Python нет pytest/SQLAlchemy; Docker daemon не работает |

Команды из корня репозитория:

```powershell
node docs/full_refactoring/analyze-imports.cjs docs/full_refactoring/import-graph.json
node docs/full_refactoring/reproduce-legacy-edit-race.cjs docs/full_refactoring/legacy-edit-race.json
& 'C:/Users/dimon/AppData/Local/Programs/OSGeo4W/apps/Python312/python.exe' -B docs/full_refactoring/analyze-backend-imports.py docs/full_refactoring/backend-imports.json
```

Frontend scripts требуют уже установленные зависимости `apps/frontend/node_modules`. Python-скрипту достаточно стандартной библиотеки Python 3.12; путь OSGeo4W — доступный в данном окружении, не обязательный для проекта. Probe возвращает успех, когда воспроизводит описанный дефект; после исправления он намеренно сообщит, что описание нужно обновить. Это диагностический артефакт, не новый регрессионный тест в suite.

Обнаружение OSGeo4W уточняет прежнее ограничение: Python есть вне PATH, backend test environment отсутствует. Пакеты не устанавливались, Docker не запускался. Правки AGENTS.md существовали до этого аудита; аудит их не менял.

## 7. Обновлённый порядок

Подробности — [порядок исправлений](refactoring-order.md). Малые задачи F7/F3, затем проверяемое ограничение F6. Развязка F1/F2 выполняется соседними шагами, поскольку они составляют одну компоненту графа. На backend B1 сохраняет issued-handle protocol, B2 локализует persistence details одного сценария. F5 исправить до использования legacy UI, B5 — при развитии legacy application boundary. F4 и B4 остаются поздними улучшениями.

Не требуется глобальная миграция frontend на FSD, перенос всех типов backend в новый domain-пакет, шина событий или универсальный DI-контейнер. Новая граница считается полезной, если уменьшает конкретную связанность и даёт независимую проверку поведения, а не просто увеличивает число файлов.
