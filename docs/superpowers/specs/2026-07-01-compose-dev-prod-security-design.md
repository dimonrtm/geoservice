# Разделение Demo/Dev Compose И Production-Safe Defaults Для DEV_MODE/JWT_SECRET

Дата: 2026-07-01
Статус: design approved
Источник: backlog исправлений по Sprint 1 deep code review

## Контекст

В текущем состоянии `infra/docker-compose.yml` смешивает production-like runtime и
локальный demo/dev сценарий. Базовый compose по умолчанию включает
`DEV_MODE=true`, задает `JWT_SECRET=CHANGE_ME_IN_ENV`, собирает backend через
`target: dev` и запускает `bash scripts/start_utility_service.sh`, который
выполняет migrations и demo seed chain перед стартом API.

Backend уже содержит второй рубеж защиты: `Settings` запрещает пустой или
placeholder `JWT_SECRET`, когда `DEV_MODE=false`. Но из-за дефолтов compose
обычный запуск остается demo/dev запуском и не проверяет production-safe
границу. После появления обычной login modal и runner `seed_demo_users`, который
создает demo users для `/api/v1/auth/login`, endpoint
`POST /api/v1/auth/dev-login` больше не нужен.

## Цели

- Сделать `infra/docker-compose.yml` безопасным baseline, который не запускается
  с dev auth или placeholder secret по умолчанию.
- Вынести удобный локальный demo/dev запуск в явный compose слой.
- Удалить `POST /api/v1/auth/dev-login` и связанный backend code path.
- Сохранить воспроизводимый demo login через `POST /api/v1/auth/login` и
  сидированных пользователей.
- Зафиксировать regression tests, которые не позволят вернуть
  `DEV_MODE=true` и `CHANGE_ME_IN_ENV` в production-safe путь.

## Не Цели

- Не вводить полноценный production deployment или CD workflow.
- Не менять модель пользователей, роли `editor`/`reviewer` или demo credentials.
- Не решать отдельные JWT risks из review backlog: storage strategy,
  WebSocket query string token и short-lived tickets остаются отдельными P1.
- Не добавлять новый флаг `ALLOW_DEV_LOGIN`; устаревший dev-login удаляется.

## Выбранный Подход

Выбран вариант: `docker-compose.yml` становится production-safe baseline, а
demo/dev поведение включается только явным дополнительным compose файлом.

Committed YAML не хранит реальные секреты. В production-safe compose
используются required env placeholders:

```yaml
JWT_SECRET: ${JWT_SECRET:?JWT_SECRET is required}
```

Аналогичное правило применяется к runtime DB переменным:
`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DATABASE_URL`. Значения передаются через
локальный `.env`, shell environment или CI secrets. `infra/.env` остается
untracked; в git хранится только пример.

## Компоненты

### `infra/docker-compose.yml`

Базовый compose должен:

- собирать `utility_service` через backend Dockerfile `target: prod`;
- задавать `DEV_MODE=false`;
- требовать `JWT_SECRET`, `DATABASE_URL`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
  через `${VAR:?message}`;
- не содержать `JWT_SECRET=CHANGE_ME_IN_ENV`;
- не содержать `DEV_MODE=true`;
- запускать `utility_service` без demo seed chain.

Production-safe command для `utility_service` должен стартовать API после того,
как отдельный migration path уже применил migrations. Если в базовом compose
нужно оставить helper service `migrate`, он тоже использует required
`DATABASE_URL`.

### `infra/docker-compose.demo.yml`

Явный demo слой должен:

- переопределять `utility_service.build.target` на `dev`;
- задавать локальный demo `JWT_SECRET`, допустимый только в этом файле;
- включать `DEV_MODE=true`, если этот флаг сохраняется как общий local/dev
  marker;
- открывать ports для `postgis`, `utility_service`, `frontend-dev`;
- запускать текущий demo startup script
  `bash scripts/start_utility_service.sh`;
- включать `frontend-dev` и сохранять demo profile workflow.

Каноническая demo команда:

```powershell
cd infra
docker compose -f docker-compose.yml -f docker-compose.demo.yml --profile dev up --build
```

### Backend Auth

`POST /api/v1/auth/dev-login` удаляется полностью:

- route в `utility_service/web_api/api/auth.py`;
- schema `DevLoginIn`;
- `AuthService.get_dev_user()`;
- тестовые ожидания, связанные с созданием пользователя без пароля.

Единственный поддерживаемый пользовательский login path:
`POST /api/v1/auth/login`. Demo users создаются через `seed_demo_users` и имеют
обычные password hashes.

`DEV_MODE` после удаления dev-login не должен означать "создать пользователя
без пароля". Он может остаться только как локальный режим конфигурации, если
его все еще используют settings/tests.

## Startup И Data Flow

Production-safe flow:

1. Оператор или CI передает required env values.
2. `docker compose -f docker-compose.yml config` падает рано, если обязательные
   значения отсутствуют.
3. `migrate` применяет migrations как отдельный explicit step.
4. `utility_service` стартует API без demo seed chain.
5. Backend settings повторно валидируют `JWT_SECRET` при `DEV_MODE=false`.

Demo/dev flow:

1. Разработчик запускает compose с `docker-compose.demo.yml`.
2. Demo слой задает локальные безопасные только-для-demo defaults.
3. `start_utility_service.sh` выполняет migrations, `seed_demo_users`,
   `seed_utility_dataset`, `seed_work_orders`.
4. Пользователь входит через `/api/v1/auth/login` с demo credentials.
5. Frontend-dev работает против `http://localhost:8000`.

## Ошибки И Защита

- Если production-safe compose запускают без `JWT_SECRET` или DB env,
  ошибка должна возникнуть на этапе compose config/up.
- Если приложение запускают вне Docker с `DEV_MODE=false` и пустым или
  placeholder `JWT_SECRET`, `Settings` должен продолжать падать.
- Если клиент вызывает `/api/v1/auth/dev-login`, endpoint отсутствует. Не нужен
  отдельный "disabled" response, потому что route больше не является частью API.
- Demo defaults допустимы только в явно названном demo compose файле.

## Тестирование

### Unit И Contract Tests

- `utility_service/utils/tests/test_settings.py`:
  - `DEV_MODE=false` отклоняет пустой и `CHANGE_ME_IN_ENV` secret;
  - `DEV_MODE=true` не открывает dev-login и не нужен для passwordless auth.
- Auth tests:
  - `POST /api/v1/auth/login` продолжает работать через `AuthService.authenticate_user`;
  - `AuthService` не содержит метода создания dev user без password hash;
  - route `/api/v1/auth/dev-login` не регистрируется.
- Compose contract tests:
  - `infra/docker-compose.yml` содержит required env placeholders для
    `JWT_SECRET`, `DATABASE_URL`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`;
  - базовый compose не содержит `CHANGE_ME_IN_ENV` и `DEV_MODE=true`;
  - `utility_service` в базовом compose использует `target: prod`;
  - demo compose явно содержит demo defaults и seed startup command.

### CI

Текущий authenticated API smoke должен запускаться через demo compose, потому
что он проверяет demo seed chain и вход по demo users. Отдельно стоит добавить
быстрые compose config checks:

- negative check: production-safe compose без required env падает;
- positive check: production-safe compose с test-only env проходит config;
- demo config проходит через `docker compose -f docker-compose.yml -f
  docker-compose.demo.yml --profile dev config --quiet`.

## Документация

Нужно обновить:

- `README.md`: разделить quick start demo и production-safe baseline.
- `Code_wiki/dev_setup/local_development.md`: указать новую demo команду.
- `Code_wiki/deployment/docker_compose.md`: описать baseline/demo split.
- `Code_wiki/архитектура/backend.md` и `Code_wiki/архитектура/api_and_realtime.md`:
  убрать утверждения, что `/api/v1/auth/dev-login` доступен при `DEV_MODE=true`.
- `infra/.env.example`: показать пример без реальных секретов и с явным
  предупреждением для production.
- `infra/dev-up.cmd` и `infra/ci-up.cmd`: использовать demo compose, если они
  остаются local/demo helpers.

## Последствия

Плюсы:

- случайный запуск базового compose больше не поднимает dev auth с placeholder
  JWT secret;
- demo остается быстрым и воспроизводимым, но называется явно;
- login surface упрощается до одного пользовательского endpoint;
- CI можно разделить на demo smoke и production-safe config guards.

Компромиссы:

- локальная команда запуска становится длиннее;
- часть старой документации и scripts нужно обновить одновременно;
- production-safe compose без env теперь намеренно падает, что может удивить
  тех, кто привык к `docker compose up` без `.env`.

## Критерии Готовности

- `docker compose -f infra/docker-compose.yml config` без required env падает.
- Production-safe config с test-only env проходит.
- Demo config проходит и сохраняет seed startup.
- Backend tests проходят без `dev-login`.
- Frontend login продолжает работать через `/api/v1/auth/login`.
- README и Code_wiki больше не описывают `dev-login` как доступный workflow.
