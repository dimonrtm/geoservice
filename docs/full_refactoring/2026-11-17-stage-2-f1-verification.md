# SDD ledger — plan: docs/full_refactoring/2026-11-16-stage-2-f1-plan.md

Реализация разрешена пользователем 2026-11-17. Выполнение последовательно в текущем чате.

- Ruling: текущий checkout first-edit-save используется без нового worktree согласно плану и настройкам среды. Git writes не выполняются.
- Ruling: ledger и логи находятся в docs/full_refactoring вместо commit-based skill scripts; запрет add/commit/push и сохранение артефактов имеют приоритет.
- Pre-flight 1→2: EditorContext/DraftIdentity/SaveAttempt и смысловые операции owners согласованы.
- Pre-flight 2→3: workflow требует live ports; runtime устанавливается до auth.setAuth/restore.
- Pre-flight 3→4: UI получает runtime своего Pinia, локальный preview использует owner operations.
- Pre-flight 4→5→6: guards проверяют итоговую production-границу; документация и тесты подтверждают её после миграции.
- Baseline в sandbox: EPERM spawn esbuild до запуска тестов; повтор с escalation.

## Задачи

- 1–5: реализация выполнена, профильные проверки пройдены. Два замечания итогового ревью устранены с RED→GREEN.
- 6: завершена. Полный Vitest, дополнительные lifecycle/UI assertions, lint, typecheck, build и все 11 M4-сценариев пройдены (10 в общем запуске + 1 отдельным повтором после файловой ошибки screenshot).

## Проверки и решения реализации

- Baseline elevated: 190 passed, один timeout 5000ms в `auth store > keeps memory until backend confirms logout` при высокой параллельности. Повтор с maxWorkers=2: этот файл и профильные tests — 53 passed. Таймаут не увеличивался.
- Owners RED: 4 отсутствующие операции; GREEN: 53 passed вместе с исходными draft/navigation/auth tests.
- Runtime RED: отсутствующий модуль сборки. После подключения получены ошибки test setup в изолированных tests, намеренно подменяющих editor owners; runtime оставлен только в интеграционных tests с реальными owners.
- Identity RED→GREEN: Cancel и новая попытка в том же workspace не переиспользуют draft generation.
- Completion RED→GREEN: старый commandId и новая draft identity не меняют фазу новой попытки; A→B→A и порядок completion→navigation проверены отдельно без Pinia.
- Context RED→GREEN: force-close отменяет намерение навигации своего контекста.
- UI RED→GREEN: панель вызывает операции preview; hide сохраняет материал.
- Guard RED→GREEN: TS/Vue writes, aliases, storeToRefs, v-model, Object.assign и destructured ports, запрещённые imports. Production: 0 violations.
- Профильный editor/UI/presentation: 67 passed. Более поздний editor-only после devtools fix: 26 passed.
- Первый полный Vitest: 563 passed, 8 failed (семь App tests использовали runtime до vi.resetModules, один isolated workOrders test ошибочно устанавливал editor). Исправлено test setup, повтор соответствующих tests + editor: 38 passed. Полный повтор ещё ожидается.
- Первый build и lint прошли; сохраняется прежнее предупреждение Vite bundle >500 kB.
- Первый M4 выявил потерю binding в devtools action Proxy (браузер оставался на restore). Прочитан локальный Pinia wrapper, добавлен воспроизводящий RED-тест. Binding использует стабильный `$state`, GREEN 26 editor tests. Первый M4 остановлен через его единственный Playwright process; runner штатно удалил свой Docker-проект и восстановил исторические evidence (hash проверены). Полный M4 повторяется.

## Rulings

- Ruling: специализировать единый workflow на draft/navigation/commands factories, собранных `createEditorWorkflow`, вместо одного большого файла — согласованная декомпозиция, одна сборка и один completion-путь. Цена ошибочного разделения: лишние переходы между небольшими файлами, не новая модель состояния.
- Ruling: сохранить совместимые public actions owners как тонкие bound delegates, в том числе для существующих интеграционных потребителей; production UI переведён на workflow. Координатор использует отдельные локальные операции, обратных imports конкретных owners нет. Цена: временно шире публичный API до возможного отдельного удаления совместимости.
- Ruling: локальные операции конкретизированы по существующим переходам (`reserveSubmission`, `recordSubmission`, `acceptSuccessfulRecovery` и др.), вместо одного широкого `startSubmission/acceptRecoveryCompletion`. Смысловые гарантии дизайна и SaveStartResult workflow сохранены; совместимый store Save оставляет Promise<void>. Цена: больше небольших методов, без generic setters.
- Ruling: session сохраняет существующие I/O/read actions и зависимости auth/read/workOrders/recovery; чужие owners доступны через явно связанный контракт, общая очистка — только workflow. Полная развязка оставшейся SCC относится к F2/F4, не расширяется здесь.
- Ruling: guard ограничен AST известной границы owners, не является общим анализатором JavaScript. Проверяет принятые формы alias/mutation и runtime imports; any/reflection не даёт формальной гарантии. Цена: новые необычные формы доступа требуют расширения guard при ревью.
- Ruling: проверить runtime binding не только на обычном store, но и на devtools action Proxy — реальный M4 выявил дополнительную оболочку `this`; `$state` сохраняет идентичность. Цена: binding опирается на публичный стабильный Pinia state, а не на объект action receiver.

Durable memory отдельно не создаётся: контракт и причины сохранены в дизайне, этом ledger и Code_wiki.

## Итоговая приёмка после ревью

- Независимое ревью: Critical 0, Important 2. [Отчёт и исправления](2026-11-17-stage-2-f1-review.md). Revert после Save/чистого выбора теперь захватывает собственную command/context/draft identity. Guard узнаёт импортный alias storeToRefs, отдельный export и неизвестные imported helper escapes; проверенные readers имеют явные source+name contracts.
- `npm.cmd test -- --maxWorkers=2 --minWorkers=1`: **584 passed, 70 files**, exit 0 (`f1-full-acceptance.log`). Предыдущий повтор под параллельной Docker-нагрузкой дал один auth timeout и ошибку App fixture: mounted wrappers переживали resetModules. Добавлен auto-unmount; итоговый полный запуск выполнялся без Docker-нагрузки, таймауты не увеличивались.
- После полного набора добавлена проверка снятия RecoveryHost/Revert watcher и усилено утверждение о panel unmount. Профильный повтор: **5 passed**, exit 0 (`f1-lifecycle.log`). Production-код после полного запуска не менялся.
- `npm.cmd run lint`: exit 0, **Editor boundaries: 0 violations** (`f1-lint-acceptance.log`).
- `npx.cmd vue-tsc -p tsconfig.app.json --noEmit`: exit 0 (`f1-typecheck-acceptance.log`).
- `npm.cmd run build`: exit 0 (`f1-build-acceptance.log`). Сохраняется предупреждение Vite chunk >500 kB; разделение bundle вне F1.
- Граф `stage-2-import-graph.json`: 105 production files, 338 import edges, 235 value edges. Draft/commands/navigation исключены из общей SCC, размер 17→14. Оставшаяся SCC содержит auth/HTTP/read/session/recovery; её полное устранение относится к отдельным F2/F4/F6.
- Второй M4: 10 passed, 1 failed из-за двух устаревших динамических import paths в storage spec. Исправлены только пути к уже перенесённым IndexedDB adapter и recovery contract; протокол хранения не менялся. Итоговый повтор выполняется проектом `geoservice-m4-c1e176b9`.
- Ruling: существующие интеграционные navigation/recovery/map tests используются вместе с новыми pure workflow/owner/runtime/guard tests; матрица отказов не дублируется целиком во второй форме. Unknown/rejected/readback/storage/protocol/session/access покрываются реальным recovery pipeline, identity и порядок завершения — также чистыми управляемыми портами.
- Ruling: M4 wrapper сохраняет/восстанавливает исторические sprint evidence и дополнительные work-order screenshots, копируя новые результаты в `evidence/f1`. Исправление путей browser storage test — поддержка приёмки текущего layout, не изменение F4.
- Final: fixed Revert identity — `completes Revert after-save/clean-selection` RED→GREEN, итоговый suite 584/584.
- Final: fixed guard aliases/exports/helper escape — три fixtures RED→GREEN, итоговый suite 584/584.
- Final: Ruling: отложенная оценка ревьюером auth/HTTP и recovery I/O сохраняется вне F1: публичные границы проверены интеграционными tests, внутренние реализации не менялись. Цена при ошибке: оставшиеся связи потребуют отдельного F2/F4, гарантии полного устранения SCC не заявлены.
- Final: Ruling: результаты запущенных tests/M4 проверяет исполнитель после ревью; ревьюер их не подтверждал. Цена при ошибке: вывод о приёмке нельзя основывать только на статическом ревью, поэтому отчёт разделяет каждый запуск и его сбои.
- Final: minor (deferred): нет.
- Дополнительная проверка preview/current/readback и source/discard в `WorkspaceComparisonPanel.test.ts`: 1 passed. Сначала fixture без token корректно блокировал discard; исправлен auth context fixture, production не менялся.
- M4 `geoservice-m4-c1e176b9`: 10 passed, 1 failed на файловом `UNKNOWN: open comparison-768x1024.png`, а не на assertion приложения. До ошибки пройдены A/B/C, account isolation и отдельные consent; оставшаяся часть сравнения требует повтора. Весь этот test повторяется отдельно в `geoservice-m4-e3ff6924`, результаты остальных 10 tests не аннулируются.

## Завершение

- Повтор A/B/C в `geoservice-m4-e3ff6924`: **1 passed**, 52.1s, exit 0 (`f1-m4-context-repeat.log`). Пройдены все шесть viewport checks, screenshot capture и discard сравнения. Оба временных Docker-проекта удалены runner. Итого все **11 разных M4-сценариев** подтверждены на финальном production-коде; единого запуска 11/11 без файлового сбоя не заявляем.
- `evidence/f1/historical-evidence-restoration.json`: exitCode 0, все 15 исторических файлов восстановлены; SHA256 дополнительно сверены после завершения. `historical-evidence-restoration-full.json` сохраняет manifest общего запуска с exitCode 1 из-за screenshot. Изменений tracked sprint_2/старых full_refactoring screenshots нет.
- Новые screenshots и scenario JSON находятся в `evidence/f1/`. Screenshots 384×512 и 512×384 оказались побайтово равны историческим: они выполнены в успешном повторе, после восстановления скопированы в F1 из равных оригиналов. Runner дополнительно учитывает mtime, чтобы последующие повторы сохраняли и побайтово одинаковые новые снимки. Desktop 1440×900 и narrow 384×512 визуально просмотрены; viewport reflow не заявляется как browser zoom 200%.
- Дополнительные eslint и Prettier checks новых editor/scripts/UI-test файлов: exit 0. `git diff --check`: exit 0. Git add/commit/push не выполнялись; изменения оставлены unstaged. Временные diagnostic helper и дублирующий backup удалены, runner, design, plan, review, graph и evidence сохранены.
- Backend, auth/HTTP, recovery I/O, schema, retries и read-token reconciliation production-файлы не изменялись; отдельного backend-набора не запускали. Миграции/seeds использованы штатным M4 только внутри disposable Docker-проектов.
