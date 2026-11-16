# Ход реализации этапа 1

План: docs/full_refactoring/2026-11-14-stage-1-plan.md. Дизайн принят; реализация разрешена пользователем 2026-11-15.

## Решения выполнения

- Работа последовательно в существующем checkout first-edit-save. Новый worktree не создаётся: сохраняем текущий checkout по правилам среды. AGENTS.md изменён пользователем до начала работы; не редактировать. Git add/commit/push запрещены.
- Ledger ведётся в этом документе вместо commit-based shell scripts skill: они не соответствуют запрету Git writes и требованию хранить артефакты в docs/full_refactoring.
- Pre-flight: F3/B3 независимы; F7-1 выдаёт типы/парсеры для F7-2/3, F7-2 — protocol presentation для F7-3. Несовпадений интерфейсов не найдено.

## Исходная точка

- Первый Vitest в sandbox: EPERM spawn esbuild (ограничение окружения). Повторяется с повышенными разрешениями.
- python из PATH — WindowsApps-заглушка; локальный pytest пока недоступен. Backend проверяется через Docker dev image.
- Docker socket недоступен в sandbox; проверенный elevated Docker доступен (28.1.1).

## Задачи

- F3: реализован; итоговые 28 профильных тестов прошли. RED: импорт pure presenter подтягивал editor; затем 27 PASS. При подготовке plain fixture восстановлен прямоугольный AOI исходного теста, алгоритм не менялся.
- B3: реализован. RED: нового типа ошибки нет. GREEN: полный backend pytest — 806 passed, 335 skipped (DB без флага); отдельный DB-прогон — 335 passed после изменения. Старые Save/replay/readback handlers сохранены.
- F7: реализован. RED parser/API/store/UI наблюдался; новый частично повреждённый список и Open работают через реальные parsers. Итоговый полный Vitest — 551 passed / 65 файлов. Браузерная проверка завершена.
- Независимое ревью: существенных production-дефектов не найдено; неблокирующее замечание к реактивному тесту устранено. Подробнее: [ревью](2026-11-15-stage-1-review.md).

## Проверки

- Baseline: frontend 93 passed; backend 69 passed; DB 335 passed.
- npm run build: PASS, Vite предупреждает о существующем размере bundle >500 kB. npm run lint: PASS.
- Ruling: npm run typecheck вызывает vue-tsc без обхода project references. Дополнительно выполнен `vue-tsc -p tsconfig.app.json --noEmit`, а build выполняет `vue-tsc -b`. Скрипт проекта вне задачи не менялся.
- Ruling: unit-тесты старой presentation сохранены также как тесты адаптера; добавлены независимые pure tests. Fixtures списка адаптированы helper-функцией вместо необязательных issues/rowKey в production.
- Ruling: узкие проверки WorkOrderOperationError объединены с transport/mapping-тестом; F7 API/List/store проверяются совместно в workOrders.contract.test.ts. Имена отдельных тест-файлов отличаются от плана, проверяемые границы сохранены.
- M4: полный `node run.mjs` — 11 passed; после выравнивания текста ошибок и уточнения скриншотов `node run.mjs work-order-contract.spec.ts` — 2 passed. Новые результаты сохранены в evidence/m4-current. Все 15 исходных файлов docs/sprint_2/evidence/s2-x01 восстановлены из предварительной копии и проверены по SHA256; исходная папка не имеет diff. Скриншоты новых сообщений проверены при ширине 1440 и 390.

## Итоговая приёмка — 2026-11-15

- Frontend: `npm.cmd test` — 551 passed, 65 файлов; `npm.cmd run lint`, `npm.cmd run build`, `vue-tsc -p tsconfig.app.json --noEmit` и Prettier по затронутым TS/Vue — PASS. Build также выполняет `vue-tsc -b`.
- Backend: полный pytest — 806 passed, 335 skipped без DB-флага; отдельный `./infra/db-tests.cmd` — 335 passed. Ruff и Black по 9 изменённым Python-файлам — PASS.
- Итоговые логи локальных прогонов: frontend-final.log, frontend-build-final.log, frontend-lint.log, m4-full.log, m4-contract-final.log в этой папке (игнорируются Git как *.log).
- Неблокирующие предупреждения: существующий размер Vite bundle >500 kB и deprecation crypt в passlib.
- `git diff --check` — PASS. Save/replay, миграции, receipts и границы транзакций не изменены. Пользовательские изменения AGENTS.md не редактировались.
- Все шаги планов завершены; изменения оставлены unstaged, git add/commit/push не выполнялись. Дополнительная durable memory не нужна: решения уже сохранены в дизайне и планах, результаты проверок — в этом отчёте.
