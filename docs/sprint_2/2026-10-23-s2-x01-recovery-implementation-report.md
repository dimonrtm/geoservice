# S2-X01 — отчёт реализации восстановления

Статус: выполнено и проверено 2026-10-23. Подзадача вне дней: календарь Sprint 2 не изменён. Изменения оставлены unstaged, без commit/push.

Основание: [карточка](2026-10-12-s2-x01-save-recovery-followup.md), [принятый дизайн](2026-10-23-s2-x01-recovery-design.md), [план](2026-10-23-s2-x01-recovery-plan.md), [журнал исполнения](2026-10-23-s2-x01-execution-ledger.md).

## Результат по трём шагам карточки

1. **Квитанция и current разделены.** Независимый recovery store хранит команды по actor/наряду/версии в IndexedDB до PUT. Known success при ошибке GET остаётся known; повторяется только чтение. Общий generation обычных и recovery GET и session epoch запрещают позднему ответу заменить новые данные. Backend, wire-контракт, миграции и транзакционная модель не менялись; `OutcomePending` не вводился.
2. **Намерение и навигация защищены.** Unknown A не блокирует B/C. Неизменные identity/payload переживают нормальное закрытие браузера в том же профиле. После обнаруженной потери доступа каждый контекст требует отдельного согласия. Dirty-переход предлагает сохранить/отказаться/остаться; первый сбой отменяет save-and-leave окончательно. Revert сохраняет две стадии согласия и историю. Stale удерживает source/candidate для сравнения, не переносит попытку автоматически.
3. **Сообщения опираются на доказательства.** No-op определяется по source, а при недостатке evidence используется нейтральное «Прежняя операция выполнена». Позиционная точность и топология показаны непроверенными. Таблица XY и отдельный map overlay не меняют current. Ручной разбор содержит доступные идентификаторы без auth tokens и без выдуманного ответственного.

## Проверки

| Проверка | Результат |
| --- | --- |
| Frontend `npm.cmd test -- --maxWorkers=2` | exit 0: 323/323, 0 failed suites |
| `npm.cmd run typecheck` | exit 0 |
| `npm.cmd run lint` | exit 0 |
| `npm.cmd run format:check` | exit 0 |
| `npm.cmd run build` | exit 0; Vite предупреждает о JS chunk более 500 kB, итоговый JS около 1.26 MB / gzip 359 kB |
| `infra/db-tests.cmd` | exit 0: 270 passed; две прежние deprecation warnings (`crypt`, `BlockingPortal`) |
| `node run.mjs` в `infra/m4` | exit 0: 7/7, retries=0, проект `geoservice-m4-efccbc54`; отдельный access-прогон также exit 0 (1/1) |
| `git diff --check`, UTF-8/LF | Проверены все изменённые и новые текстовые файлы, включая untracked |
| `scripts/lint-wiki.py --root .` | 37 известных missing_frontmatter только в RAW_inputs; затронутые Code_wiki без новых ошибок |

Sandbox не позволял esbuild spawn: тесты/сборка выполнялись с предусмотренной эскалацией. Промежуточные failures не скрыты: новая keyboard-проверка выявила отсутствие явного циклического Tab; access-fixture сначала нарушал NOT NULL, затем назначал исходному actor, затем ожидал 403 вместо контрактного 404. Fixture исправлен без изменения backend. Неуспешный прогон с оставшимся недоступным нарядом остановлен, его изолированная среда удалена runner. Успешный evidence принимается только с новым run ID и exit 0.

## Матрица X01-01–16

Пути тестов ниже относительно `apps/frontend/src`, если не указано иное.

| Критерий | Проверка и наблюдаемый результат |
| --- | --- |
| X01-01 | `infra/m4/recovery.spec.ts`, `s2-x01-recovery.spec.ts`: настоящий commit, потеря ответа, прежний payload/CommandId, replay и отдельный GET. Revision/events/commands после replay равны снимку первого commit. Save и Revert отдельно. |
| X01-02 | `s2-x01-recovery.spec.ts`: `launchPersistentContext` закрывается и запускается заново с тем же userDataDir, без storageState/import. [Save](evidence/s2-x01/save-browser-restart.json), [Revert](evidence/s2-x01/revert-browser-restart.json). |
| X01-03 | A/B unknown, C успешно сохранён в реальном UI; `workspaceRecovery.test.ts`, `workOrders.multicontext.test.ts` подтверждают независимость и scoped callbacks. [Evidence](evidence/s2-x01/multi-context.json). |
| X01-04 | Более новый Save через публичный HTTP test driver и поздний replay первого Save: current остаётся новым, counters не растут. UI намеренно запрещает новый Save занятой версии; этот driver не выдается за пользовательский обход. |
| X01-05 | Реальный logout → другой actor → возврат исходного: чужие recovery скрыты, PUT отсутствует до каждого согласия; `auth.epoch.test.ts` и `http.test.ts` защищают новую сессию от позднего ответа. |
| X01-06 | `workspaceRecovery.test.ts`: потеря доступа A останавливает только A; global role loss останавливает actor. M4 отзывает назначение в тестовой БД и проверяет возврат после отдельного согласия: [evidence](evidence/s2-x01/access-restoration.json). |
| X01-07 | `workOrders.recovery.test.ts`, `workOrders.multicontext.test.ts`, `workspaceComparison.test.ts` и M4: source/candidate удержаны, current из GET; preview read-only, отказ очищает выбранную попытку. |
| X01-08 | `workOrders.recovery.test.ts`: refresh до обязательного readback сохраняет команду; после завершённого stale GET материал не восстанавливается, как принято в дизайне. |
| X01-09 | `workOrders.edit.test.ts`, `WorkspaceEditCommands.test.ts`: dirty → discard → отмена baseline consent не возвращает draft и не вызывает PUT. DB/M4 подтверждают baseline/history при Revert. |
| X01-10 | `workOrders.navigation.test.ts`: stay/discard/success, unknown с late success, GET error с поздним manual GET, domain rejection, protocol/storage failure. Переход выполняется только при непрерывном успехе исходной команды. |
| X01-11 | `workspaceRecoveryMigration.test.ts`, `workspaceRecoveryIndexedDb.test.ts`, Chromium storage spec: receipt прерванного импорта не воскрешает завершённую команду; source legacy отсутствует явно. |
| X01-12 | Storage/CAS/parser tests, `workOrders.edit.test.ts` и `.recovery.test.ts`: write failure не допускает PUT, cleanup failure сохраняет known result и block. Chromium: повреждённый key не уничтожает B и скрыт от другого actor. |
| X01-13 | `workspaceCommandPresentation.test.ts`, `workOrders.edit.test.ts`, `WorkspaceEditCommands.test.ts`: no-op только с evidence, исторический результат нейтрален, positional/topology unverified. |
| X01-14 | Существующие `apps/backend/tests/integration_tests/test_edit_geometry_spatial.py`, `test_save_geometry_atomicity.py` в новом DB-прогоне: нулевой сегмент/atomic rejection, no-op и replay. Реализация backend повторно не создавалась. |
| X01-15 | `workspaceRecoveryScheduler.test.ts`, `workspaceRecovery.test.ts`, `workOrders.recovery.test.ts`: FIFO max 2, single flight, пять дополнительных/пять всего, frozen payload и epoch check при выполнении очереди. |
| X01-16 | M4: safe focus, Tab/Shift+Tab wrap, Escape, возврат инициатору; `dialogFocus.test.ts`, command/map/store tests: direct guards, overlay без мутации current. Шесть viewport со screenshots, root horizontal overflow отсутствует. |

## UI и визуальная проверка

Сквозной проход использует настоящий Chromium, MapLibre, frontend и backend. Сценарии выполняются Playwright через UI; отдельного ручного кликанья человеком не заявляется. Изображения 1440×900 и 384×512 просмотрены агентом: подписи, source/candidate/current и read-only overlay различимы; на узком экране контент доступен прокруткой. Сохранены также 1024×768, 768×1024, 720×450, 512×384. Это viewport reflow, не настоящий zoom 200%.

- [Большой экран](evidence/s2-x01/comparison-1440x900.png).
- [Узкий экран](evidence/s2-x01/comparison-384x512.png).
- [Регрессия прежних M4](evidence/s2-x01/legacy-m4/save.json): новые результаты сохраняются отдельно от исторического evidence Дня 12.

## Независимое review и исправления

Итоговое read-only review выполнено отдельным агентом. Подтверждённые Important замечания исправлены:

- Dirty B при sent/stale A теперь требует разрешить draft B; logout отдельно перечисляет потерю stale-материалов.
- Storage/protocol/identity failure отменяют save-and-leave, диалог не остаётся в бесконечном saving.
- Сетевой сбой списка сохраняет последние подтверждённые назначения; отсутствие сохранённого наряда A не останавливает B/C.
- Global role/auth loss останавливает все контексты actor; устаревший ответ не сбрасывает новую сессию.
- Cancel stale очищает material/preview, direct actions сохраняют guards.
- Более новый recovery GET открывает workspace независимо от порядка завершения старого ordinary GET; поздняя ошибка старого GET не закрывает принятое новое workspace.

Регрессионные тесты гонок наблюдались RED→GREEN. Дополнительно M4 выявил запись overlay при teardown уже уничтоженной карты; запись из дочернего unmount удалена. Проверка keyboard выявила переход фокуса к browser chrome; explicit Tab wrap исправлен и проверен в Chromium. Открытых подтверждённых Critical/Important замечаний нет; повторный полный review не подменяет regression suite.

## Решения исполнения и ограничения

- Работа в существующем checkout `first-edit-save`; пользователь не просил новую ветку/worktree. Git-операции staging/commit/push запрещены, журнал остаётся в docs.
- `fake-indexeddb` — test-only dependency. Native adapter выделен в `workspaceRecoveryIndexedDb.ts`, legacy parser/writer остался для миграции/старых fixtures; production v1 не пишет.
- Имена и группировка тестов уточнены: navigation проверяется на store и реальном браузере, comparison — domain/map/M4; отдельные дублирующие component suites не добавлялись. `WorkspaceComparisonPanel` соответствует плановому `WorkspaceStaleComparison`. Test helpers — `recoveryIntegration.ts`, а не второй самописный IDB adapter.
- Временные browser profiles сохранены в игнорируемом test-results для диагностики. Они не включаются в артефакты и не являются пользовательским профилем.
- Не реализованы offline drafts, cross-tab lock, multi-device recovery, repair уничтоженного storage, history UI, evaluator и автоматический перенос stale candidate. После завершённого stale readback refresh может удалить временное сравнение.
- Fixture/аккаунты/геометрия синтетические. Производственная и геодезическая валидация не заявляются.
- Технические ноды Code_wiki обновлены через repository-change; прежний FU-2026-10-11-001 по metadata/fixture не закрыт. Отдельная agent-memory запись не нужна: причины и контракты сохранены здесь и в архитектурной ноде.
