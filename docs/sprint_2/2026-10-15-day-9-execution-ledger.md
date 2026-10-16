# Журнал исполнения — docs/sprint_2/2026-10-14-day-9-frontend-state-plan.md

Исполнение разрешено пользователем 2026-10-15. Режим inline, итоговое независимое review. Код оставляется unstaged.

## Решения исполнения

- Ruling: работа в существующем checkout `first-edit-save` — план разрешает подходящий checkout, здесь находятся согласованные untracked документы и готовые зависимости; новая копия не нужна. Цена ошибки: изменения остаются в общей рабочей ветке, без автоматического commit.
- Ruling: журнал хранится в docs/sprint_2, скрипты commit-based ledger не используются — пользователь запретил staging/commits и требует артефакты здесь; доказательства привязаны к командам/файлам, не к commit ranges.
- Pre-flight 1→2/3/4: contracts request/result используются draft/storage/orchestration; один модуль типов.
- Pre-flight 3→4/5: storage имеет явные ошибки, retry helper не владеет state; orchestration остаётся в workOrders.
- Pre-flight 4/5→6: auth reset должен останавливать runtime до очистки actor; guard отдельно от forced clearing.

## Выполнение

Задача 1 начата: contracts и API. Baseline frontend suite запущен перед изменением кода.

- Baseline: sandbox заблокировал esbuild (spawn EPERM); после разрешения тесты выполняются с escalation. Это не functional RED.
- Task 1: complete — RED отсутствующие guards/client; GREEN 6 tests, typecheck exit 0. Добавлены обязательные workspace поля в существующие fixtures.
- Task 2: complete — RED отсутствующие draft functions/actions; GREEN 3 tests. Current/candidate разделены, Cancel без HTTP.
- Task 3: complete — RED отсутствующие storage/retry helpers; GREEN 4 tests. Ошибки записи явные, чужой commandId нельзя затереть/удалить.
- Ruling: общий fixture размещён в src/test/workspaceEditFixture.ts — исключает дублирование contract fixtures между новыми suites; production не импортирует его.
- Task 4: complete — RED отсутствующий Save orchestration; GREEN 6 tests для Save/error policy. Success/readback/storage failure разделены.
- Task 5: complete — RED только один initial request и отсутствует restorePendingSave; GREEN точные 6/5/1 PUT, fake timers, historical receipt/current, no overlap.
- Task 6: complete — RED навигация стирала правку, auth/workspace access loss оставляли unknown без block; GREEN 83 tests targeted, затем 49 tests с immutable pending и workspace access fix.
- Полная frontend регрессия: 30 suites, 207 tests PASS. `npx vue-tsc -p tsconfig.app.json --noEmit` и lint PASS. Build прошёл TypeScript, Vite был остановлен sandbox spawn EPERM; запущен повтор с escalation.
- Ruling: дополнительно запущен vue-tsc с явным tsconfig.app.json — штатный typecheck не обнаружил app diagnostics; итоговый build также проверяет project references. Исправлены narrowing и одна fixture revision=7.
- Ruling: suspend helper учитывает неизвестного actor при initial 401, блокируя сохранённые recovery records без показа данных — иначе relogin превращался бы в автоматический retry. Это защитная граница, не UI восстановления доступа.
- Final review: три Important замечания, без Critical/Minor. Пять регрессионных cases сначала FAIL: storage failure через logout/reset/login, access failure из PUT/readback/list, повторный выбор вершины. Один проход исправлений: recovery suite 22 tests PASS.
- Ruling: приватная actor-scoped блокировка переживает reset store, даже если storage недоступен; цена — до отдельного явного recovery flow автоматическое продолжение остаётся запрещённым. Это не гарантия сохранения runtime после закрытия страницы.
- Ruling: единый access-loss transition скрывает данные workspace и останавливает retries; receipt остаётся в закрытом recovery context. Повторный выбор той же вершины идемпотентен, смена dirty target требует Cancel.
- Review вне scope: UI drag/Save/Revert/relogin, реальный browser/backend restart, координация вкладок и уничтоженное storage; backend не меняется. Эти ограничения сохранены в отчёте, не представлены как завершённая функциональность.
- Task 7 complete: итоговый `npm test` — 30 suites, 216 tests PASS; typecheck, явный app typecheck, lint, build PASS. Vite предупреждает о chunk >500 kB (JS 1208,27 kB, gzip 344,07 kB). Повторное review после fix pass не запускалось.
- Завершение по finishing-a-development-branch с приоритетом AGENTS.md: оставить существующий checkout и изменения unstaged; меню merge/push не применяется, Git операции пользователь выполняет самостоятельно.
