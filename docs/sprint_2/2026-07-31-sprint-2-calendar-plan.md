# Календарный план Sprint 2

## Паспорт спринта

| Параметр | Значение |
| --- | --- |
| Период | 3–16 августа 2026 года |
| Длительность | 14 календарных интенсивных дней |
| Рабочий режим | Все дни периода, включая субботы и воскресенья |
| Цель | Получить полноценный UI-demo `edit -> save -> readback -> restart -> revert` для одной существующей line feature и одной внутренней вершины |
| Основной пользователь | Editor |
| Демо-контекст | `WO-001`, `L-003`, внутренняя вершина с индексом `1` |
| Главный критерий | Изменение сохраняется атомарно, переживает перезапуск и может быть возвращено к immutable baseline |

Подробные требования и критерии приёмки описаны в [техническом задании](2026-07-31-sprint-2-technical-requirements.md).

## Контрольные точки

| Дата | Контрольная точка | Проверяемый результат |
| --- | --- | --- |
| 7 августа | M1. Готов фундамент backend | Настройки координатной сетки, demo fixture, migration, модели и проверки геометрии готовы к использованию |
| 9 августа | M2. Работает транзакционное сохранение | Save, idempotent retry, rejection history и Revert подтверждены backend-тестами |
| 12 августа | M3. Работает основной UI-путь | Editor выбирает линию, перемещает внутреннюю вершину, сохраняет или отменяет изменение |
| 14 августа | M4. Работает восстановление | Readback после refresh/restart, stale refresh, retry и Revert проходят сквозной сценарий |
| 16 августа | M5. Sprint 2 принят | Полная матрица проверок и ручной UI-demo завершены; результаты отражены в acceptance report |

## План по дням

### День 1 — понедельник, 3 августа

Фокус: координатная сетка и воспроизводимые demo data.

- Добавить настраиваемые `UTILITY_GEOMETRY_XY_RESOLUTION` и `UTILITY_GEOMETRY_ROUNDING_MODE`.
- Зафиксировать default `0.0000001` градуса и `ROUND_HALF_AWAY_FROM_ZERO`.
- Сделать `L-003` трёхвершинной линией с редактируемой внутренней вершиной.
- После create-once seed chain атомарно обновлять только безопасные двухвершинные materialized-копии `L-003`; unsafe state блокирует demo startup.

Результат дня: fresh demo environment создаёт ровно одну пригодную для сценария линию, не меняя общие counts 19 features и 9 associations.

Проверка: settings tests, seed specification tests, upgrade service tests, startup contract и DB integration.

### День 2 — вторник, 4 августа

Фокус: схема данных первого сохранения.

- Добавить `draft_revision` в `EditVersion`.
- Добавить durable command registry.
- Добавить append-only change event history.
- Зафиксировать ограничения, индексы и связи с `EditVersion`.

Результат дня: migration описывает token, команды и историю изменений без дублирования baseline geometry в current snapshot.

Проверка: migration upgrade на чистой БД.

### День 3 — среда, 5 августа

Фокус: соответствие моделей схеме.

- Добавить SQLAlchemy models для command registry и change events.
- Проверить PK, FK, check/unique constraints и spatial indexes.
- Подтвердить цикл upgrade/downgrade/upgrade.

Результат дня: модели и metadata полностью соответствуют migration.

Проверка: migration integration tests и model metadata tests.

### День 4 — четверг, 6 августа

Фокус: детерминированные правила геометрии.

- Реализовать Decimal canonicalization по настроенной сетке.
- Проверить одинаковое округление положительных и отрицательных midpoint.
- Разрешить изменение только одной внутренней вершины.
- Запретить изменение endpoints, количества частей и вершин.
- Сформировать стабильный command fingerprint.

Результат дня: одинаковый запрос всегда приводит к одинаковой canonical geometry и fingerprint.

Проверка: unit tests для grid, structure guard и fingerprint.

### День 5 — пятница, 7 августа

Фокус: атомарный repository context.

- Блокировать нужный `EditVersion` на время Save.
- Читать current feature, immutable baseline и AOI в одной транзакции.
- Проверять существование, simple/valid geometry и покрытие AOI средствами PostGIS.
- Обновлять только current snapshot.

Результат дня: backend имеет безопасный persistence boundary; authoritative `DefaultState` не изменяется.

Проверка: repository integration tests и контрольная точка M1.

### День 6 — суббота, 8 августа

Фокус: успешный Save и идемпотентность.

- Реализовать synchronous Save transaction.
- Проверять `DraftVersionToken`.
- Резервировать глобально уникальный `CommandId`.
- Возвращать сохранённый terminal result при повторе того же запроса.
- Не увеличивать revision для no-op и idempotent retry.

Результат дня: один логический Save выполняет mutation не более одного раза.

Проверка: use-case tests для success, no-op, retry и command reuse.

### День 7 — воскресенье, 9 августа

Фокус: отклонения, события и Revert.

- Сохранять terminal rejection для команд, дошедших до use case.
- Разделить stale, reused command, invalid structure, invalid geometry и AOI errors.
- Записывать по одному append-only событию на content-changing Save или Revert.
- При Revert вернуть geometry к baseline и operation к `unchanged`.

Результат дня: положительные и отрицательные исходы воспроизводимы, а история изменения остаётся проверяемой.

Проверка: полная backend-матрица Save/Revert и контрольная точка M2.

### День 8 — понедельник, 10 августа

Фокус: API и durable readback.

- Добавить подтверждённый `PUT` endpoint.
- Сохранить строгую форму ошибок `{code,message,correlationId}`.
- Расширить workspace response полями token, persisted change set, validation и baseline geometry.
- Проверить Editor role и assignment guards.

Результат дня: UI получает всё необходимое для Save и Revert без локального знания seed coordinates.

Проверка: API contract tests, workspace service tests и OpenAPI review.

### День 9 — вторник, 11 августа

Фокус: frontend contracts и state.

- Добавить TypeScript contracts для Save и workspace draft.
- Добавить API client.
- Расширить Pinia store current draft, token, pending command и canonical response merge.
- Хранить uncertain pending request в `sessionStorage`.

Результат дня: frontend state поддерживает edit, retry, refresh и canonical response.

Проверка: store и API client unit tests.

### День 10 — среда, 12 августа

Фокус: взаимодействие с линией на карте.

- Разрешить выбор только eligible line.
- Показывать draggable MapLibre `Marker` только для внутренней вершины.
- Обновлять локальный draft во время drag.
- Не добавлять новую frontend dependency.

Результат дня: Editor может выбрать `L-003` и визуально переместить вершину с индексом `1`.

Проверка: component tests и ручной drag; контрольная точка M3.

### День 11 — четверг, 13 августа

Фокус: команды пользователя.

- Добавить Save, Cancel и Revert.
- Показать dirty state, progress и `POSITIONAL_ACCURACY_UNVERIFIED`.
- Блокировать повторный submit во время запроса.
- Добавить keyboard и accessibility states.

Результат дня: основной UI-сценарий понятен без технических знаний и не допускает случайной повторной отправки.

Проверка: view/component tests и responsive review.

### День 12 — пятница, 14 августа

Фокус: восстановление после сбоев и перезапуска.

- Повторять uncertain network outcome с тем же `CommandId`.
- После `DRAFT_VERSION_STALE` перечитывать workspace без автоматического повторного Save.
- Восстанавливать persisted change set после refresh и backend restart.
- Выполнять Revert по baseline geometry из readback.

Результат дня: сохранённое изменение не теряется, а повтор запроса не дублирует mutation.

Проверка: recovery tests, restart readback и контрольная точка M4.

### День 13 — суббота, 15 августа

Фокус: сквозная автоматическая проверка.

- Добавить smoke phases Save и verify/retry/revert.
- Проверить stale, reused `CommandId`, invalid geometry и outside AOI.
- Доказать неизменность `DefaultStateFeature` до и после сценария.
- Включить проверки в CI.

Результат дня: ключевой сценарий воспроизводится автоматически на fresh database и после restart.

Проверка: backend/frontend suites, DB integration и smoke tests.

### День 14 — воскресенье, 16 августа

Фокус: приёмка, документация и резерв.

- Выполнить полный regression suite.
- Провести ручной UI-demo от открытия `WO-001` до Revert.
- Проверить fresh `full-clean` setup.
- Исправить только дефекты, блокирующие основной сценарий.
- Создать `2026-08-16-sprint-2-acceptance-report.md`.
- Решить, нужен ли `/ingest repository-change` для новой устойчивой технической информации.

Результат дня: Sprint 2 либо принят по всем обязательным критериям, либо acceptance report явно перечисляет блокирующие отклонения.

Проверка: Definition of Done из ТЗ и контрольная точка M5.

## Связь backlog с календарём

| Backlog | Краткий результат | Основные дни |
| --- | --- | --- |
| S2-01 | Настраиваемая координатная сетка | 1, 4 |
| S2-02 | Редактируемая demo fixture | 1, 13 |
| S2-03 | Token, command registry и event history | 2–3 |
| S2-04 | Атомарное изменение одной line feature | 4–6 |
| S2-05 | Идемпотентный Save | 6–7 |
| S2-06 | Durable readback и Revert | 7–8, 12 |
| S2-07 | Save API и structured errors | 8 |
| S2-08 | Полноценный workspace editing UI | 9–11 |
| S2-09 | Retry, stale refresh и restart recovery | 9, 12 |
| S2-10 | Автоматическое и ручное доказательство | 13–14 |

## Ежедневный ритм

1. В начале дня — проверить результат предыдущего дня и открытые blockers.
2. Сначала добавить или уточнить проверку ожидаемого поведения.
3. Реализовать минимальный объём текущего дня без расширения scope.
4. В конце дня — запустить targeted tests и показать проверяемый результат.
5. Изменения оставлять unstaged для проверки пользователем; `git add`, `git commit` и `git push` не выполнять.

## Правила изменения календаря

- Если задача дня не завершена, сначала используется резерв внутри следующего связанного дня.
- Scope не расширяется за счёт attributes, associations, topology, reconcile, review/post или positional verification.
- При риске срыва сохраняются Save, readback, restart, retry и Revert; откладывается только визуальная полировка.
- Изменение дат или обязательных результатов фиксируется в этом документе до начала затронутого дня.

## Условия старта

- Доступен disposable demo environment.
- Штатный demo startup после create-once seeds автоматически выполняет transactional in-place upgrade старых безопасных copies `L-003`.
- Host CMD не запускает Python и не удаляет volume; повторный startup является no-op для уже трёхвершинной hierarchy.
- Destructive local `full-clean` разрешён только как ручной fallback для unsafe/invalid fixture или несовместимого disposable demo volume.
- Fallback-команда запускается из `infra`:

```powershell
docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml down -v
```

- После ручной очистки demo stack запускается повторно, чтобы create-once seeds создали обновлённую `L-003`.
