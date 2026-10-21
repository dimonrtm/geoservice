# День 12 — план реализации восстановления после сбоев

> **Для исполнителя:** применять `superpowers:executing-plans` либо, если пользователь выберет делегирование, `superpowers:subagent-driven-development`. Выполнять задачи последовательно, отмечая шаги. Запрет репозитория на `git add`, `git commit`, `git push` имеет приоритет.

**Цель:** завершать восстановление Save/Revert без потери сохранённых изменений и без повторной mutation.

**Архитектура:** расширить существующий `useWorkOrdersStore`, общий pipeline отправки и панель команд. Current получать отдельным GET; подтверждение Revert связывать с контекстом в store. Существующие API и persisted recovery schema сохраняются.

**Технологии:** Vue, Pinia, TypeScript; существующие Vitest/Vue Test Utils, pytest и изолированный DB runner. Для M4 отдельно принят Playwright Test в `infra/m4`.

**Спецификация:** [принятый дизайн](2026-10-20-day-12-recovery-design.md); [анализ и D12-01–D12-20](2026-10-20-day-12-recovery-analysis.md).

Статус: пользователь поручил реализацию 2026-10-21; задачи 1–5 выполнены; оба объединённых сценария M4 прошли. См. [отчёт](2026-10-20-day-12-recovery-implementation-report.md). Задачи 1–4 описывают продуктовую часть; задача 5 дополнена после отдельного принятия инструмента и содержит команды, устройство окружения и assertions.

## Общие ограничения

- Ручной retry и recovery после refresh: пять попыток, задержки перед ними `[0, 2000, 5000, 10000, 20000]` мс. Первоначальная отправка: один PUT плюс до пяти повторов.
- Все повторы сохраняют actor, target, `CommandId`, исходный token и geometry; новый GET не меняет pending payload.
- При известном исходе ручной повтор чтения выполняет один GET и ноль PUT.
- До успешного stale readback нельзя отказаться от попытки и начать новую. После readback refresh может потерять отвергнутый draft — граница Дня 9.
- Первый отказ от dirty draft окончателен; отмена следующего подтверждения его не восстанавливает.
- Unknown блокирует переключение наряда. Восстановление после обнаруженной потери доступа остаётся S2-X01.
- Revert использует baseline и feature из change set. Новый endpoint, storage schema, production debug endpoint и новая зависимость не планируются.
- Нельзя считать `operation=unchanged` доказательством Revert или отсутствия mutation.
- Текстовые файлы — UTF-8/LF; `.cmd`/`.bat` — CRLF. Изменения оставлять unstaged.
- Выбор инструмента M4 и способа потери ответа принят отдельно 2026-10-21; детали в задаче 5.

## Особое внимание при review

1. Двойной вызов action до первого `await` не создаёт две серии или два GET — задача 1.
2. Поздний callback после смены actor/token не отправляет Revert — задача 2.
3. Неудачная запись/очистка storage не открывает путь к следующей mutation — задачи 1–2.
4. Отмена второго диалога клавишей Escape не возвращает окончательно отменённый draft — задача 3.
5. Историческая квитанция после replay не подменяет более новый current — задачи 1 и 5.

## Файлы и ответственность

Пути ниже относительно корня репозитория.

| Файлы | Ответственность |
| --- | --- |
| `apps/frontend/src/stores/workOrders.ts` | Guards, retry/readback/stale actions, confirmation context, Revert |
| `apps/frontend/src/stores/workOrders.recovery.test.ts` | Серии, чтение, stale, storage/access/identity |
| `apps/frontend/src/stores/workOrders.edit.test.ts` | Создание Revert и контекст согласия |
| `apps/frontend/src/stores/workspaceRetry.ts`, `workspaceRetry.test.ts` | Существующие интервалы/отмена; менять только при необходимости общей защиты |
| `apps/frontend/src/domain/workspaceCommandPresentation.ts`, `.test.ts` | Доступность действий и сообщения |
| `apps/frontend/src/components/WorkspaceEditCommands.vue`, `.test.ts` | Recovery actions, диалоги, фокус |
| `apps/frontend/src/composables/map/useWorkspaceLineInteraction.ts` | Запрет взаимодействия при подтверждении, marker/selection |
| `apps/frontend/src/components/WorkspaceLineInteraction.test.ts` | Проверки карты и смены контекста |
| `docs/sprint_2/2026-10-20-day-12-recovery-implementation-report.md` | Создать при реализации: фактические проверки и ограничения |

Не выделять новый controller/store. Backend первоначально не менять: существующие replay, baseline и readback уже реализованы. Выявленный дефект оформлять отдельно с воспроизводимым тестом.

## Задача 1. Серии повторов, одиночное чтение и завершение stale

**Файлы:** store и recovery tests из таблицы.

**Интерфейсы:** сохранить `retryPendingSave(): Promise<void>`, `refreshCurrentWorkspace(): Promise<void>` и `restorePendingSave(): Promise<void>`. Добавить `discardRejectedAttempt(): boolean`. Новые read-only getters `canRetryPendingCommand: boolean`, `canRetryCurrentRead: boolean`, `canDiscardRejectedAttempt: boolean` будут использоваться панелью; actions повторно проверяют эти условия.

- [x] Добавить тест `manual_retry_runs_five_attempts_with_frozen_command`: после исходного unknown обнулить счётчик HTTP; ручная серия выполняет пять PUT с интервалами 0/2000/5000/10000/20000, все payload и target равны исходным. После исчерпания новый ручной запуск допускает ещё пять попыток.
- [x] Добавить тесты `manual_retry_is_single_flight` и `terminal_result_stops_retry`: два синхронных вызова дают одну серию; success/rejection/block останавливают её. При отмене контекста late response не меняет новую рабочую область. Проверить сохранение запрета другого наряда.
- [x] Добавить тесты `manual_read_is_one_get_without_put`, `manual_read_is_single_flight`, `stale_discard_requires_readback`: success/stale с ошибкой чтения сохраняют известный исход; повтор даёт один GET; discard до успешного GET возвращает false, после него true и не вызывает HTTP.
- [x] Добавить регрессии storage cleanup failure, refresh после завершённого stale readback и historical result + newer current. Для последнего утверждать, что показанный workspace равен ответу GET, а не результату старой команды.
- [x] Запустить из `apps/frontend`: `npm.cmd test -- --maxWorkers=2 src/stores/workOrders.recovery.test.ts src/stores/workspaceRetry.test.ts`. Убедиться, что новые требования дают assertion failures, а не ошибку окружения.
- [x] Реализовать действия/getters в `workOrders.ts`: синхронно занять слот до первого `await`, освобождать только владельцем текущего запуска; ручной retry использует существующую серию. Не разрешать второму вызову отменять и заменять уже активную серию. Для GET сохранить отдельную защиту от параллельного чтения и проверки request generation.
- [x] Реализовать discard только для разрешённого stale после readback/cleanup: очистить draft, candidate и ошибку; новый edit начинает работу с current. Не очищать unknown и не обходить storage/access guards.
- [x] Повторить команду тестов; ожидается PASS. Покрытие: D12-01–07, D12-14–16.

## Задача 2. Revert через существующий pipeline

**Файлы:** `workOrders.ts`, `workOrders.edit.test.ts`, `workOrders.recovery.test.ts`.

**Интерфейсы:** добавить store state `revertConfirmation: RevertConfirmationContext | null`, где контекст содержит уникальный `confirmationId: string`, actor/workOrder/editVersion/feature IDs и исходный token с типами существующего workspace. Добавить `beginRevert(): "resolve-dirty" | "confirm" | "blocked"`, `discardLocalDraftForRevert(confirmationId: string): boolean`, `cancelRevert(confirmationId: string): void`, `confirmRevert(confirmationId: string): Promise<void>`. Фазу диалога хранить в контексте как `"resolve-dirty" | "confirm"`; `workspaceInteractionLocked: boolean` отражает наличие контекста.

`beginRevert` создаёт контекст без UUID команды. `discardLocalDraftForRevert` окончательно очищает draft и переводит тот же контекст в confirm. `confirmRevert` проверяет ID контекста, фазу, identity/token и полномочия; только затем создаёт UUID команды. Это новые внутренние интерфейсы реализации, а не расширение публичного API.

- [x] Добавить `revert_uses_change_set_baseline_without_selection`: clean workspace с persisted change set и без выбранной линии; begin/confirm создают один PUT для `changeSet.featureId`, geometry равна baseline, token равен current, ID новый, storage записан до PUT.
- [x] Добавить `discard_dirty_then_cancel_does_not_restore_candidate`: первый выбор продолжения сохраняет draft и даёт ноль PUT; отказ очищает draft сразу; отмена confirm оставляет его очищенным и даёт ноль PUT.
- [x] Добавить `stale_confirmation_callback_cannot_send`: смена actor/workspace/token, потеря доступа и повторный callback дают ноль дополнительных PUT. Команды редактирования и Save не проходят при открытом подтверждении, в том числе при прямом вызове store.
- [x] Добавить `revert_storage_failure_prevents_put`, `revert_unknown_reuses_command_without_confirmation`, `stale_revert_requires_new_consent_and_id`. Если после stale GET change set отсутствует, новая команда не создаётся.
- [x] Запустить `npm.cmd test -- --maxWorkers=2 src/stores/workOrders.edit.test.ts src/stores/workOrders.recovery.test.ts`; зафиксировать ожидаемые failures новых проверок.
- [x] Реализовать интерфейсы в store. Вынести общий участок подготовки/отправки Save и Revert в приватный helper в том же файле, принимающий frozen `PendingGeometryCommand`; сохранить порядок persist → PUT → terminal record → GET → cleanup. Не переносить бизнес-правила в компонент.
- [x] Инвалидировать контекст при смене identity/token и доступа; проверять snapshot заново на confirm. Успешный Revert использует тот же readback/cleanup и очистку выбора, что Save. При readback failure новые правки остаются закрыты.
- [x] Повторить тесты; ожидается PASS. Покрытие: D12-08–13, D12-15.

## Задача 3. Recovery actions, диалоги и карта

**Файлы:** presentation, панель, map composable и соответствующие tests из таблицы.

**Интерфейсы:** расширить `WorkspaceCommandPresentation` полями `canRetryCommand`, `canRetryRead`, `canDiscardRejectedAttempt` типа boolean. Добавить соответствующие getters и confirmation lock в `WorkspaceCommandState`. Компонент вызывает интерфейсы задач 1–2; собственные таймеры/HTTP отсутствуют.

- [x] Добавить presentation tests по всем строкам матрицы спецификации: unknown показывает retry; failed GET известного результата — read; завершённый stale — discard; блокировки скрывают полномочия. Проверять нейтральные сообщения результата после refresh, не выводить тип действия из `operation=unchanged`.
- [x] Добавить component tests для кнопок «Повторить запрос», «Повторить загрузку», «Отказаться от отклонённой попытки»: реальный store с HTTP promises/fake timers; assertions проверяют количество запросов, а не только disabled.
- [x] Добавить проверки двух отдельных диалогов: безопасный начальный фокус, Tab/Shift+Tab, Escape, возврат фокуса; `escape_after_discard_keeps_draft_discarded` отдельно. Live region одна; обновление retry не перехватывает фокус.
- [x] Добавить map tests: drag/выбор блокируются при confirmation; изменение контекста закрывает диалог; после Revert + GET + cleanup выбор снят и маркер отсутствует. Проверить, что watcher блокировки карты не инвалидирует собственный действующий диалог.
- [x] Запустить `npm.cmd test -- --maxWorkers=2 src/domain/workspaceCommandPresentation.test.ts src/components/WorkspaceEditCommands.test.ts src/components/WorkspaceLineInteraction.test.ts`; проверить ожидаемый RED.
- [x] Реализовать presentation, кнопки и диалоги с контекстом store. Удалить placeholder Revert; сохранить пояснение о позиционной точности и фокусные правила Дня 11.
- [x] Подключить confirmation lock к map interaction и store actions; UI должен отражать тот же запрет. Не смешивать блокировку изменения геометрии с отменой действующего согласия.
- [x] Повторить тесты; ожидается PASS. Покрытие: D12-01–16, D12-20 на уровне frontend.

## Задача 4. Регрессия продуктовой части

**Интерфейсы:** итог задач 1–3; новых контрактов нет.

- [x] Из `apps/frontend` выполнить `npm.cmd test -- --maxWorkers=2`, затем `npm.cmd run lint`, `npm.cmd run build`. Ожидаются exit code 0 и отсутствие ошибок.
- [x] Выполнить `npm.cmd run format:check`; если имеются исходные несвязанные нарушения, отдельно проверить изменённые файлы и явно перечислить ограничение, не форматировать весь репозиторий.
- [x] Из корня выполнить `.\infra\db-tests.cmd` в доступном Docker-окружении. Это отдельный регрессионный прогон, а не шаг внутри M4: runner пересоздаёт только своё тестовое окружение.
- [x] Проверить результат существующих integration suites `test_save_geometry_events.py`, `test_save_geometry_atomicity.py`, `test_geometry_save_api_integration.py`, `test_workspace_draft_readback.py`, `test_workspace_save_concurrency.py` в `apps/backend/tests/integration_tests/`. Они подтверждают серверные предпосылки, но не фактический restart/refresh.
- [x] Выполнить `git diff --check` и проверить окончания строк новых/изменённых файлов. Создать отчёт с фактическими результатами; до задачи 5 статус M4 — «не проверена».

## Задача 5. Объединённая проверка M4 — после отдельного выбора способа

**Точка решения закрыта 2026-10-21:** пользователь принял [первый вариант](2026-10-21-day-12-m4-tool-options.md): Playwright Test и потерю настоящего ответа после commit через `route.fetch()` / `route.abort()`.

**Файлы и исполнение:** `infra/m4/compose.yml` задаёт отдельные PostGIS, API и frontend; `run.mjs` создаёт уникальный Compose-проект, выполняет миграции/seed только до сценариев и удаляет только этот проект после завершения. `playwright.config.ts` и `recovery.spec.ts` запускают Chromium, реальные UI-действия и read-only SQL assertions. Зависимость зафиксирована в отдельном `infra/m4/package-lock.json`, приложение не получает новых зависимостей.

**Команды:** из `infra/m4`: `npm.cmd ci`, `npx.cmd playwright install chromium`, `npm.cmd test`. Runner перезапускает API через `docker compose -p <уникальный-проект> -f compose.yml restart api`. API запускает только uvicorn; повторный seed при restart исключён. Evidence: `docs/sprint_2/evidence/day-12/m4/`.

**Assertions:** реальный success до потери ответа; прирост revision/events/command registry ровно на один; неизменность baseline; блокировка повторов до новой навигации после restart; тот же actor, URL и исходный JSON; исторический success при replay; отдельный GET после replay; актуальная geometry/change set, отсутствие выбранной линии/маркера; нулевой прирост счётчиков после replay. Сетевые трассы с auth headers не сохраняются.

**Контракт проверки:** действующая сессия того же actor, настоящее UI-действие, тот же tab/sessionStorage, отдельное тестовое окружение и сохранение БД между первым commit и replay. Ни synthetic recovery record, ни независимые тесты restart и retry не заменяют сценарий.

- [x] После выбора способа подготовить один сценарий Save и один Revert. Для каждого сохранить baseline, current, revision и количество соответствующих событий до первого PUT.
- [x] Выполнить content-changing действие через UI; доказать commit, скрыть ответ и не позволить автоповторам разрешить unknown раньше restart. Зафиксировать ID/token/payload и состояние БД после commit.
- [x] Перезапустить реальный backend-процесс без пересоздания БД/seed; подтвердить готовность нового процесса.
- [x] Обновить ту же вкладку; восстановление получает command из существующего sessionStorage. Проверить прежние ID/token/payload в replay и последующий GET.
- [x] Сравнить с состоянием после первого commit: replay добавил ноль к revision и ноль событий. Первая mutation дала ровно одно увеличение revision и одно соответствующее событие. Baseline не изменился.
- [x] Для Revert проверить очищенный change set и снятый выбор/маркер после GET; отдельной регрессией сохранить правило более нового current при историческом replay.
- [x] Выполнить ручной happy path и проверку клавиатуры/фокуса новых controls на размерах Дня 11. Не выдавать результаты unit tests за браузерную проверку.
- [x] Дополнить отчёт доказательствами без auth tokens/секретов. M4 принимать только при успешных обоих объединённых сценариях. Покрытие: D12-17–20.

## Завершение и передача

Все D12-01–D12-20 распределены между задачами. Выполненные при discovery 44 теста — исходная контрольная точка. Результаты реализации и обычного browser happy path приведены в отчёте; объединённые сценарии M4 прошли; доказательства — в 2026-10-21-day-12-m4-report.md.

Пользователь выбрал реализацию в текущем каталоге. Продуктовая часть выполнена последовательно в этом чате с отдельным итоговым review. Коммиты и push выполняет только пользователь. Выбор инструмента M4 принят отдельно; задача 5 выполняется по дополненному плану.
