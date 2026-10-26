# План реализации INF-02: production HTTP и WebSocket

Дата: 2026-10-26.
Статус: выполнен 2026-10-26 по отдельному поручению пользователя; результаты и ограничения — в [отчёте](2026-10-26-inf-02-production-api-routing-implementation-report.md).
Основание: [спецификация, принятая 2026-10-26](2026-10-26-inf-02-production-api-routing-design.md), [анализ](2026-10-26-inf-02-production-api-routing-analysis.md).

## Цель и ограничения

Production frontend из чистой сборки использует origin страницы для HTTP API и WebSocket. nginx передаёт `/api/v1/...` внутреннему `utility_service:8000`. Локальная приёмка подтверждает auth, workspace, Save/readback/Revert и реальное WebSocket-соединение.

- HTTPS остаётся внешним условием; сайт в корне адреса.
- INF-03, новый CI gate, изменение auth/domain contracts и realtime для Save/Revert исключены.
- Dev fallback и явный `VITE_API_BASE_URL` сохраняются. Production API остаётся с `DEV_MODE=false`, Secure=true и без автоматических seeds/migrations.
- Legacy API включается только в отдельной фазе изолированной проверки.
- Изменения оставлять unstaged; не выполнять `git add`, `git commit`, `git push`.
- Сохранять чужие изменения. Документы и скрипты писать с LF, по-русски; идентификаторы не переводить.
- Выполнять последовательно в текущем чате; делегирование не требуется.

## 1. Единый адрес для HTTP и WebSocket

**Файлы:** новый `apps/frontend/src/api/baseUrl.ts` и тесты; существующие `src/api/http.ts`, `src/api/http.test.ts`, `src/composables/map/useLayerRealtime.ts`, `src/composables/map/useLayerRealtime.test.ts`.

- [x] Реализовать чистую функцию разрешения base URL с явными входами: configured URL, production flag, origin страницы. Отделить чтение browser/env от вычисления, чтобы HTTPS и произвольный порт проверялись без браузерного стенда.
- [x] Различать отсутствующее значение и пустую строку: отсутствующее в dev → прежний localhost:8000; отсутствующее в prod и пустое → origin страницы. Относительные значения разрешать через URL относительно origin.
- [x] Использовать одно разрешённое значение в Axios и при построении WebSocket URL; HTTP(S) преобразовывать в WS(S), сохраняя host/port и существующий endpoint. Удалить независимый WebSocket fallback к localhost.
- [x] Сохранить auth interceptors, timeout Axios, ticket workflow и reconnect logic.
- [x] Проверить production HTTP/HTTPS с нестандартным портом, dev fallback, явный dev URL, пустое и относительное значение. Проверить отсутствие двойного `/api/v1` и правильный ticket query parameter.
- [x] Запустить целевые Vitest tests, typecheck и lint. Проверки HTTPS URL не объявлять фактическим WSS handshake.

**Готовность:** HTTP и WebSocket согласованно используют выбранный адрес, текущие realtime/auth tests проходят.

## 2. nginx в production image

**Файлы:** новый `apps/frontend/nginx.conf`, существующий `apps/frontend/Dockerfile`.

- [x] Подключить собственную server configuration только к prod stage; сохранить dev stage.
- [x] Добавить `/api/v1/` proxy к `utility_service:8000` без удаления префикса и query string. Статика остаётся в `/usr/share/nginx/html`; API errors не уходят в SPA fallback.
- [x] Задать HTTP/1.1, Upgrade и условный Connection. Для API сохранить заголовки auth/cookie, body и backend status; не переписывать cookie attributes.
- [x] Явно исключить proxy cache и upstream retry изменяющих команд. Для WebSocket установить согласованный read timeout 300 секунд.
- [x] Настроить API access log без query string, cookie и Authorization; не сохранять ticket в диагностических артефактах.
- [x] Проверить `nginx -t` в окружении с разрешаемым именем upstream. Проверить, что ошибочный API URL не возвращает HTML/200.

**Готовность:** собранный prod image содержит нужную конфигурацию. Публичный API port не добавлен; `.dockerignore` не изменён.

## 3. Изолированный runner локальной приёмки

**Артефакты:** `docs/sprint_2/verify-inf-02.ps1` и вспомогательные файлы в `docs/sprint_2/inf-02/`. Использовать существующие зависимости Playwright из `infra/m4`; его dev Compose и привязанные к M4 helper-команды не запускать как production evidence.

- [x] Создать уникальный project `geoservice-inf02-<суффикс>`, журнал созданных ресурсов, ограниченные таймауты и `try/finally`. Перед cleanup проверять принадлежность контейнеров/сети/volumes этому project.
- [x] Сформировать временный чистый build context из текущих исходников, включая незакоммиченные изменения реализации. Исключить `.env*`, `node_modules`, `dist` и временные артефакты; исходные файлы не удалять. Записать хеши проверяемых исходников без секретов.
- [x] Использовать базовый Compose с изолированными overrides: уникальные container names, disposable DB, свободный loopback port frontend, синтетические credentials. Сохранить service name `utility_service` для реального nginx upstream. Проверить итоговую конфигурацию без вывода полного env.
- [x] Собрать оба target `prod`, проверить runtime DEV_MODE=false и Secure=true. Не публиковать порт API; не использовать demo override.
- [x] Выполнить миграции и подготовку fixtures отдельными одноразовыми командами. Существующие seeds применять только к проверочной БД; для WebSocket подготовить настоящий legacy layer. Не добавлять seeds в API startup.
- [x] Запускать browser smoke через `http://localhost:<port>`, с настоящими cookie из login. Не внедрять cookie вручную, не выключать browser security. Учитывать выбранный localhost origin во всех browser probes.
- [x] Exit 0 только при прохождении всех обязательных сценариев и cleanup. Ошибки запуска Docker, сборки или браузера не считать подтверждением исходного дефекта.

**Готовность:** runner запускается из любого cwd, не затрагивает рабочую БД и не подменяет проверяемый API уже работающим контейнером.

## 4. Полный пользовательский путь через production frontend

**Артефакты:** Playwright config/spec в `docs/sprint_2/inf-02/`; evidence в `docs/sprint_2/evidence/inf-02/`.

- [x] Открыть настоящий production bundle и войти тестовым Editor. Зафиксировать фактические origin запросов `/api/v1/`; не ограничиваться проверкой текста bundle.
- [x] Проверить получение cookie с Secure/HttpOnly/Path, reload и восстановление сессии, список нарядов и открытие workspace.
- [x] Через UI изменить разрешённую внутреннюю вершину fixture, сохранить, перезагрузить страницу и сравнить прочитанную геометрию с ожидаемой. Использовать существующие UI-селекторы и контрактные ожидания M4 как источник сценария, без жёсткой зависимости от M4 project/port.
- [x] Выполнить Revert с подтверждением; новым чтением подтвердить baseline. Отдельное read-only сравнение в disposable БД подтверждает неизменность authoritative baseline; оно не заменяет публичный readback.
- [x] Выполнить logout, проверить удаление cookie и отказ последующего refresh. Не ожидать немедленной инвалидизации уже выданного JWT, если такого контракта нет в auth.
- [x] Проверить отказ защищённого endpoint без авторизации и API 404 без HTML fallback. Сохранить статусы и безопасные assertions, не access tokens/cookies.

**Готовность:** полный согласованный сценарий выполнен из production JavaScript через единственный frontend port.

## 5. WebSocket и регрессия

- [x] При обычной конфигурации проверить отказ выдачи ticket из-за выключенного legacy API.
- [x] В отдельной фазе включить legacy API только в тестовом override. Если API пересоздаётся, перезапустить nginx для разрешения актуального upstream IP; не скрывать это действие в отчёте.
- [x] Авторизованным запросом через frontend origin получить ticket, открыть WebSocket через тот же origin и дождаться backend-сообщения `connected` с нужным layerId.
- [x] Удерживать соединение более 60 секунд с ограниченным общим ожиданием, подтвердить, что оно осталось открытым. Проверить отказы без ticket и с уже использованным ticket. Не требовать конкретного browser close code, если отказ происходит до upgrade; проверять отсутствие успешного соединения.
- [x] Проверить отсутствие query string ticket в сохраняемом access log/evidence. Тела ответов ticket/auth не сохранять.
- [x] Выполнить frontend format/lint/typecheck/tests/build; проверить demo URL regression. Полный повторный backend DB suite не требуется при неизменных backend/migrations; его необходимость пересмотреть только при новых изменениях или отказах.
- [x] Проверить runtime-конфигурацию, Docker build и `git diff --check`; проверить LF также у новых untracked файлов.

**Готовность:** positive/negative WebSocket evidence получено с реальным backend; default legacy policy сохранена.

## 6. Runbook и отчёт

- [x] Создать `2026-10-26-inf-02-production-api-routing-runbook.md`: prerequisites, команда runner, сборка, изоляция, таймауты, cleanup, диагностика без секретов.
- [x] Описать внешнее HTTPS/WSS, общий root origin, необходимость restart frontend при изменении upstream IP, ограничение чистой сборки до INF-03 и отличие localhost проверки от проверки TLS.
- [x] Создать implementation report с image IDs, версиями инструментов/браузера, хешами исходников, матрицей результатов и оставшимися ограничениями. Не отмечать непроведённые проверки как успешные.
- [x] Обновить README и статус INF-02 в инфраструктурном ревью только после фактической приёмки; сохранить остальные изменения пользователя.
- [x] Оценить наличие нового уникального технического знания для Code_wiki согласно AGENTS.md. Не запускать repository-change ingest лишь из-за завершения плана; agent memory не дублирует эту спецификацию и runbook.

## Критерий завершения

Все шесть этапов выполнены, обязательная матрица локальной приёмки прошла, ограничения отражены в runbook/отчёте. Рабочие данные не затронуты, CI и INF-03 не изменены. Принятие спецификации и подготовка этого плана сами по себе не означают реализации или закрытия INF-02.
