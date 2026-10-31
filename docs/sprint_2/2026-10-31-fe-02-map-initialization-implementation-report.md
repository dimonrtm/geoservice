# FE-02 — отчёт о реализации

Дата: 2026-10-31.

Основание: [принятый дизайн](2026-10-31-fe-02-map-initialization-design.md), [план](2026-10-31-fe-02-map-initialization-plan.md), [журнал исполнения](fe-02/execution-ledger.md).

## Результат

`MapView` показывает отдельный alert «Не удалось запустить карту» с инструкцией обновить страницу средствами браузера. Сообщение доступно в workspace, empty и legacy editing. Кнопок retry/reload нет. Legacy toolbar и вся панель `WorkspaceEditCommands`, включая recovery-действия, скрыты до успешной готовности карты.

Готовность принадлежит экземпляру карты и передаётся родителю через `readyChange`. Позднее завершение после unmount не включает команды и не продолжает настройку удалённого компонента. Первичная ошибка отрисовки workspace обрабатывается как ошибка запуска. Ошибка legacy-загрузки данных отделена от ошибки renderer. Скрытие не меняет draft, recovery record или исход Save.

Изменены два production-компонента и их два тестовых файла. Backend, Pinia state machine, API и composable lifecycle карты не менялись. FE-03, timeout/cancel ожидания load и сбои уже работающей карты остаются вне scope.

## Проверки

- Исходные целевые тесты: 25/25 passed.
- TDD: ошибка/готовность MapView — 11 RED до реализации; после реализации 15/15 GREEN. Дополнительный сценарий позднего reject уже проходил и сохранён как регрессия.
- TDD: панель workspace — 4 RED до реализации, затем объединённый прогон 40/40 GREEN.
- Полный frontend suite: финальный прогон после CSS-исправления — 52 файла, 454/454 passed (112.69s), exit 0. Лог: `fe-02/frontend-tests.log`.
- `npm.cmd run typecheck` — exit 0. `npm.cmd run build` — exit 0. Build сохраняет предупреждение о chunk >500 kB; оптимизация bundle вне FE-02.
- Prettier для четырёх изменённых frontend-файлов — passed.
- Независимый reviewer обнаружил переполнение карточки из-за content-box. Оно воспроизведено браузерным assertion и исправлено через border-box/min-width. Повтор браузерного сценария — passed. Других замечаний reviewer не выявил.

Sandbox первоначально блокировал дочерний esbuild (`spawn EPERM`); тесты/build выполнены разрешённым запуском вне sandbox. Build выявил несовместимый с target `Array.at` в новых assertions; заменён на `slice(-1)` без изменения требований.

## Браузерные evidence

Воспроизводимый скрипт: [smoke.mjs](fe-02/smoke.mjs), команда из корня `node docs/sprint_2/fe-02/smoke.mjs` после `npm.cmd run build` в `apps/frontend`. Используются существующий Playwright из `infra/m4` и Edge. Запускается отдельный browser context, production/global browser settings не изменяются.

Проверен реальный MapLibre: init script возвращает null для canvas WebGL context, затем ограничение отключается через тестовый sessionStorage marker и страница обновляется. API-ответы синтетические, OSM tile заменён локальным fixture. Это проверка браузерного frontend, не реального backend.

- [Ошибка на desktop](fe-02/evidence/startup-error-desktop.png): сообщение видно, команды отсутствуют, список нарядов доступен.
- [Ширина 390px](fe-02/evidence/startup-error-narrow.png): нет горизонтального переполнения карточки, текст читаем.
- [Reflow для 200%](fe-02/evidence/startup-error-zoom-200.png): CSS viewport 640×450 вместо 1280×900; после прокрутки сообщение читаемо. Это эквивалент уменьшенного viewport, не проверка изменения масштаба через меню браузера.
- [После обновления](fe-02/evidence/after-refresh.png): canvas и панель команд видны, Save без выбранной линии disabled. Неожиданных API mutations и pageerror нет.
- [Результаты](fe-02/evidence/results.json).

Все три режима отдельно проверены component tests; браузерный end-to-end сценарий выполнен для основного workspace. Реальный screen reader, ручной browser toolbar zoom и настоящий backend в этом smoke не проверялись. Снимки narrow/reflow визуально просмотрены.

## Передача

Работа выполнена в существующем checkout `first-edit-save`; файлы оставлены unstaged. Staging, commit и push не выполнялись. Новая agent memory и repository-change ingest не нужны: причина, выбранный контракт и проверки сохранены в документах этой задачи.
