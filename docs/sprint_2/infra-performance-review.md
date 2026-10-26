# Ревью инфраструктуры, CI, миграций и производительности

Дата: 2026-10-26. Метод: read-only анализ текущих файлов; изменён только этот отчёт. Проверены Compose, Dockerfile, workflow, зависимости, цепочка Alembic, ключевые запросы и realtime. Секреты и содержимое локальных `.env` не читались. БД, контейнеры и destructive integration-тесты не запускались. Выводы ниже подтверждены конфигурацией и кодом; время выполнения и планы SQL не измерены.

## Подтверждённые находки

### INF-01 — P1: production Compose не может запустить API с обязательной безопасной cookie

**Статус: решена 2026-10-26.** Base Compose передаёт Secure=true, demo override — false; защитная валидация сохранена. Фактический startup API и `/health`, отказ при Secure=false и demo settings проверены локально; regression — 51 passed без skips. [Отчёт исправления](2026-10-26-inf-01-production-cookie-implementation-report.md), [runbook](2026-10-26-inf-01-production-cookie-runbook.md). HTTPS/browser routing и новый CI gate исключены из объёма по согласованию с пользователем; INF-02 остаётся открытой.

Ниже сохранено исходное описание находки до исправления. Ограничения метода во введении относятся к первоначальному ревью; последующие runtime-проверки описаны в отчёте исправления.

- Место: `infra/docker-compose.yml:41–51`; `apps/backend/utility_service/utils/settings.py:33–36,94–95`; `apps/backend/.dockerignore:17–18`.
- Сценарий: чистая сборка и запуск base Compose с валидными `DATABASE_URL`, `JWT_SECRET` и остальными обязательными переменными. Compose выставляет `DEV_MODE=false`, но не передаёт `AUTH_SESSION_COOKIE_SECURE`. Значение Settings по умолчанию — `False`, а валидатор запрещает его при `DEV_MODE=false`. Локальный `.env` не попадает в backend image. Даже установка переменной в shell или Compose env-file не передаст её в контейнер без соответствующей записи environment/env_file.
- Последствие: исключение при импорте Settings, API не становится healthy; зависимый frontend не стартует штатно.
- Рекомендация: явно передать `AUTH_SESSION_COOKIE_SECURE=true` в production-конфигурации, согласовать HTTPS termination и добавить проверку фактического старта production API с минимальным разрешённым набором env. Проверка `docker compose config` этого не обнаруживает.

### INF-02 — P1: production frontend не имеет рабочего маршрута к API

**Статус: решена 2026-10-26 в согласованных границах.** Production frontend использует origin страницы; nginx передаёт HTTP/WebSocket в API. Полный локальный browser Save/readback/Revert и WebSocket smoke, 334 frontend tests прошли. [Отчёт](2026-10-26-inf-02-production-api-routing-implementation-report.md), [runbook](2026-10-26-inf-02-production-api-routing-runbook.md). HTTPS остаётся внешним условием, INF-03 отдельной задачей, CI не менялся. Ниже — исходное описание находки.

- Место: `apps/frontend/src/api/http.ts:12–14`; `apps/frontend/Dockerfile:21–28`; `infra/docker-compose.yml:35–88`.
- Сценарий: чистый checkout без локальных `.env`, запуск `frontend-prod` после устранения INF-01. API URL собирается как `http://localhost:8000`; build args/ENV для его переопределения в Dockerfile отсутствуют. Base Compose публикует только frontend `8080:80`, API port наружу не опубликован. В образ копируется стандартный nginx без proxy configuration.
- Последствие: страница открывается, но login/API идут на порт 8000 компьютера посетителя и не достигают backend. Runtime environment статического nginx сам по себе уже собранный bundle не изменяет.
- Рекомендация: определить публичный маршрут API, предпочтительно same-origin reverse proxy с поддержкой WebSocket; явно задать build/runtime configuration frontend. Проверять production browser/API путь, а не только HTTP `/` nginx.

### INF-03 — P2: frontend Docker build включает локальные зависимости и env-файлы

- Место: `apps/frontend/Dockerfile:7–13`; отсутствует `apps/frontend/.dockerignore` и Dockerfile-specific ignore.
- Доказательство: Docker сначала выполняет `npm ci`, затем `COPY . .`. В текущем workspace существуют `apps/frontend/node_modules` и `.env.local`; проверены только факт наличия и имена, содержимое env не выводилось.
- Сценарий: разработчик запускает Docker build после локального `npm ci`, как в обычном Windows workspace. Дерево host dependencies копируется поверх результата Linux `npm ci`; `.env.local` также меняет Vite build environment.
- Последствие: сборка зависит от локального состояния, в контекст уходит тяжёлое дерево зависимостей; возможны несовместимые native modules/исполняемые файлы и незапланированный API endpoint. Локальные env попадают в build layers. Наличие секретов в этих файлах не утверждается.
- Рекомендация: добавить `.dockerignore` для `node_modules`, `dist`, локальных env и артефактов; передавать разрешённые frontend settings явно. Сравнить сборку чистого checkout и checkout с установленными Windows dependencies.

### INF-04 — P2: CI пропускает существующие infra contract tests

- Место: `.github/workflows/ci.yml:62–70`; `apps/backend/Dockerfile:20`; `apps/backend/tests/test_compose_security_contract.py:5–19`; `apps/backend/tests/test_compose_startup_contract.py:7–20`.
- Сценарий: стандартный backend CI строит image с context `./apps/backend` и запускает `pytest` только внутри него. Файлов `infra` там нет, поэтому `find_repo_root` возвращает None, весь security-contract модуль и repo-dependent startup проверки получают skip.
- Последствие: зелёный backend CI не подтверждает contract tests для Compose и Windows launchers. Отдельные shell guards в smoke проверяют часть Compose, но не выполняют эти тесты и не стартуют production mode: `.github/workflows/ci.yml:96–127`.
- Рекомендация: запускать infra tests отдельно с доступом к checkout либо монтировать требуемые файлы read-only в runner. Контролировать отсутствие неожиданных skips в этом отдельном наборе.

## Риски, требующие измерений или отдельного решения

Это не доказанные нарушения SLA и не подтверждённые CVE.

- **Производительность workspace.** `apps/backend/utility_service/infrastructure/postgresql/sql/workspace_aggregate.sql:32–98` материализует видимые features, делает full outer join baseline/current и сериализует обе EWKB геометрии для всех пар, затем повторно сериализует видимую геометрию. Это даёт несколько представлений данных в одном ответе БД. Коррелированный `EXISTS` на материализованном наборе (`69–72`) требует проверки плана; утверждать квадратичную сложность без EXPLAIN нельзя. Проверить `EXPLAIN (ANALYZE, BUFFERS)` и RSS на disposable dataset нескольких размеров, включая сложные линии и маленькую AOI относительно версии. Зафиксировать бюджет response size и latency.
- **Неограниченная выдача поручений.** `apps/backend/utility_service/infrastructure/postgresql/repositories/work_order_repository.py:72–78` возвращает все записи пользователя без pagination/status фильтра. На текущем маленьком demo наборе это допустимо; для длительной эксплуатации нужны измерения количества записей, размера ответа и политика архивирования/пагинации.
- **Накопление auth state.** `apps/backend/utility_service/infrastructure/postgresql/repositories/auth_session_repository.py:16–34,81–104` создаёт записи и помечает ротацию, а `websocket_ticket_repository.py:16–35,37–59` создаёт и помечает использованные tickets. В этих repositories удаления нет; отдельный production retention job в просмотренной инфраструктуре не найден. TTL запрещает использование, но сам строки не удаляет. Определить retention и пакетную очистку с учётом аудита; измерить рост. Legacy WebSocket API выключен по умолчанию, поэтому ticket риск условен.
- **Realtime backpressure и масштабирование.** `apps/backend/utility_service/use_cases/services/realtime_connection_manager.py:17–19,36–50` хранит соединения в памяти одного процесса и последовательно await-ит `send_json` без собственного timeout. Медленный клиент может задерживать других; увеличение числа workers потребует доставки между процессами. Текущий `apps/backend/scripts/start_api.sh:3` запускает один worker, поэтому межпроцессная потеря сейчас не заявляется. Проверять в отдельном стенде с медленным потребителем; предусмотреть bounded queue/timeout и broker только при реальной необходимости масштабирования.
- **Воспроизводимость backend dependencies.** `apps/backend/requirements.txt` фиксирует прямые версии, но полного lock с hashes нет; `apps/backend/Dockerfile:8,19` дополнительно устанавливает unpinned pip/pytest. Docker base tags и actions major tags также изменяемы. Это риск изменения результата повторной сборки, не утверждение об уязвимостях. Ввести воспроизводимый dependency manifest и процесс обновлений; CVE оценивать отдельным сканированием и первичными advisories.
- **Миграционные блокировки.** `apps/backend/utility_service/infrastructure/postgresql/alembic/versions/c8e3f0a5b7d9_edit_version_geometry_policy.py:80–101` выполняет backfill всех edit_versions и последующий NOT NULL; migration-local validation и неизменяемый snapshot policy полезны. На крупной БД требуются репетиция, lock budget и резервное копирование. Это не основание требовать online migration для текущего demo масштаба.

## Проверки и ограничения

- По declarations просмотрена последовательная цепочка 14 migration revisions: корень `431fdb240d56`, head `c8e3f0a5b7d9`; свежий upgrade/downgrade фактически не выполнялся. Старые demo volumes явно не поддерживаются checkpoint migration `f2b3c4d5e6a7`; это принятая граница, не находка.
- Полезные меры уже существуют: отделённый migration service, backend `.dockerignore`, production Settings fail-closed, изолированный disposable DB-test Compose, CI smoke сохранения после рестарта, геометрические/командные constraints и транзакционные guards.
- Запуск `python` для вспомогательного статического анализа в этом shell не дал исполняемого Python runtime; выводы не опираются на якобы выполненный Python тест. Сверка выполнена чтением файлов и `rg`/PowerShell.
- Проверка dependency CVE и внешних advisories не проводилась, безопасность версий не подтверждается и не опровергается. Нагрузочных тестов, production deployment и database migrations не запускалось.
- Отдельная запись agent-memory не нужна: находки и причины уже сохранены в этом отчёте, дублирование не добавит устойчивого контекста.
