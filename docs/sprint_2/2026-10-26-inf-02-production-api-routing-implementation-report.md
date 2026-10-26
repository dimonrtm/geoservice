# INF-02: отчёт реализации

Дата: 2026-10-26.
Статус: реализовано и проверено локально в согласованных границах.
Основание: [принятая спецификация](2026-10-26-inf-02-production-api-routing-design.md), [план](2026-10-26-inf-02-production-api-routing-plan.md).

## Результат

Production frontend без API override использует origin открытого сайта. HTTP client и WebSocket используют общее разрешение адреса. nginx production image обслуживает статику и передаёт `/api/v1/...` внутреннему `utility_service:8000`, сохраняя путь, query string, cookie, Authorization, body и backend status.

Добавлены HTTP/1.1 Upgrade, условный Connection, read timeout 300 секунд и API access log без query string. API cache/retry отключены; ошибки API не подменяются HTML. Изменения production-кода ограничены frontend URL resolver, HTTP/realtime clients, nginx configuration и его подключением в Dockerfile. Backend, миграции, base/demo Compose, CI и frontend `.dockerignore` не менялись.

## Проверки

| Проверка | Результат |
| --- | --- |
| Целевые frontend tests до дополнительной integration assertion | 17 passed |
| Полный frontend suite с двумя workers | **45 файлов, 334 теста passed**, 76,90 секунды |
| `npm.cmd run typecheck` | exit 0 |
| `npm.cmd run lint` | exit 0 |
| `npm.cmd run format:check` | exit 0 |
| Production build frontend/API из чистой копии текущих исходников | passed; frontend build выполняет `vue-tsc -b && vite build` |
| `nginx -t` внутри production frontend | passed |
| Runtime settings API | DEV_MODE=false, Secure=true, legacy flag=false по умолчанию |
| Настоящий production bundle в Chromium | Все наблюдавшиеся `/api/v1/` запросы отправлены на origin страницы |
| Login, cookie, session refresh после reload | passed; cookie Secure/HttpOnly, Path=/api/v1/auth, SameSite=Lax |
| WorkOrder/workspace, UI Save → reload/readback → Revert | passed; сохранённая геометрия прочитана после reload, после Revert совпала с baseline |
| Authoritative baseline | SQL digest до/после сценария совпал |
| Logout и refresh после него | cookie удалена, refresh вернул 401 |
| Защищённый API без авторизации / неизвестный API path | 401 / JSON 404, без HTML fallback |
| Ticket при выключенном legacy API | 403, `LEGACY_GIS_API_DISABLED` |
| WebSocket при явно включённом legacy API в test project | Получен `connected`; соединение оставалось открытым **65 004 мс** |
| Повторный ticket / отсутствие ticket | Соединения отклонены |
| Логи frontend | `ticket=` отсутствует; сохранён проверенный лог |
| Cleanup | passed; контейнеры, network и volume test project отсутствуют |
| Wiki lint | 37 известных `missing_frontmatter` в RAW_inputs, новых ошибок в Code_wiki нет; общий exit 1 |

Команды frontend выполнялись в `apps/frontend`. Полный suite: `npm.cmd run test -- --maxWorkers=2 --minWorkers=1`. Браузерный runner: `pwsh -NoProfile -File docs/sprint_2/verify-inf-02.ps1`. Начальный Vitest запуск был заблокирован sandbox (`spawn EPERM`), Docker также потребовал разрешения; необходимые проверки затем выполнены с разрешённым доступом.

## Воспроизводимое evidence

Успешный запуск: **geoservice-inf02-e06a7579**, 26 октября 2026, 22:18:49–22:21:34 Asia/Qyzylorda. Публичная проверочная точка — `http://localhost:50629`, только loopback frontend port. API port не публиковался.

- [Матрица результатов](evidence/inf-02/geoservice-inf02-e06a7579/verification.json).
- [Хеши чистого build context](evidence/inf-02/geoservice-inf02-e06a7579/source-hashes.json).
- [Состояние UI после reload](evidence/inf-02/geoservice-inf02-e06a7579/saved-after-reload.png). Скриншот вспомогательный: совпадение геометрии подтверждено assertions readback, а не внешним видом подложки карты.
- [Проверенный frontend log](evidence/inf-02/geoservice-inf02-e06a7579/frontend.log).

Окружение: Docker 28.1.1, Compose 2.35.1-desktop.1, Node.js v24.12.0, Chromium 156.0.8078.4 из существующего Playwright окружения `infra/m4`.

Образы успешного запуска:

- API: `sha256:eb1afd9312e5d0529eed5aa70fffc8b6a5ff02214182fbba68dbf51fbbbea1e0`.
- Frontend: `sha256:1b1891aef80266e965dfb2f0e8abba4173d0f8624357c56ce615ea23cfdffa89`.

Первый запуск `geoservice-inf02-a688f750` прошёл полный HTTP/browser workflow, но остановился с `ERR_CONNECTION_REFUSED` при открытии frontend сразу после restart nginx в WebSocket-фазе; cleanup прошёл. Runner исправлен: фиксированный свободный port на весь запуск и bounded readiness probe через API после restart. Точная причина различия порта/готовности в первом запуске отдельно не диагностировалась; это отказ проверочного orchestration, не доказательство нового дефекта API. [Первый результат](evidence/inf-02/geoservice-inf02-a688f750/verification.json) сохранён и не считается успешной приёмкой.

## Артефакты и ограничения

Runner и вспомогательные browser probes находятся в `docs/sprint_2/verify-inf-02.ps1` и `docs/sprint_2/inf-02/`. [Runbook](2026-10-26-inf-02-production-api-routing-runbook.md) описывает prerequisites, запуск, evidence, cleanup и внешние условия.

- HTTPS/WSS и сертификаты внешнего deployment не проверялись. HTTPS→WSS вычисление проверено unit tests; реальное соединение smoke использует WS на localhost. Secure cookie не отключалась, использовано специальное поведение браузера для localhost.
- INF-03 остаётся открытой: чистая временная копия изолирует проверку, но не исправляет загрязнение обычного Docker context.
- При пересоздании API с другим IP требуется restart frontend nginx; runner выполняет его явно. Rolling deployment и автоматическое обновление upstream DNS не заявляются.
- Длительная нагрузка и бесконечное idle connection не проверялись; read timeout 300 секунд сохранён. Обычный backend DB regression не повторялся, так как backend/migrations не изменены.
- CI не менялся; demo URL regression проверена frontend tests, новый полный dev stack не запускался.

Через `source-command-ingest repository-change` обновлена существующая нода `Code_wiki/deployment/docker_compose.md` и компактный реестр: сохранены новая маршрутизация и эксплуатационные границы, не журнал выполнения задач. Новая agent-memory запись не требуется: причины и ограничения сохранены в спецификации, runbook и Code_wiki.

Изменения оставлены unstaged для review пользователя. Git add/commit/push не выполнялись; исходные изменения материалов ревью сохранены.
