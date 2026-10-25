# День 13: анализ сквозной автоматической проверки

Дата анализа: 2026-10-25. Календарная задача: День 13, суббота, 15 августа 2026 года.

Статус: анализ и уточнения завершены, подход и спецификация приняты. Наблюдения ниже относятся к исходному коду до реализации; фактические изменения и прогоны описаны в [отчёте](2026-10-25-day-13-smoke-implementation-report.md).

## Основания

- [ТЗ спринта](2026-07-31-sprint-2-technical-requirements.md), разделы 2–5, 11, 14–16: Save одной внутренней вершины L-003, durable readback, retry, Revert, неизменность authoritative baseline.
- [Календарь](2026-07-31-sprint-2-calendar-plan.md): День 13 добавляет smoke phases Save и verify/retry/revert, четыре отрицательных исхода и CI; День 14 сохраняет отдельную финальную приёмку и ручной demo.
- [M4](2026-10-21-day-12-m4-report.md) и [отчёт S2-X01](2026-10-23-s2-x01-recovery-implementation-report.md): исторические результаты, не доказательство нового прогона текущего checkout.
- [Инварианты](../../DDD_Wiki/invariants/edit_version_persisted_edit_invariants.md), [серверная state machine](../../DDD_Wiki/state_machines/edit_version_save_request.md), [команда](../../Wiki/commands/update_edit_version_feature_geometry.md), [recovery policy](../../Wiki/policies/editor_recovery_policy.md).
- [Память об изоляции БД](../agent-memory/bugfixes/2026-06-28-ci-smoke-401-seed-cleanup.md): DB integration cleanup ранее удалял пользовательскую EditVersion; RUN_DB_TESTS требует отдельную disposable БД.

Анализ технический: отдельное исследование доменной модели не запускается. Правила условной организации прочитаны; не требуется искать реальных сотрудников или внутренние документы.

## Что существует в коде

| Область | Наблюдение | Источник |
| --- | --- | --- |
| API smoke | Login → assigned WorkOrder → open EditVersion → workspace. Проверяются identity, AOI, 19 features и 9 associations. Нет Save, restart, retry, Revert и снимка baseline | `apps/backend/tests/smoke/full_path_workspace_smoke.py` |
| CI | Backend/frontend suites уже включены. DB integration выполняется отдельным Compose. Затем API smoke работает с demo Compose. Между smoke-фазами API не перезапускается. M4 не вызывается | `.github/workflows/ci.yml` |
| Save | Блокировка версии, проверка текущего доступа, reservation CommandId, fingerprint, stale, spatial validation, запись current/revision/terminal result/history. Matching retry возвращает terminal result до проверки старого token | `apps/backend/utility_service/use_cases/services/edit_version_service.py` |
| DB tests | Уже есть atomicity, no-op/revert/retry, durable rejection, history, concurrency и HTTP Save/readback/revert/stale/old replay | `apps/backend/tests/integration_tests/test_save_geometry_*.py`, `test_geometry_save_api_integration.py` |
| Browser M4 | Реальный commit → потеря ответа браузеру → restart API → refresh → replay; сравниваются revision, commands, events и baseline EWKB | `infra/m4/recovery.spec.ts`, `recovery-helpers.ts` |
| Изоляция M4 | Уникальный Compose-проект, PostGIS на tmpfs, миграции/seeds до сценариев; API стартует напрямую через uvicorn. Restart API не повторяет seed chain. Runner очищает собственный проект | `infra/m4/run.mjs`, `compose.yml` |
| Browser harness | Chromium, один worker, retries=0, screenshot при ошибке, trace выключен; фиксированные host ports | `infra/m4/playwright.config.ts`, `compose.yml` |

M4 snapshot проверяет EWKB геометрии выбранного baseline feature. Это более узкое доказательство, чем сравнение всех полей всех DefaultStateFeature. Имеющийся CI fingerprint защиты demo от DB tests сравнивает identity/status WorkOrder, DefaultState и EditVersion; он не проверяет содержимое baseline features.

## Контракты, влияющие на доказательство

1. Content-changing Save/Revert увеличивает revision и добавляет одно событие. Retry/no-op не создаёт повторного изменения и события. Новый no-op при этом является отдельной зарегистрированной командой.
2. Обычный domain rejection сохраняет terminal запись команды, хотя current/revision/history остаются прежними. Поэтому требовать неизменности всей БД при отказе некорректно.
3. Reused CommandId должен сохранить исходный результат и identity команды; ошибку нельзя трактовать как новую успешно зарегистрированную операцию.
4. Ошибка parsing до use case не резервирует CommandId. Сценарий `GEOMETRY_INVALID` должен действительно достигать соответствующей проверки, а не завершаться ошибкой JSON/structure/stale раньше неё.
5. Outside AOI означает нарушение покрытия всей линии; касание границы разрешено. Отрицательная геометрия должна пройти предшествующие guards, чтобы доказать именно этот исход.
6. Revert передаёт baseline geometry из readback через тот же Save API. Его результат — current равен baseline, operation=unchanged, change set очищен; история фактического изменения остаётся.
7. Replay старой успешной команды не обязан совпадать с текущим workspace после следующего изменения. Историческая квитанция и current проверяются раздельно.

## Расхождения источников

- Старый Wiki command описывает pending operation, актуальный объект в replay и stale response. Более поздняя серверная state machine исключает pending response/polling. ТЗ требует строгую ошибку `{code,message,correlationId}`, а актуальный workspace читается отдельно. Код соответствует этому разделению. Старую формулировку нельзя непосредственно превращать в assertion.
- В календарном разделе S2-X01 ещё стоит «выполнение не начато», тогда как README и отчёт 2026-10-23 описывают реализованное расширение recovery. Для анализа нельзя считать исходный sessionStorage-контракт Дня 9 полным описанием текущего frontend.
- Fresh DB и restart API присутствуют в M4, но CI пока не соединяет их с обязательным автоматическим browser-прогоном.

Документы Wiki и календарь в рамках этого анализа не исправляются автоматически.

## Уточнения

### D13-Q01 — граница CI-приёмки

Нужно уточнить, включает ли обязательная автоматическая приёмка Дня 13 настоящий браузерный пользовательский путь в CI, помимо backend/frontend suites, DB integration и API smoke. В исходном календаре названы smoke phases; M4 и дополнительные сценарии S2-X01 появились позднее и сейчас выполняются отдельным runner.

Ответ пользователя: «Нет это пока локальная проверка». Браузерный M4 остаётся локальной проверкой; включение настоящего браузерного сценария в обязательный CI Дня 13 не требуется. Это уточнение не отменяет CI для API smoke и существующих backend/frontend suites и DB integration.

### D13-Q02 — объём доказательства неизменности baseline

ТЗ требует доказать неизменность DefaultStateFeature до и после сценария, но не определяет ширину снимка. Существующий M4 сравнивает EWKB геометрии только выбранной L-003; это не доказывает неизменность остальных полей и baseline features наряда.

Вопрос: требуется ли доказательство для всех baseline features WO-001 со всеми сохранёнными полями или только для геометрии редактируемой L-003?

Ответ пользователя: «Пока только геометрии редактируемой `L-003`». Обязательное доказательство ограничено геометрией соответствующего DefaultStateFeature; сравнение всех полей и остальных baseline features не требуется.

### D13-Q03 — повторная проверка отказов после restart

Календарь требует автоматического воспроизведения на fresh database и после restart. ТЗ явно требует сохранности успешного Save после restart backend, но не задаёт, должны ли все четыре отрицательных исхода также проверяться по обе стороны restart.

Вопрос: нужно ли для stale, reused CommandId, invalid geometry и outside AOI проверять повтор соответствующего запроса после restart backend или эти отрицательные проверки достаточно выполнить один раз за сквозной сценарий?

Ответ пользователя: «достаточно проверить эти отказы один раз за сквозной сценарий». Повтор всех четырёх отказов после restart не входит в обязательную матрицу Дня 13. Проверка успешного Save, его сохранности после restart, retry и Revert остаётся обязательной.

### D13-Q04 — повторный запуск завершённого smoke

Fresh database явно входит в обязательную приёмку. Не определено, должен ли весь smoke поддерживать повторный запуск на той же БД после предыдущего успешного завершения. После Revert геометрия возвращается к baseline, но revision, command registry и append-only history не возвращаются к начальному состоянию.

Вопрос: должен ли smoke повторно проходить на той же тестовой БД после успешного предыдущего прогона без очистки накопленных revision, команд и истории или каждый полный прогон начинается на fresh database?

Ответ пользователя: «каждый полный прогон начинается на fresh database». Между фазами одного прогона и при restart backend БД сохраняется. Поддержка повторного полного прогона на накопленной БД не является требованием.

## Дополнительная сверка после уточнений

- `test_save_geometry_rejections_integration.py` уже создаёт invalid geometry совпадением внутренней вершины с начальной: endpoints и число вершин сохраняются, но возникает запрещённый нулевой сегмент. Для smoke не требуется отдельная испорченная БД. Outside AOI проверяется перемещением только внутренней вершины за границу; конкретные координаты smoke должны соответствовать штатной demo fixture, а не произвольно копироваться из integration fixture.
- `test_geometry_save_api_integration.py` проверяет Save, новый HTTP client, no-op и Revert, включая очищенные changeSet/basicValidation и сохранённую историю. Создание нового ASGI app/client в этом тесте не является restart настоящего процесса backend.
- `scripts/start_utility_service.sh` при штатном запуске выполняет Alembic и seeds/upgrade fixture перед uvicorn. Следовательно, restart сервиса demo Compose повторяет startup chain. M4 запускает uvicorn напрямую и этой цепочки при restart не касается. Проверка через штатный demo Compose дополнительно охватывает сохранность результатов при повторном startup.
- Для доказательства restart необходимы фактическая смена запуска процесса/контейнера и readiness после неё. Один новый HTTP client не доказывает перезапуск.
- Состояние между фазами должно сохранять исходный CommandId, token, geometry, identity версии, terminal response и контрольные снимки. Повтор после restart обязан отправлять исходную команду, а не создавать новую с актуальным token. Это следствие действующего idempotency-контракта.
- Прямое чтение БД нужно отличать от выполнения сценария: пользовательские mutations идут через публичный API; контрольные чтения проверяют baseline geometry, revision, registry и историю. HTTP readback сам по себе не доказывает отсутствие повторного события.

## Согласованная граница задачи

1. Автоматический API-путь Save → restart backend на сохранённой БД → readback/retry/Revert включается в CI.
2. Настоящий browser M4 остаётся локальным. Перенос дополнительных сценариев S2-X01 в CI не входит в задачу.
3. Каждый полный прогон начинается на fresh database; данные не сбрасываются между его фазами.
4. Stale, reused CommandId, invalid geometry и outside AOI проверяются по одному разу за сквозной сценарий.
5. Обязательная неизменность baseline ограничена геометрией DefaultStateFeature линии L-003.
6. Backend/frontend suites и изолированные DB integration сохраняются. Их существующие проверки не заменяют live API smoke с настоящим restart.

После четырёх уточнений существенных открытых вопросов о пользовательском объёме задачи не осталось. Пользователь выбрал подход 1: расширить существующий API smoke и CI, затем принял [спецификацию](2026-10-25-day-13-smoke-design.md) и поручил выполнить [план реализации](2026-10-25-day-13-smoke-plan.md). Реализация отражена в отчёте; исторические наблюдения анализа не заменяют текущее состояние кода.

### Области дальнейшего уточнения

После ответа на D13-Q01 требуется определить неописанные границы доказательства: объём baseline snapshot, точное значение restart, покрытие отрицательных исходов относительно restart и объём включения сценариев S2-X01. Это ещё не принятые требования и не предложения реализации. Детали, однозначно установленные исходниками и принятыми контрактами, повторно пользователю не задаются.

## Память и изменения

Отдельная agent-memory запись не нужна: результаты анализа сохраняются здесь, ограничения изоляции уже записаны. Git staging/commit/push не выполняются.
