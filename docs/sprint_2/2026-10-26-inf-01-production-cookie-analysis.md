# INF-01: остановка production API из-за настройки session cookie

Дата: 2026-10-26.
Статус: анализ выполнен; границы результата уточнены. Пользователь выбрал вариант А (первый вариант) и принял спецификацию 2026-10-26. Реализация завершена; результаты — в [отчёте](2026-10-26-inf-01-production-cookie-implementation-report.md).

## Запрос и границы анализа

Разобрать INF-01 из [инфраструктурного ревью](infra-performance-review.md) на основе Sprint 2, текущего кода, Wiki и DDD_Wiki. Не предлагать решение до прояснения требований. Вопросы задавать последовательно, отдельными сообщениями. Артефакты сохранять в `docs/sprint_2`.

В этом этапе изменяется только данный документ. Существующие незакоммиченные материалы ревью и изменения README принадлежат исходному состоянию рабочего дерева. Код, Compose, тесты, wiki и рабочая БД не изменялись. Отдельная agent-memory запись не нужна: причины и контекст сохранены здесь.

## Что уже установлено

### Цепочка отказа

1. `infra/docker-compose.yml`, service `utility_service`, использует backend target `prod`, задаёт `DEV_MODE: "false"`, требует `DATABASE_URL` и `JWT_SECRET`.
2. В `environment` этого сервиса отсутствует `AUTH_SESSION_COOKIE_SECURE`. Service-level `env_file` также отсутствует.
3. `apps/backend/Dockerfile` копирует build context, но `apps/backend/.dockerignore` исключает `.env` и `.env.*`. Поэтому на локальный backend `.env` при чистой сборке опираться нельзя.
4. `apps/backend/scripts/start_api.sh` запускает `uvicorn utility_service.web_api.main:app`.
5. Импорт приложения приводит к загрузке `utility_service.utils.settings`; в конце этого модуля выполняется `settings = get_settings()`.
6. `Settings.auth_session_cookie_secure` имеет default `False`. Валидатор при `DEV_MODE=false` и валидном JWT secret выбрасывает `ValueError("AUTH_SESSION_COOKIE_SECURE должно быть true, если DEV_MODE=false")`.
7. Приложение не доходит до обслуживания HTTP. `/health` недоступен; `frontend-prod` зависит от `utility_service: service_healthy`.

Это рассогласование контракта конфигурации приложения и Compose. Защитный валидатор действует согласно существующему auth-контракту. Ошибка возникает до обращения пользователя к login и не зависит от данных `WorkOrder`.

Задать переменную только в shell или в CLI `--env-file` недостаточно, если Compose не использует её для формирования environment контейнера. Интерполяция Compose и environment сервиса — разные этапы. Подтверждение: [Docker: environment контейнера](https://docs.docker.com/compose/how-tos/environment-variables/set-environment-variables/), [Docker: приоритеты и примеры](https://docs.docker.com/compose/how-tos/environment-variables/envvars-precedence/).

### Воспроизведение причины

На текущих исходниках выполнены три отдельных Python-процесса с минимальным синтетическим окружением внутри одноразового контейнера `geoservice-day14-check:latest`:

| Входные условия | Код выхода дочернего процесса | Результат |
| --- | --- | --- |
| Валидные синтетические DB URL/JWT secret, `DEV_MODE=false`, Secure отсутствует | 1 | В stderr присутствует указанная ошибка обязательной Secure cookie |
| Те же условия, `AUTH_SESSION_COOKIE_SECURE=true` | 0 | Settings: `dev_auth_enabled=False`, `auth_session_cookie_secure=True` |
| Те же DB URL/JWT secret, `DEV_MODE=true`, Secure отсутствует | 0 | Settings: `dev_auth_enabled=True`, `auth_session_cookie_secure=False` |

Второй случай — диагностический контроль одной переменной, а не согласованное решение задачи.

Условия проверки: `--network none`, `--read-only`, `--tmpfs /tmp`, `PYTHONDONTWRITEBYTECODE=1`; только каталог `apps/backend/utility_service` смонтирован read-only в `/source/utility_service`, `PYTHONPATH=/source`, cwd `/tmp`. Дочерним процессам передано явно сформированное окружение без host env и локальных `.env`. Импортировался настоящий `utility_service.utils.settings`, не его копия. Секрет — синтетическая тестовая строка, БД недоступна и не используется.

Ограничение: это проверка импорта Settings, а не новая сборка prod image, полный Compose startup, HTTP smoke или браузерный HTTPS-тест. Зависимости взяты из существующего локального образа. Docker первоначально был недоступен в sandbox; проверка выполнена после разрешённого запуска вне sandbox.

## Связанные контракты и последствия

### Cookie и восстановление сессии

`apps/backend/utility_service/web_api/api/auth.py`:

- login и refresh устанавливают session cookie;
- `HttpOnly=True`, `Path=/api/v1/auth`, имя по умолчанию `geoservice_session`;
- `Secure` берётся из Settings, `SameSite` по умолчанию `lax`;
- logout очищает cookie с теми же Path/Secure/SameSite;
- `/auth/me` работает с Bearer token; Secure относится к session cookie, а не к самому JWT.

`apps/frontend/src/api/auth.ts` отправляет login/refresh/logout с `withCredentials: true`. Auth-контракт [Code_wiki](../../Code_wiki/архитектура/api_and_realtime.md) фиксирует access token только в памяти и восстановление через cookie refresh. Значит, успешный старт процесса сам по себе не доказывает работоспособное восстановление сессии.

Браузерный Secure cookie предполагает HTTPS; localhost имеет специальное исключение и потому не доказывает работоспособность обычного HTTP-хоста. См. [MDN: Set-Cookie / Secure](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie). Это внешний технический факт, не выбранная схема развёртывания GeoService.

В текущем base Compose опубликован frontend `8080:80`; TLS termination не описан. `CORS_ORIGINS` и `infra/.env.example` используют HTTP localhost. Backend запускается Uvicorn без TLS-параметров. Из этого нельзя заключить, что внешний HTTPS proxy запрещён или уже существует: такой контракт в изученных требованиях не задан.

### Demo/dev и наследование

`infra/docker-compose.demo.yml` переопределяет `DEV_MODE=true`, target `dev`, command на demo startup и открывает HTTP API/frontend. Собственной настройки Secure в нём нет. Значение `DEV_MODE=true` в Settings лишь снимает production-проверку, но не принудительно выставляет cookie Secure в false.

Следовательно, изменение базового environment потенциально затрагивает и объединённую demo-конфигурацию. Сохранение текущего HTTP demo — отдельный регрессионный аспект; конкретное изменение пока не выбрано.

### Старт, миграции и health

Принятый [дизайн разделения Compose](../superpowers/specs/2026-07-01-compose-dev-prod-security-design.md) требует отдельного explicit migration step и запрещает demo seed chain в production API startup. `start_api.sh` этому соответствует. INF-01 не даёт основания переносить миграции или seed в API startup.

`/health` в `utility_service/web_api/main.py` возвращает `{"ok": true}` без обращения к БД. Lifespan создаёт realtime connection manager и закрывает runtime resources при завершении. Поэтому доступный `/health` подтверждает ограниченный факт старта приложения, но не готовность схемы БД, корректный login или браузерное хранение cookie.

## Что задают материалы Sprint 2 и доменная модель

| Источник | Существенное требование | Значение для INF-01 |
| --- | --- | --- |
| [ТЗ Sprint 2](2026-07-31-sprint-2-technical-requirements.md), разделы 1–3 | Editor сохраняет геометрию, видит её после refresh и backend restart; целевое окружение — demo | Исправление инфраструктуры не должно ломать demo и восстановление доступа |
| [Дизайн разделения Compose](../superpowers/specs/2026-07-01-compose-dev-prod-security-design.md), цели и нецели | Безопасный baseline отделён от demo; полноценный production deployment/CD исключён | Термин production в находке не определяет автоматически объём нового HTTPS-развёртывания |
| [DDD: safety invariants](../../DDD_Wiki/invariants/release1_safety_invariants.md) | Workspace доступен только назначенному active Editor; Default не изменяется через workspace | Ослабление авторизации не следует из исправления старта |
| [Wiki: назначение редактора](../../Wiki/specifications/editor_assigned_to_work_order.md) | Active user, роль Editor, assignee WorkOrder | Наличие cookie не заменяет проверку актуальных прав |
| [DDD: Work Order context](../../DDD_Wiki/bounded_contexts/work_order.md) | Владение WorkOrder, AOI и EditVersion | Cookie/TLS относятся к технической инфраструктуре, не к новой доменной сущности |
| [Wiki: recovery policy](../../Wiki/policies/editor_recovery_policy.md) и [DDD: recovery states](../../DDD_Wiki/state_machines/editor_save_recovery.md) | Возвращённый доступ не отменяет текущих guards; продолжение намерения явно подтверждается; другой пользователь не получает локальные данные автоматически | Восстановленная auth-сессия не должна автоматически исполнять Save/Revert или менять owner/context |

В изученных узлах Wiki/DDD_Wiki не найден отдельный контракт сертификатов, публичных URL или TLS termination. Их нельзя вывести из бизнес-инвариантов. Доменное исследование с квотой внешних источников для этого технического разбора не требуется.

## Почему существующие проверки пропускают ошибку

- `test_compose_security_contract.py` проверяет required DB/JWT placeholders, DEV_MODE, target и startup command, но не передачу Secure cookie.
- `test_compose_startup_contract.py` проверяет содержимое скриптов и launcher contracts, а не реальный production startup.
- `test_settings.py` отдельно проверяет отказ при insecure production и разрешение Secure. Эти тесты не получают environment из Compose.
- `.github/workflows/ci.yml` выполняет base `compose config`, строит prod image, но API smoke запускает с demo override.
- Backend pytest в backend-only image не видит `infra`; repo-dependent contract tests могут быть skipped. Это отдельная находка INF-04, важная для достоверности будущей проверки INF-01.

Прошлое ревью зафиксировало 12 passing infra tests с полным checkout ([evidence](evidence/code-review/verification.md)); это исторический результат, не повторный прогон в данном анализе.

## Граница с соседними находками

- **INF-01:** несовместимый runtime environment и отказ API до HTTP startup.
- **INF-02:** публичный путь браузер → API; frontend fallback `http://localhost:8000`, отсутствие proxy config и публикации API в base Compose. Если результат INF-01 включает браузерную HTTPS-сессию, границы двух задач пересекаются.
- **INF-03:** загрязнение frontend Docker build локальными dependencies/env. Это не причина отказа Settings.
- **INF-04:** пропущенные infra tests в CI. Новая проверка INF-01 должна реально выполняться, однако полный объём INF-04 автоматически в задачу не включён.
- SameSite=None/CSRF, retention auth sessions, администрирование пользователей, полноценный CD и общий security audit не становятся согласованными требованиями INF-01 только из-за близости к auth.

## Уточнение требований

### Вопрос 1 — ожидаемый результат

Какой результат должен считаться завершением INF-01: безопасный старт API в базовом Compose или также рабочий вход и восстановление сессии из браузера через HTTPS?

Причина вопроса: находка рекомендует согласовать HTTPS termination, но прежний утверждённый дизайн исключает полноценный deployment, а browser/API routing выделен в INF-02. Это выбор границы результата, не просьба подобрать proxy или сертификат.

Ответ пользователя: «безопасный старт API в базовом Compose».

Согласованная граница: INF-01 устраняет отказ API при production-настройках базового Compose с сохранением существующей защитной валидации. Рабочий браузерный вход через HTTPS, TLS termination и маршрутизация frontend → API не входят в результат INF-01. Исправление INF-02 не является условием завершения этой задачи. Существующий HTTP demo и разделение API startup / migrations / seed остаются регрессионными ограничениями.

### Вопрос 2 — обязательность проверки в CI

Должен ли фактический безопасный старт API в базовом Compose автоматически проверяться в CI при каждом изменении, или для приёмки INF-01 достаточно воспроизводимой локальной проверки?

Причина вопроса: сейчас CI проверяет конфигурацию base Compose и сборку prod image, но запускает API только с demo override. Требование постоянного production startup gate явно не принято. Ответ определяет обязательную среду проверки и объём изменений CI, но не выбирает способ реализации.

Ответ пользователя: «достаточно воспроизводимой локальной проверки».

Согласованная граница: постоянный production startup gate в CI не требуется для завершения INF-01. INF-04 не включается в задачу. Локальная проверка должна быть воспроизводимой; существующие CI jobs не меняются ради нового gate.

## Итоговое понимание задачи

Существенные требования прояснены. Требуется исправить передачу production-настройки cookie так, чтобы базовый API запускался с `DEV_MODE=false` и безопасной cookie при валидных обязательных DB/JWT параметрах. Защитные проверки Settings сохраняются. Явный demo override продолжает поддерживать текущий HTTP demo. Production startup по-прежнему не запускает migrations и demo seeds.

Приёмка ограничена локальной воспроизводимой проверкой. Она должна различать корректность собранного Compose environment, реальный запуск API и доступность `/health`. Успешный Settings import из анализа не заменяет проверку startup. `/health` не доказывает доступность БД или браузерную auth-сессию. Проверки выполняются изолированно от существующей demo-БД, контейнеров и volumes; одно лишь имя Compose project не гарантирует изоляцию из-за фиксированных `container_name` в base YAML.

HTTPS termination, сертификаты, frontend routing, полноценный login/refresh через браузер, CD и исправление INF-02/03/04 не входят в согласованный результат. Утверждение об успешном старте не будет выдаваться за готовность полноценного production-развёртывания.

## Варианты решения после уточнения требований

После обсуждения пользователь выбрал первый вариант: А, явная политика в Compose. Вариант Б сохранён как рассмотренная альтернатива.

### А. Явная политика в Compose

В base `utility_service.environment` задать `AUTH_SESSION_COOKIE_SECURE: "true"`, а в явном demo override — `"false"`. Settings и его default оставить без изменения.

Преимущества: base Compose сам удовлетворяет своему обязательному контракту; оператору не нужна дополнительная переменная, которая в production всё равно допускает только true. Demo явно сохраняет свой HTTP-режим. Существующая валидация продолжает защищать запуск вне Compose и ошибочные overrides.

Цена: настройка фиксируется в соответствующих Compose слоях; shell-переменная сама по себе её не переопределяет. Для изменения поведения нужен явный override; небезопасный production override всё равно отклоняется Settings.

### Б. Дополнительный обязательный вход окружения

В base передавать Secure через required placeholder; в demo явно задавать false. Согласовать отдельное значение true для интерполяции base при demo merge: required placeholders могут проверяться до объединения файлов. Обновить инструкции и примеры окружения.

Преимущество: оператор явно подтверждает production-настройку через окружение, отсутствие значения обнаруживается при Compose config.

Цена: появляется дополнительный обязательный параметр без полезной вариативности в production; усложняется demo-запуск и его совместимость с базовым слоем. Правило интерполяции до merge описано в [Docker Compose reference](https://docs.docker.com/reference/compose-file/interpolation).

### Рекомендация

Вариант А соответствует согласованному узкому объёму. Изменение глобального default Settings затронуло бы запуск вне Compose и существующие dev-предположения; ослабление production-валидатора противоречило бы требованию безопасности. Поэтому эти направления не предлагаются как равнозначные альтернативы.

Подготовлена и принята [спецификация INF-01](2026-10-26-inf-01-production-cookie-design.md). Последующая реализация и проверки описаны в отдельном отчёте; диагностические результаты этого анализа сохраняются как исходное основание.
