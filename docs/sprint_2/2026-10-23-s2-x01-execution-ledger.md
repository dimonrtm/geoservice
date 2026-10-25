# SDD ledger — plan: docs/sprint_2/2026-10-23-s2-x01-recovery-plan.md

Спецификация: `2026-10-23-s2-x01-recovery-design.md`. Пользователь поручил реализацию; последовательное исполнение основным агентом, итоговое независимое review. Изменения не индексируются и не коммитятся.

## Подготовка

- Исходная ветка `first-edit-save`, обычный checkout. Исходные изменения: README и три документа S2-X01 этого обсуждения; product code чистый.
- Ruling: работа выполняется в текущем checkout — developer instructions предпочитают подходящий существующий checkout, план и документы находятся здесь, создание отдельного worktree пользователь не запрашивал — при параллельной работе в том же каталоге возможны конфликты; проверять status и не затирать посторонние изменения.
- Ruling: журнал хранится в `docs/sprint_2/`, shell helpers skill для commit-based ledger не используются — запрет Git операций и требование сохранять артефакты в этой папке имеют приоритет — нужен ручной учёт проверок и состояния задач.
- Pre-flight 1→2→3: contracts/schema, storage и recovery согласованы; async adapter вводится до переключения старых потребителей.
- Pre-flight 3→4→5: host принимает readback, workOrders владеет snapshots, auth epoch инвалидирует старые callbacks. Временный auth delegate удаляется после переключения.
- Pre-flight 4→6→7: navigation связывается с CommandId; stale comparisons в памяти, preview не меняет current.
- Pre-flight 2–7→8→9: настоящий IndexedDB/browser restart и DB counters дополняют unit tests; прежние M4 сценарии сохраняются.

## Задачи — итог 2026-10-23

1. Контракты — complete: schema v2, frozen identity/source, проверка outcome/block/readback consistency, 4 tests.
2. IndexedDB/миграция — complete: 4 adapter tests, 2 migration tests, native Chromium CAS/corruption/receipt. Abort после request success не считается durable write.
3. Recovery/очередь — complete: независимые ключи, сериализация writes, 2 HTTP slots, single flight, access/session barriers, retry policy; store/scheduler tests и M4.
4. Workspace/Revert — complete: scoped snapshots/comparisons, общий read generation, постоянное opening intent; 6 multicontext tests и прежние integration suites.
5. Auth — complete: session epoch, поздние 401/403, остановка unloaded records и отдельное согласие; unit и реальный logout/relogin/access M4.
6. Навигация — complete: 8 tests на stay/discard/save, unknown/GET/rejection/storage/protocol и dirty B при stale A.
7. UI/сравнение — complete: список, per-context consent, XY/source unavailable/read-only overlay, честные no-op/quality; map/component/presentation tests, M4 keyboard и шесть viewport.
8. M4 — complete: 7/7, exit 0, проект `geoservice-m4-efccbc54`, retries=0. Отдельный access-прогон `geoservice-m4-7ec5cfbf`: 1/1, exit 0.
9. Полная приёмка — complete: frontend 323/323, DB 270/270; lint/typecheck/format/build exit 0; отчёт/карточка/wiki, LF и diff-check. Git staging/commit/push не выполнялись.

## Проверки и решения

- Baseline: `npm.cmd test -- --maxWorkers=2` — 287 tests / 34 files PASS. Sandbox esbuild `spawn EPERM`, разрешён запуск вне sandbox.
- Contracts RED: actor mismatch не отклонялся; GREEN: 3/3 tests.
- Ruling: для тестирования реального IndexedDB adapter использовать test-only `fake-indexeddb` вместо самописной эмуляции транзакций — ручная эмуляция могла бы скрыть abort/commit/CAS defects — дополнительная devDependency; реальный Chromium остаётся обязательным в M4.

- Ruling: native IndexedDB adapter выделен в workspaceRecoveryIndexedDb.ts; старый модуль реэкспортирует adapter и содержит v1 parser для миграции — уменьшает смешение форматов — старые v1 writers остаются только для legacy fixtures.

## Итоговые решения исполнения

- Ruling: navigation type и UI компоненты проверяются через store/domain/map tests и реальный браузер вместо трёх дублирующих component suites — эти уровни доказывают поведение с реальными событиями и HTTP — стоимость: ниже изоляция локализации UI failure.
- Ruling: `WorkspaceComparisonPanel` заменяет плановое имя `WorkspaceStaleComparison`; `recoveryIntegration.ts` и fake-indexeddb заменяют самописный adapter fixture — публичное поведение сохраняется — стоимость: сопровождение test-only зависимости.
- Ruling: native dialog дополнен общим `containDialogFocus` — Chromium RED показал уход Shift+Tab в browser chrome — стоимость: helper рассчитан на текущие button-only dialogs; при новых focusable controls его нужно расширить.
- Ruling: persistent profiles остаются в игнорируемом test-results, Docker-проект очищает runner — не нужны необязательные рекурсивные удаления — стоимость: локальное дисковое место, профили нельзя публиковать.
- Ruling: ручной UI-проход выполняется как воспроизводимый Playwright flow плюс визуальный просмотр agent screenshots — покрыты реальные UI/backend/MapLibre и keyboard — стоимость: не подтверждена человеческая usability-сессия и настоящий zoom 200%.
- Ruling: после новых проверок access fixture использует отдельного synthetic editor и контрактный `404 EDIT_VERSION_NOT_FOUND` — исходный 403 и nullable assignment не соответствовали backend — стоимость: fixture обслуживает именно текущий контракт скрытия недоступной версии.
- Ruling: lifecycle `blocked`/`session` добавлены в host interruption — иначе error branch оставлял pending navigation или останавливал только один key — стоимость: новые host implementations должны обрабатывать причины.
- Ruling: завершение по finishing-a-development-branch оставляет текущий checkout как есть — пользователь запретил stage/commit/push и не поручал merge — стоимость: интеграцию выполняет пользователь.

## Итоговое независимое review

Read-only reviewer: `s2_x01_final_review`. Проверены общий diff, spec/plan и риски actor/storage/readback/navigation. Critical не обнаружены. Important приняты к исправлению; регрессии добавлены до исправлений, новые opening race tests наблюдались RED→GREEN.

- Final: fixed dirty B при sent/stale A — navigation test; logout отдельно предупреждает о stale material.
- Final: fixed storage/protocol/identity failure оставлял saving navigation — interrupted/submit guard, RED→GREEN.
- Final: fixed временный network сбой списка трактовался как потеря всех назначений — multicontext regression, RED→GREEN.
- Final: fixed missing stored workspace A останавливал B/C — per-work-order suspension.
- Final: fixed global role loss останавливала только один recovery — actor suspension + session callback/interceptor, regression.
- Final: fixed cancel stale оставлял comparison/preview — recovery regression.
- Final: fixed ordinary/recovery opening race — durable workspaceReadIntent независимо от spinner, общий generation, obsolete error guard; оба порядка completion и поздняя ошибка RED→GREEN.
- Final: fixed UI keyboard wrap — реальный M4 RED→GREEN, helper unit и M4 Escape/restore-focus.
- Final: fixed map teardown — дочерний unmount больше не пишет overlay после parent map.remove; полный M4 GREEN.
- Final: Ruling: reviewer не оценивал уничтоженное storage, cross-tab/multi-device и refresh после завершённого stale readback — это явно исключённые/принятые границы spec — стоимость: эти случаи не получают гарантий восстановления.
- Final: Ruling: документация и финальные gates были отложены до fix pass — теперь выполнены и записаны в отчёте — стоимость: раньше промежуточный diff не был готов к приёмке.

Подтверждённых незакрытых Critical/Important и отложенных Minor нет. Повторное полное review не требовалось; fix pass закрыт regression tests и итоговыми suites.

## Финальные gates и evidence

- Frontend: `npm.cmd test -- --maxWorkers=2 --reporter=json --outputFile=node_modules/.cache/s2-x01-final.json`: 323 passed, 0 failed suites, exit 0.
- `npm.cmd run lint`, `typecheck`, `format:check`, `build`: exit 0. Build сохраняет предупреждение chunk >500 kB. Ошибка `.at()` для настроенного TS target исправлена индексированием; сборка повторно PASS.
- `infra/db-tests.cmd`: 270 passed, exit 0; две deprecation warnings сторонних библиотек.
- `node run.mjs`: 7 passed, exit 0; native IndexedDB, настоящий browser restart, A/B/C, account/access и keyboard. Два прежних M4 сохранены. Новые артефакты только `evidence/s2-x01`; прежние day-12 bytes восстановлены из HEAD после обнаружения перезаписи runner.
- Wiki: repository-change обновил две содержательные архитектурные ноды и реестр/index; существующий FU-2026-10-11-001 является основанием correction. Lint — только 37 известных RAW missing_frontmatter. Agent memory не дублирует архитектуру/отчёт; domain wiki и live state не синхронизировались автоматически.
- Все новые/изменённые текстовые файлы UTF-8/LF, `git diff --check` чист. Проверены untracked, JSON/evidence без auth secrets.

Итог: [отчёт](2026-10-23-s2-x01-recovery-implementation-report.md).
