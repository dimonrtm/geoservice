# День 13: сквозная автоматическая проверка

Дата: 2026-10-25. Статус: спецификация принята пользователем («Принимаю»); реализация отражена в [отчёте](2026-10-25-day-13-smoke-implementation-report.md).

Независимая проверка полноты отдельным агентом выполнена 2026-10-25: существенных неотвеченных вопросов, мешающих планированию, не выявлено. Это проверка документа, не результат тестирования реализации.

Основание: [анализ и ответы D13-Q01–04](2026-10-25-day-13-smoke-analysis.md), [ТЗ спринта](2026-07-31-sprint-2-technical-requirements.md), [календарь](2026-07-31-sprint-2-calendar-plan.md). Пользователь выбрал подход 1: расширить существующий API smoke и CI.

## Цель и границы

CI должен автоматически доказать, что Editor может сохранить перемещение внутренней вершины L-003 в WO-001, прочитать сохранённое состояние после настоящего restart backend, повторить исходную команду без второй mutation и вернуть линию к baseline. Четыре отрицательных исхода должны проверяться через живой API. Геометрия соответствующего DefaultStateFeature остаётся неизменной.

Каждый полный прогон начинается на fresh database. Внутри прогона БД сохраняется между фазами, включая restart backend. Повторный полный прогон на накопленной БД не требуется. Браузерный M4 остаётся локальной проверкой и не включается в CI. Backend/frontend suites и isolated DB integration сохраняются.

Не входят: новые продуктовые возможности, изменение API или доменных правил, crash/restart PostGIS, искусственная потеря ответа в API smoke, повтор отрицательных запросов после restart, сравнение всех baseline features/полей, перенос S2-X01 browser suite в CI. Потерю ответа и browser recovery уже проверяет локальный M4; API smoke доказывает durable replay после restart.

## Рассмотренные подходы

1. **Расширить существующий smoke и CI — выбран пользователем.** Повторно используются login/open/workspace проверки и штатный demo startup. Добавляются две явно разделённые фазы с restart между ними. Меньше новой инфраструктуры; промежуточное состояние и lifecycle окружения требуют явных проверок.
2. **Отдельный runner с собственным стеком.** Изоляция могла бы целиком принадлежать runner, но это ещё один lifecycle рядом с CI smoke и M4. Не выбран.

## Устройство проверки

Основная точка входа остаётся `apps/backend/tests/smoke/full_path_workspace_smoke.py`. Существующий вызов без параметров сохраняет проверку открытия workspace. Новые явно выбранные фазы: `save` и `verify-retry-revert`. Названия CLI-параметров и размещение вспомогательных функций определяются при реализации.

Сценарные изменения выполняются только через публичный HTTP API. Read-only SQL-наблюдения нужны для независимой проверки baseline EWKB, revision, command registry и append-only событий. Smoke не очищает таблицы, не исправляет seeds, не обнуляет revision и не возвращает ошибочную fixture к ожидаемому состоянию скрытым Revert.

Перед первой mutation проверяются WO-001, actor, идентичность версии и baseline, L-003, eligibility, LineString из трёх вершин, отсутствие persisted change set и ожидаемое начальное состояние registry/history. Предыдущие CI-шаги могут уже открыть версию; это допустимо при её неизменённом состоянии. Неожиданное изменённое состояние означает ошибку подготовки fresh-прогона.

### Фаза Save

1. Login, assigned WorkOrder, open EditVersion, workspace с существующими проверками состава.
2. Сохранить стартовый снимок: идентификаторы, token, geometry L-003, baseline EWKB, revision, command/event records выбранной версии.
3. Сформировать допустимое перемещение только вершины с индексом 1. Координаты основываются на текущем workspace и штатной demo fixture. Endpoints остаются прежними; canonical result должен действительно отличаться от исходного. Не создавать бесконечный подбор кандидатов до случайного успеха.
4. Отправить Save с новым UUID и исходным token. Проверить 200, command identity, canonical resulting geometry, operation=updated, hasPersistedChangeSet=true и validation по действующему контракту, включая POSITIONAL_ACCURACY_UNVERIFIED.
5. Отдельным GET подтвердить resulting geometry, token, validation, changeSet с baselineGeometry и vertexIndex=1.
6. Read-only снимок подтверждает: revision увеличилась на 1, появилась одна successful command и одно persisted event, связанное с ней; baseline EWKB не изменился.
7. Записать завершённое фазовое состояние. При ошибке фаза завершается ненулевым exit code и не допускает продолжение как успешного Save.

### Restart

CI сохраняет время запуска контейнера backend, выполняет restart только `utility_service`, ждёт нового запуска и готовности API с ограниченным временем ожидания. Проверка не должна принять старый healthy status за завершённый restart. Изменившийся StartedAt и успешная readiness нового запуска обязательны.

Штатный `start_utility_service.sh` повторно выполняет migrations и create-once seeds/upgrade fixture. Это часть проверяемого startup: сохранённый draft и baseline должны пережить его. Между фазами запрещены reset БД, удаление volume и ручной reseed. PostGIS продолжает работать.

### Фаза verify/retry/revert

1. Проверить фазовое состояние и identity запуска; заново выполнить login и GET workspace. Сопоставить canonical geometry, token, validation и changeSet с результатом Save; SQL-снимок должен совпадать с состоянием после Save по проверяемым данным.
2. Повторить точный исходный Save с прежними CommandId, token и geometry. Ожидается исходный terminal result; revision, current, commands и events не меняются. Отдельный GET подтверждает актуальное состояние.
3. Проверить четыре отрицательных исхода по одному разу, в порядке таблицы ниже. После каждого сверять HTTP и независимый SQL-снимок.
4. Выполнить новый content-changing Revert через тот же PUT с новым CommandId, актуальным token и baselineGeometry из workspace readback. Не брать baseline для команды из seed-константы или SQL.
5. Подтвердить response и отдельный readback: current geometry равна исходной, operation=unchanged, hasPersistedChangeSet=false, changeSet/basicValidation очищены в workspace по действующему контракту. Token изменился; revision выросла ровно на 1, добавились одна successful command и один cleared event. Событие Save сохранилось.
6. Финальная геометрия baseline в EWKB совпадает со стартовой. Завершить итоговый JSON только после всех assertions.

## Отрицательные исходы

| Случай | Запрос | Ожидаемый результат и запись |
| --- | --- | --- |
| Stale | Новый CommandId, исходный token до Save, структурно допустимая geometry | 409 DRAFT_VERSION_STALE; одна terminal rejected command |
| Reused CommandId | CommandId успешного Save, изменённая внутренняя вершина, отличающийся canonical fingerprint | 409 COMMAND_ID_REUSED; исходная successful command не изменена, новая запись не добавлена |
| Invalid geometry | Новый CommandId, актуальный token, внутренняя вершина совпадает с начальной, endpoints/count сохранены | 422 GEOMETRY_INVALID; одна terminal rejected command |
| Outside AOI | Новый CommandId, актуальный token, только внутренняя вершина за AOI, линия simple и без нулевых сегментов | 422 GEOMETRY_OUTSIDE_AOI; одна terminal rejected command |

В каждом случае response содержит только code/message/correlationId, с корректным непустым сообщением и UUID correlationId. Current geometry, revision, baseline и event history не меняются. Для rejected command сверяются identity и сохранённый code/status; counters недостаточно для доказательства правильного отказа. Каждый случай должен проходить предшествующие guards и доходить до целевой проверки. Конкретные координаты и детали helper выбирает исполнитель, учитывая grid и штатную AOI; новая пространственная политика не вводится.

Для полного чистого сценария без дополнительных mutations ожидаются две successful commands (Save/Revert), три rejected commands и два события. Reused request и replay строк не добавляют. Не добавлять скрытые no-op или подготовительные Save, меняющие эти ожидания. Самостоятельная матрица no-op, concurrent requests и rollback остаётся в существующих DB suites.

## Состояние и evidence

Технический выбор автора спецификации: использовать JSON с версией формата и уникальным run ID. Он содержит только синтетические данные сценария: target IDs, исходную команду, terminal response, readback и SQL-контрольные снимки, фазовый статус. Auth tokens, пароли, connection strings и полные environment dumps не сохраняются.

Файл хранится в каталоге артефактов запуска, доступном вне процесса backend. Перед restart он выгружается из контейнера либо изначально записывается в доступное CI хранилище; следующая фаза получает именно этот файл. Конкретный механизм передачи выбирает исполнитель. Отсутствующий, неполный или несовместимый файл, неверная identity, повторное выполнение завершённой фазы — fail closed до PUT. Успешный документ сохраняется атомарно, старый evidence не считается результатом нового run.

Итоговый evidence содержит результаты этапов, StartedAt до/после, контрольные снимки, ожидаемые и фактические коды, конечный статус. При failure сохраняется доступная диагностика с указанием незавершённого этапа. CI публикует evidence и ограниченные логи до cleanup даже при ошибке. Нельзя публиковать auth headers или секреты в request dumps. Точное имя CI artifact и формат внутренних полей — детали реализации.

## CI и локальное выполнение

Существующий `smoke_test` расширяется последовательностью: fresh demo stack → health → isolated DB integration → существующие API проверки → Save → restart/readiness → verify/retry/revert → сбор артефактов → cleanup в always. Ошибка любой фазы проваливает job, автоматический повтор всего сценария не маскирует сбой.

Fresh database обеспечивается lifecycle нового CI runner и принадлежащего ему volume. Очистка относится только к этому CI stack. Не добавлять удаление пользовательского demo volume как способ локальной подготовки.

Локальный runbook воспроизводит те же фазы в явно disposable окружении. У текущего demo Compose есть фиксированные container_name и host ports: одного другого project name недостаточно для безопасной параллельности с пользовательским demo. Исполнитель должен описать безопасную подготовку отдельного окружения (например, отдельный Docker context/VM), либо ограниченный Compose override изоляции, если выберет автоматизировать локальный запуск. Отдельный полный runner не требуется. Не перезапускать обычный пользовательский backend ради проверки и не запускать destructive DB integration в demo-БД.

## Приёмка и проверки

- Smoke unit tests с fake transport обнаруживают неверный terminal result, HTTP code, snapshot mutation, несовпадение run/target, испорченное фазовое состояние; неизменный базовый smoke продолжает работать.
- Backend suite, frontend suite, штатные format/lint/typecheck/build и isolated DB integration выполняются применимыми командами проекта. Не подменять live restart новым TestClient.
- Live API smoke проходит на fresh test database с настоящим restart штатного backend. Revision/events/registry и baseline проверены на каждой значимой границе.
- В локальную регрессию входят существующие browser M4 и S2-X01 tests; их выполнение не становится CI browser job. Невозможность прогона явно отражается как непроверенная часть, а не успешная приёмка.
- Отрицательные проверки выполняются один раз; дополнительных циклов restart ради них нет.
- Сохраняются русский runbook и отчёт Дня 13 с командами, результатами и ограничениями. Новые материалы — в docs/sprint_2; итоговый acceptance report всего спринта остаётся Дню 14.

Если обнаружен дефект приложения, не расширять незаметно тестовую задачу до изменения доменного поведения: описать воспроизводимое отклонение и отдельно согласовать исправление. Документ и последующий план не разрешают staging/commit/push.
