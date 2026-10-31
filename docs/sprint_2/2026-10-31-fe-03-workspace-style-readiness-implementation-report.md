# FE-03 — отчёт о реализации

Дата: 2026-10-31.

Основания: [дизайн](2026-10-31-fe-03-workspace-style-readiness-design.md), [план](2026-10-31-fe-03-workspace-style-readiness-plan.md), [журнал исполнения](2026-10-31-fe-03-execution-ledger.md).

## Изменение

Watcher MapView пишет workspace только после успешного запуска текущей карты. Первичный render по последним props по-прежнему выполняется перед ready=true. Обновления до готовности и после startup error не вызывают ранние записи слоёв. Правила fit и сообщения FE-02 сохранены.

useMapInstance подписывается на load до первого await. destroyMap отменяет запуск, снимает подписку до remove и завершает ожидающий createMap с null. Проверки после nextTick защищают и первый resize, и продолжение callback load; удалённый MapView игнорирует отменённый результат. Ошибка resize действующего запуска отклоняет createMap и не теряется как отдельный async rejection.

Изменены два production-файла, расширены компонентные тесты и добавлен тестовый файл composable. Backend, store, API и domain invariants не менялись.

## Проверки

- RED lifecycle: 5 из 6 тестов падали на исходном коде. После исправления — 6/6 GREEN. Дополнительно добавлены 2 проверки resize rejection.
- RED watcher: 3 из 20 тестов падали до исправления. После ограничения watcher — 20/20 GREEN.
- Связанный прогон пяти файлов до добавления двух error-path assertions: 70/70 passed.
- Typecheck и production build — exit 0. Build сначала выявил Array.at в новом тесте, несовместимый с текущим target; исправлено на slice(-1)[0]. Сохраняется прежнее предупреждение bundle >500 kB.
- Prettier четырёх изменённых frontend-файлов — passed.
- Независимое read-only ревью не обнаружило блокирующих замечаний; предложение проверить resize rejection учтено. Reviewer не смог независимо запустить Vitest из-за sandbox spawn EPERM; выполнение тестов подтверждено основным исполнителем разрешённым запуском вне sandbox.

Полный frontend suite после всех изменений: **53 файла, 467/467 passed**, 98.34s, exit 0; [лог](fe-03/frontend-tests.log). Ошибок необработанных Promise не зарегистрировано. `git diff --check` и проверка LF изменённых/новых текстовых файлов прошли.

## Браузерная проверка

[Скрипт](fe-03/smoke.mjs), запуск из корня: `node docs/sprint_2/fe-03/smoke.mjs`. Используются существующие Vite и Playwright, отдельный Edge context, настоящий MapLibre/WebGL и production MapView/useMapInstance. Тестовый Vite plugin заменяет только baseMapStyle на задерживаемый JSON URL; product-файлы не переписываются. Workspace синтетический, интерактивное редактирование не включено.

- Пока JSON стиля удерживается, две последовательные замены props не вызывают addSource/addLayer, fit или ready=true.
- После освобождения стиля source содержит последнюю геометрию, fit подтверждён только для latest key; карта отображается. [Снимок](fe-03/evidence/latest-workspace.png) визуально просмотрен.
- При unmount до освобождения стиля последующие workspace-записи и ready=true отсутствуют.
- В обоих сценариях нет pageerror и вызовов инструментированных методов карты после remove. [Результаты](fe-03/evidence/results.json).

Это проверка renderer, не сквозной тест настоящего backend/recovery. Точки удаления между microtasks отдельно детерминированно проверены unit tests; browser smoke не доказывает все возможные межсобытийные порядки. Timeout, обработка всех ошибок MapLibre, runtime WebGL failure и динамическая замена стиля не входят в исправление.

## Передача

Изменения оставлены unstaged в текущем checkout. Git add/commit/push не выполнялись. Предшествующие изменения README/общего ревью сохранены. Agent memory и repository-change ingest не нужны: причина и технический контракт сохранены в документах задачи.
