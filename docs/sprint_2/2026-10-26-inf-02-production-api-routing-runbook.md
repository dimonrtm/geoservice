# INF-02: локальная проверка production-маршрутов

## Назначение

Проверить текущие исходники frontend/backend в production images через один frontend port: авторизацию, восстановление сессии, workspace, Save/readback/Revert, logout, API errors и WebSocket. Основание — [принятая спецификация](2026-10-26-inf-02-production-api-routing-design.md).

## Запуск

Нужны Docker Desktop с Linux engine, Docker Compose v2, Node.js и PowerShell 7. В `infra/m4` должны быть установлены зависимости из package-lock и Chromium для Playwright. Подготовка, если они отсутствуют:

```powershell
cd C:\Repositories\geoservice\infra\m4
npm.cmd ci
npx.cmd playwright install chromium
```

Запуск из корня репозитория:

```powershell
pwsh -NoProfile -File docs/sprint_2/verify-inf-02.ps1
```

Сам скрипт можно вызвать абсолютным путём из любого cwd. Runner печатает идентификатор project и этапы; exit 0 означает прохождение обязательной матрицы и успешную очистку. Exit 1 требует прочитать `verification.json` конкретного запуска. Не трактовать успешную первую фазу при неудачной второй как закрытие INF-02.

## Что запускается

1. Создаётся `geoservice-inf02-<суффикс>` и временная копия текущих backend/frontend исходников, включая незакоммиченные изменения. Из копии исключены локальные env, dependencies, dist и кэши. В исходном checkout ничего не удаляется.
2. Базовый Compose разрешается с явным пустым env-файлом и синтетическими DB/JWT настройками. Проверяются production target, DEV_MODE=false, Secure=true и отсутствие API ports. Полученная конфигурация изолируется: отдельные container names, project network/volume, временные build contexts, loopback port frontend.
3. Собираются production images. В отдельной БД выполняются миграции, тестовые seeds и создание слоя для WebSocket. Seeds не добавляются в production startup.
4. Browser smoke работает через `http://localhost:<свободный порт>`. Временный браузерный профиль не использует пользовательские cookie/recovery. Браузер получает session cookie обычным login; ручного внедрения cookie нет.
5. Проверяется запрет legacy ticket по умолчанию. Затем только в этом test project включается legacy API, API пересоздаётся, nginx перезапускается, runner ждёт фактического ответа API. Проверяются connected, отказ повторного/отсутствующего ticket и соединение длительностью минимум 65 секунд.
6. Сохраняется результат; проверяются labels и удаляются только ресурсы этого test project. Подтверждается отсутствие его контейнеров, сетей и volumes. Временный каталог удаляется только после проверки абсолютного пути и ожидаемого имени. Собранные images и build cache остаются в Docker для ускорения повторного запуска.

На сборку выделено до 10 минут, на Compose-команды — до 3 минут, readiness Compose — до 90 секунд, восстановление маршрута после restart — до 30 секунд. WebSocket handshake/negative probes ограничены 10 секундами. Во время 65-секундной проверки соединения новых сообщений может не быть.

## Evidence и диагностика

Каждый запуск сохраняется отдельно в `docs/sprint_2/evidence/inf-02/geoservice-inf02-<суффикс>/`:

- `source-hashes.json` — SHA-256 файлов чистого build context;
- `verification.json` — итог, версии инструментов, production image IDs, runtime flags, результаты фаз, origin и cleanup;
- `saved-after-reload.png` — сохранённая геометрия после reload;
- `frontend.log` — после успешной WebSocket-фазы, проверен на отсутствие `ticket=`.

Список browser API requests содержит только method/origin/path. Cookie, Authorization, login response и ticket не сохраняются. Backend logs автоматически не выгружаются: Uvicorn может записывать ticket query string. При ручной диагностике не публиковать такие строки. Штатная API access log nginx не содержит query string; error log этого location ограничен уровнем `crit`, чтобы обычные upstream failures не сохраняли полный request URI с ticket.

Если cleanup завершился ошибкой, использовать project из manifest для read-only `docker compose`/`docker inspect` диагностики и проверять ownership перед удалением. Не запускать общий `down -v` для рабочей инфраструктуры. При принудительном завершении runner cleanup не гарантируется; project и временный каталог имеют собственный префикс.

## Контракт развёртывания

- Сайт расположен в корне одного origin. Production без API override использует этот origin; адрес WebSocket вычисляется согласованно. Для чистой сборки смена домена/порта не требует пересборки.
- nginx передаёт `/api/v1/...` в `utility_service:8000`, сохраняя путь, query, auth и cookie. Backend остаётся внутри Compose network.
- Внешняя инфраструктура обеспечивает HTTPS/WSS, поддержку Upgrade и передачу исходных API paths/cookies/Authorization. Прямой обычный HTTP-хост не заменяет это условие.
- Secure cookie сохраняется. Localhost имеет специальное браузерное поведение: успешный smoke не доказывает TLS/certificate configuration внешнего сервера. HTTPS→WSS вычисление проверяется unit tests; реальный WSS handshake этим runner не проверяется.
- nginx разрешает upstream при старте. После пересоздания API с новым IP нужно перезапустить frontend; runner делает это явно в legacy-фазе. Обычный restart процесса и пересоздание контейнера — разные случаи.
- Read timeout nginx — 300 секунд отсутствия upstream data; это не бессрочная гарантия соединения. Smoke доказывает фактическую работу свыше 60 секунд, а не все длительные network scenarios.
- Существующие dev target и `VITE_API_BASE_URL` сохранены. `.dockerignore` frontend не добавлен: INF-03 остаётся открытой. Произвольная локальная сборка с `.env` не получает гарантий чистого build context этого runner.
- CI не изменён. Runner не проверяет TLS, throughput, все браузеры, rolling deployment или повторно весь backend DB regression.
