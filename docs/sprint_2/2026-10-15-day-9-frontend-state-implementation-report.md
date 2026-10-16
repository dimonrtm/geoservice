# День 9 — отчёт реализации frontend contracts и state

Дата: 2026-10-15. Основание: [принятая спецификация](2026-10-14-day-9-frontend-state-design.md) и [план](2026-10-14-day-9-frontend-state-plan.md).
Статус: реализация завершена; независимое review и заключительная проверка выполнены. Изменения оставлены unstaged.

## Что реализовано

- TypeScript contracts Save/workspace draft, runtime guards и geometry PUT client без скрытых повторов.
- Единственный Pinia workOrders store с раздельными current, localDraft, recoveryRecord/pendingCommand и commandResult. Локальная правка не изменяет current; Cancel не вызывает backend.
- Обязательная запись actor-scoped recovery record до PUT; проверки формата, запрет перезаписи другой команды, подтверждённые фазы для readback и явные storage errors.
- Ограниченная серия повторов с неизменяемым payload: пять после initial failure, пять при refresh, один при manual retry; паузы 0/2/5/10/20 секунд.
- После success актуальные geometry/token/changeSet берутся из GET. Ошибка GET не вызывает новый Save; historical receipt не подменяет current.
- Stale удерживает попытку для сравнения без automatic reapply; domain rejection, protocol/access/storage failures имеют отдельные переходы.
- Guards навигации, отмена retry timers, поколение запросов и остановка восстановления при потере доступа/смене actor. Старый callback не отправляет команду от другого пользователя.

## Матрица проверки

Имена suites ниже относительно `apps/frontend/src/`.

| Требования | Suite / доказательство |
| --- | --- |
| D9-01..02 | `api/workOrders.test.ts`, `contracts/workspace-edit.test.ts`: exact request, token, error propagation, mismatched IDs и summary |
| D9-03 | `domain/workspaceDraft.test.ts`, `stores/workOrders.edit.test.ts`: независимость current/candidate, dirty и Cancel |
| D9-04 | `stores/workOrders.edit.test.ts`: does not send when recovery write fails |
| D9-05 | `stores/workOrders.recovery.test.ts`: refresh before first PUT restores same intent |
| D9-06..07 | Там же: initial has five additional attempts; restore has five total attempts; manual single, fake timers |
| D9-08..10 | Там же и edit suite: success/readback, no-op, confirmed success refresh GET only, historical receipt/current |
| D9-11..12 | `stores/workspaceSaveErrors.test.ts`, recovery suite: stale comparison, malformed response, access/format distinction, cancellation |
| D9-13 | `stores/workspaceRecoveryStorage.test.ts`, recovery/edit suites: corrupt data/version/actor, inaccessible storage, cleanup/write failure |
| D9-14 | Recovery suite: old GET cannot overwrite post-Save readback; reset during retry delay; interceptor reset before catch |
| D9-15 | Recovery suite: dirty navigation blocked, assignment loss retains recovery, workspace access failure blocks replay |
| D9-16 | Существующие workOrders/auth/EditorWorkOrdersView и прочие frontend suites |

## Выполненные команды

Из `apps/frontend`:

- Targeted Vitest запускались после RED и реализации каждого этапа; подробности в [журнале](2026-10-15-day-9-execution-ledger.md).
- `npm test`: заключительная полная проверка после исправлений review — 30 suites, 216 tests, PASS.
- `npm run typecheck`: PASS.
- `npx vue-tsc -p tsconfig.app.json --noEmit`: PASS. Эта проверка явно охватывает app project, дополняя штатный typecheck.
- `npm run lint`: PASS.
- `npm run build`: PASS после разрешённого запуска вне sandbox. Build выполнил vue-tsc -b и Vite; предупреждение о chunk больше 500 kB, итоговый JS около 1,21 MB до gzip. Bundling оптимизация не входит в День 9.
- Prettier применён только к изменённым frontend файлам; `git diff --check` без ошибок.

Sandbox блокировал spawn esbuild с EPERM. Тесты и Vite повторно запускались с разрешением, а не обходом проверки или изменением конфигурации.

## Границы результата

Независимое review выявило три Important замечания; все воспроизведены пятью failing cases и исправлены за один проход. Регрессионная recovery suite: 22 tests PASS. Полный набор после исправлений: 216 tests PASS. Повторное review не выполнялось.

- Потеря доступа при отказе записи storage: actor-scoped блокировка хранится также в приватном runtime экземпляра store и переживает reset. После восстановления storage прежняя команда не возобновляется автоматически.
- Отказ доступа из PUT, readback GET или assigned list останавливает retry, скрывает workspace/localDraft/commandResult и сохраняет blocked recovery с известным результатом. Для каждого источника отказа есть отдельный тест.
- Повторный выбор той же вершины сохраняет candidate; переключение с изменённой правки на другую цель блокируется до явного Cancel.

Замечания о drag/кнопках/полном relogin UI и browser/backend restart отнесены к следующим дням согласно спецификации; они не заявлены проверенными здесь. Координация вкладок и восстановление после уничтожения storage не входят в гарантии. Backend не изменялся, frontend contracts сверены с существующей схемой.

Кнопки Save/Cancel/Revert, drag на карте и пользовательские диалоги ещё не реализованы: это дни 10–11. State/API callable и покрыты unit tests; нет заявления о завершённом browser demo. Реальный browser/backend restart, полный relogin resume и навигация с выбором остаются Дню 12/S2-X01.

Не добавлены backend endpoints, migrations, новые зависимости, offline mode, polling или межвкладочные блокировки. sessionStorage не даёт гарантии восстановления после его уничтожения. Принятый запрет записи при известной потере identity/access не заменяется новым CommandId.

## Решения исполнения

Работа выполнена в существующем checkout `first-edit-save`, без staging/commit/push. Журнал сохранён в docs/sprint_2 вместо commit-based scratch ledger. Общий test fixture исключает дублирование synthetic geometry. Initial auth failure без известного actor блокирует recovery records, не показывая их другой учётной записи.

Новая agent memory не создавалась: спецификация, план и этот отчёт сохраняют знания без дублирования. Repository-change ingest автоматически не запускался; отдельное описание нового runtime в Code_wiki пока не добавляется поверх этой документации.
