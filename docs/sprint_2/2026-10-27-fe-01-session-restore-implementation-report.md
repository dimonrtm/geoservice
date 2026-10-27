# FE-01: отчёт об исправлении

Дата: 2026-10-27. Статус: исправлено в согласованных границах, локальные проверки выполнены. Изменения оставлены unstaged.

Основание: [принятое решение](2026-10-27-fe-01-session-restore-analysis.md), [план](2026-10-27-fe-01-session-restore-plan.md).

## Результат

После «Повторить» приложение удерживает экран восстановления до ответа или timeout. Форма входа и действия экрана ошибки недоступны. Позднее завершение старого restore после начала нового password login больше не меняет сессию, readiness и рабочий контекст.

`restoreGeneration` находится в экземпляре auth store. Новый login инвалидирует restore до первого await; success/catch/finally восстановления проверяют поколение. Существующий `sessionEpoch` сохраняет свою семантику. Новый вход того же пользователя защищён, включая замену токена без смены actor. При неуспешном новом login старый restore не возобновляется и экран ожидания не зависает.

Только запрос refresh помечается `authErrorHandling: "caller"`. Axios interceptor передаёт его отказ вызывающему action без предварительной очистки сессии. Обычные 401 и auth-related 403 по-прежнему обрабатываются с проверкой epoch. Backend logout из interceptor не вызывается.

## Проверки

| Проверка | Результат |
| --- | --- |
| Новые тесты до исправления | 17 ожидаемых отказов, 12 passed: UI терял ожидание, старый ответ менял новую сессию |
| Целевой набор App/auth/API | 67 passed, 7 файлов |
| Полный frontend suite | 368 passed, 47 файлов |
| Уточнённая проверка старого токена того же actor | 25 integration tests повторно passed после уточнения тестового payload; production-код не менялся |
| `npm run typecheck` | passed |
| `npm run lint` | passed |
| Prettier изменённых frontend-файлов | passed |
| `npm run build` | passed; предупреждение о размере JS chunk свыше 500 kB сохраняется |
| Браузер, production bundle с mock API | 4/4 passed: 200, 401, 503, настоящий клиентский timeout |
| Wiki lint | 37 `missing_frontmatter` в прежних RAW_inputs; изменённые ноды без новых замечаний |

Для Vitest/build понадобился разрешённый запуск вне sandbox из-за `spawn EPERM` esbuild. Первоначальный запуск команды `python` попал в WindowsApps alias; wiki lint выполнен bundled Python из Codex runtime.

### Покрытие гонки

Новый `src/api/auth.restore.integration.test.ts` использует настоящий Axios, interceptors, API-функции и store, подменяя транспорт adapter. Проверены поздние success/401/403/503/timeout, тот же и другой actor, ожидание запроса login и `suspendActor`, неуспешный login. Сравниваются состояние store и число побочных эффектов reset/suspend/hide после установки новой сессии.

Актуальные initial/runtime исходы проверяются отдельно, включая `USER_INACTIVE`. Обычный рабочий 401 текущего/старого epoch сохраняет прежнее поведение. Существующие auth-тесты продолжают проверять сохранение workspace-маркеров и их сброс при initial 401. Полный suite включает workOrders recovery/navigation/multicontext и workspace recovery.

Новый `src/App.restore.test.ts` использует реальный auth action с управляемым API: первое восстановление падает, retry остаётся незавершённым, затем проверяется каждый исход. Тест не ограничивается spy кнопки.

### Браузерное evidence и повторный запуск

Из корня репозитория, при установленных frontend и `infra/m4` зависимостях и Chromium для Playwright:

```powershell
npm --prefix apps/frontend run build
node docs/sprint_2/fe-01/smoke.mjs
```

Runner обслуживает `apps/frontend/dist` на свободном loopback-порту, создаёт изолированные browser contexts и закрывает browser/server в `finally`. API подменяется синтетическими ответами; рабочая БД не используется. Каждый проход делает два refresh и ноль login. Timeout проверен без уменьшения 30-секундной настройки: возврат retry за 30048 мс после проверки экрана ожидания.

- [Assertions](evidence/fe-01/verification.json).
- [Экран ожидания 1024×768](evidence/fe-01/retry-waiting.png), визуально проверен: форма и кнопки отсутствуют, текст не обрезан.
- [Runner](fe-01/smoke.mjs).

## Документация и ограничения

Через `source-command-ingest`, режим `repository-change`, обновлены существующая нода `Code_wiki/архитектура/frontend.md` и компактный реестр: зафиксированы владелец refresh-ошибки, поколение восстановления и его отличие от epoch. Это новое устойчивое техническое правило. Отдельная agent memory не нужна, live project state не переписывался ради истории задачи.

Исправление не является общим менеджером login/logout/restore и не закрывает AR-01. Браузерный smoke с mock API не проверяет серверную ротацию cookie. Generation guard не отменяет `Set-Cookie` уже полученного ответа. Согласованность cookie при произвольных принудительных пересечениях auth-запросов не заявляется. Изменений backend, миграций и CI нет; backend/DB suite не запускался.
