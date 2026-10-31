# AR-01: выпуск и проверка сессии браузера

Дата документа: 2026-10-27. Фактическая проверка: 2026-10-28, Asia/Qyzylorda.
Контракт: [дизайн](2026-10-27-ar-01-browser-session-design.md).
Результаты: [отчёт](2026-10-27-ar-01-browser-session-implementation-report.md).

## Выпуск и миграция

Frontend, backend и миграция `e9f1a2b3c4d5` выпускаются совместно. Смешанный
rolling deployment старой и новой auth-версии не поддерживается: старый backend
не проверяет родительский sid и не понимает новый контракт logout/status.

1. Подготовить согласованные production images и резервную копию БД штатными
   средствами окружения. Сохранить бизнес-данные, geometry baseline и историю
   команд; не запускать demo reset/seed на рабочей БД.
2. Закрыть внешний доступ на время выпуска и остановить все старые API workers
   и WebSocket connections. Не оставлять старый backend доступным по другому URL.
3. На целевой БД выполнить `alembic upgrade head` из нового backend image.
   Миграция создаёт `user.browser_auth_sessions`, заполняет связи legacy rows
   отдельными отозванными родителями и завершает старые refresh credentials и
   tickets. Исторические timestamps сохраняются. Старые JWT без sid отвергаются
   новым decoder. Пользователям нужен однократный повторный login.
4. Запустить новый backend и опубликовать соответствующий frontend. Проверить
   `/health`, revision `e9f1a2b3c4d5`, production `DEV_MODE=false`, Secure cookie,
   общий HTTPS origin и отсутствие старых instances. Localhost используется
   только для изолированной локальной проверки.
5. Выполнить login, reload двух вкладок, logout и проверку соседнего независимого
   браузера. Только после этого открыть внешний доступ.

Downgrade также завершает credentials. Откат требует согласованного старого
frontend/backend и остановки всех workers. Старый код не проверяет sid: при
возврате к нему требуется смена `JWT_SECRET`, чтобы ранее выданные JWT не стали
снова действительны. Откат схемы сам по себе не восстанавливает прежние входы.

## Что меняется для пользователя

Вкладки одного origin/profile разделяют один вход. Web Locks сериализует
login/refresh/logout, access JWT остаётся в памяти каждой вкладки. Marker
`geoservice.auth.session.v1` содержит только version/revision/sessionId/state.
Отсутствие BroadcastChannel допускается; marker и независимый status остаются.
При отсутствии Web Locks не выполняется некоординированный refresh.

Logout отзывает конкретный sid, не user id. Другой profile/browser/device того
же пользователя продолжает работу. Logout не удаляет и не заменяет cookie:
недействительная HttpOnly cookie остаётся до login/expiry. Это ожидаемый исход,
а не незавершённый выход. Новый login выдаёт новый sid и credential.

При ошибке до начала logout HTTP вход и workspace сохраняются с сообщением
«Не удалось выйти, попробуйте ещё раз». После dispatch network/timeout означает
неопределённый исход: «Не удалось подтвердить выход» и status reconciliation
исходного sid. Клиент не угадывает commit по сетевой ошибке и автоматически не
повторяет logout. Поздний ответ старого sid не очищает новый вход.

Закрытие вкладки после server rotation с потерей ответа и поздний старый
`Set-Cookie` могут лишить браузер актуального refresh credential. В таком случае
допустим явный повторный login; нельзя принимать другой sid либо ослаблять
одноразовость refresh. Не вводить replay grace period.

## Status, нагрузка и realtime

Каждая активная сессия вкладки опрашивается с паузой до 1000 ms после окончания
предыдущей проверки; timeout status — 1500 ms. На вкладку допускается один HTTP
status и один заменяемый pending context. Hidden tabs опрашиваются с учётом
ограничений browser scheduler; после `pageshow`/visible resume нужен свежий
status до защищённого действия. Ответ, начатый до resume, свежесть не доказывает.

Для N работающих вкладок это до примерно N status requests/s без кеша положительного
результата; каждый запрос делает короткий DB read. Это расчёт верхнего порядка,
а не нагрузочное измерение. Наблюдать latency/errors/DB connections агрегатами,
не записывать bearer/cookie/body. SLA login UI ≤5 s относится к работающим
вкладкам; OS suspend и произвольное throttling не имеют такой гарантии.

После commit новые access/refresh/ticket проверки отозванного sid отвергаются.
Уже допущенная операция может завершиться. Активные WebSocket connections
закрывает manager текущего процесса, проверяющий sid при admission/send.
Немедленный active close гарантируется только в принятой single-worker границе;
межпроцессный fanout и AR-02 в этот выпуск не входят. Legacy GIS по умолчанию
выключен. Harness включает его только для проверки ticket после отзыва.

## Изолированный автоматический запуск

Нужны Docker Desktop, Node.js, установленные Chrome/Edge и зависимости
`infra/m4/node_modules` из существующего `infra/m4/package-lock.json`.
Firefox — Playwright build 157.0 revision1555, путь
`.tmp-tests/ar01-browsers/firefox-1555/firefox/firefox.exe`. Это patched Firefox,
не установленный stock binary; [документация Playwright](https://playwright.dev/docs/browsers#firefox)
описывает эту границу. Пользовательские browser profiles не используются.

```powershell
docker build --target prod -t geoservice-ar01-backend-prod apps/backend
node docs/sprint_2/ar-01/run.mjs chrome msedge firefox
```

Harness копирует чистый frontend context без `.env`/host dependencies, использует
отдельный уникальный Compose project, tmpfs PostGIS, loopback port и одноразовый
fixture user со случайным паролем. Существующий seed используется только для
синтетической геометрии/назначения в disposable БД, затем credential заменяется.
Demo volumes не подключаются. Production backend image задан явно; исходники
не подменяются debug endpoints. Config содержит ссылки на process environment;
случайные secrets не записываются в него и evidence.

Для уже подготовленного isolated origin поддерживается интерфейс:

```powershell
node docs/sprint_2/ar-01/smoke.mjs --browser chrome --origin http://localhost:PORT --output EVIDENCE_DIR
```

Credential и идентификатор fixture layer должны быть переданы запускающим
процессом в `AR01_EMAIL`, `AR01_PASSWORD`, `AR01_LAYER_ID`; Firefox path — через
`PLAYWRIGHT_BROWSERS_PATH`. Не сохранять эти значения в `.env`, shell history,
отчёты или logs. Полный `run.mjs` передаёт их напрямую в памяти.

Дополнительная проверка одного/нескольких cases использует `AR01_CASE` с
подстроками через запятую. `browser.json.scope` отличает её от полного прогона;
пустое совпадение не считается успехом. Пример безопасного фильтра:

```powershell
$env:AR01_CASE = 'real_history_resume'
node docs/sprint_2/ar-01/run.mjs chrome msedge firefox
Remove-Item Env:AR01_CASE
```

Runner сохраняет только browser versions, статусы/booleans, timing, безопасные
assertion coordinates и counts. Тела/headers/cookie/JWT/ticket/password/HAR/trace
и screenshot сетевых заголовков не сохраняются. Network proxy держит настоящие
ответы backend в памяти и меняет только задержку/доставку. `route.fetch` не
используется для потери refresh: shared APIRequestContext сам применяет cookie.
В конце проверяются project ownership и очистка containers/network/volumes;
удаляется только проверенный абсолютный temporary path с префиксом harness.

## Диагностика sid без secrets

Проверять связь sid только в памяти runner: equality `session_id` login/refresh,
claim sid JWT и ожидаемого marker. В отчёт писать `sameSid=true/false`, HTTP
status либо агрегат counts, а не JWT, cookie, ticket и не raw SQL rows.
Сохранёнными в памяти старыми credentials после успешного logout проверить
`/auth/me` → 401, refresh → 401 и неиспользованный ticket → rejected handshake;
для независимого sid того же пользователя `/auth/me` должен остаться 200.

DB race verification выполняется только в отдельной `_test` БД с
`RUN_DB_TESTS=1`, `TEST_DATABASE_URL` и PostGIS extension. `infra/db-tests.cmd`
создаёт/удаляет собственный tmpfs project; lane должен явно показать passed,
а не skipped. Скопированные credentials не печатать даже при failure.
