# GeoService

GeoService — экспериментальное веб-приложение для редактирования геометрии инженерной сети по нарядам. Редактор открывает назначенный участок на карте, вносит правку в рабочую версию и может вернуться к ней после повторного входа. Демо использует синтетические данные условной организации.

## Локальный запуск

Для демо достаточно Docker с Compose v2. Запустите сервисы из корня репозитория.

```sh
cd infra
docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml --profile dev up -d --build
```

При запуске backend применяет миграции Alembic, подготавливает сеть и наряд, затем проверяет геометрию линии `L-003`. Когда сервисы готовы, откройте [приложение](http://localhost:5173). На порту 8000 доступны [состояние API](http://localhost:8000/health) и [Swagger UI](http://localhost:8000/docs).

### Первая правка

1. Войдите как редактор, которому назначен наряд `WO-001` «Проверка участка фидера». Выберите наряд и нажмите **Начать** или **Продолжить**, если рабочая версия уже открывалась. [Данные для входа в демо](apps/backend/seeds/specs/seed_demo_user_specs.py)
2. Выберите на карте линию `L-003` и немного сдвиньте её среднюю вершину в пределах области работ. **Отменить** снимает несохранённую правку.
3. Нажмите **Сохранить**. При следующем открытии наряда карта покажет сохранённую геометрию рабочей версии. Чтобы вернуть исходную геометрию, выберите линию, нажмите **Сбросить** и подтвердите действие.

Если связь прервалась после отправки, приложение использует запись команды в IndexedDB, чтобы восстановить её результат. Сервер распознаёт повтор той же команды по идентификатору.

### Остановка и диагностика

Если API не запустился, посмотрите журнал из каталога `infra/`.

```sh
docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml --profile dev logs utility_service
```

Следующая команда останавливает демо и сохраняет данные до следующего запуска. Выполните её в том же каталоге.

```sh
docker compose --env-file demo.env -f docker-compose.yml -f docker-compose.demo.yml --profile dev down
```

При повторном запуске совместимая старая демо-БД получает трёхвершинную `L-003`. Если обновление линии небезопасно, оно откатывается и запуск API останавливается. Старый том, созданный до замены истории миграций, требует пересоздания. Если в журнале есть `password authentication failed`, проверьте, совпадает ли пароль в конфигурации с паролем, заданным при создании тома. Для одноразовой демо-БД, данные которой можно удалить, добавьте `-v` к команде `down` и повторите запуск. Это удалит и сохранённые правки.

## Код и конфигурация

| Часть проекта | Где искать |
| --- | --- |
| Backend на Python 3.12 и FastAPI | [Точка входа API](apps/backend/utility_service/web_api/main.py), [сценарии приложения](apps/backend/utility_service/use_cases/), [доменные правила](apps/backend/utility_service/domain_services/) |
| Хранение геометрии и миграции | [PostgreSQL/PostGIS, SQLAlchemy и Alembic](apps/backend/utility_service/infrastructure/postgresql/), [демо-данные](apps/backend/seeds/) |
| Frontend на Vue 3, TypeScript и Pinia | [Интерфейс](apps/frontend/src/App.vue), [сценарии редактора](apps/frontend/src/editor/), [карта MapLibre](apps/frontend/src/map/), [команды Vite и тестов](apps/frontend/package.json) |
| Инфраструктура | [Базовый Compose](infra/docker-compose.yml), [настройки демо](infra/docker-compose.demo.yml), [описание развёртывания](Code_wiki/deployment/docker_compose.md) |

Демо использует публичные настройки. Vite получает адрес API через `VITE_API_BASE_URL`. Войти через API можно запросом `POST /api/v1/auth/login` с полями `email` и `password`. Для проверки входа передайте полученный `access_token` в заголовке `Authorization: Bearer <access_token>` запроса `GET /api/v1/auth/me`. [Настройки демо](infra/demo.env)

Для базового Compose задайте собственные `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DATABASE_URL` и `JWT_SECRET`. Миграции в этой конфигурации выполняет отдельный сервис `migrate`. В профиле `prod` nginx отдаёт frontend и проксирует запросы `/api/v1/` на backend. Для cookie браузерной сессии включён флаг `Secure`. [Пример конфигурации](infra/.env.example)

Рабочее пространство использует API нарядов `/api/v1/work-orders`. Прежний API слоёв `/api/v1/layers` по умолчанию отключён. Параметр `UTILITY_GEOMETRY_XY_RESOLUTION` задаёт шаг координатной сетки для новых рабочих версий (по умолчанию `0.0000001`), а `UTILITY_GEOMETRY_ROUNDING_MODE` — правило округления `ROUND_HALF_AWAY_FROM_ZERO`. [Настройки backend](apps/backend/utility_service/utils/settings.py)

## Проверки

- **Backend.** Из корня репозитория соберите тестовый образ командой `docker build --target dev -t geoservice-backend-tests apps/backend`, затем выполните `docker run --rm geoservice-backend-tests python -m pytest` для проверок без PostGIS.
- **Интеграция с PostGIS.** В Windows из корня выполните `.\infra\db-tests.cmd`. Скрипт применяет миграции и запускает `tests/integration_tests` в отдельной БД `geo_test` в памяти, затем удаляет тестовые контейнеры. При ручном запуске с `RUN_DB_TESTS=1` нужен отдельный `TEST_DATABASE_URL` с именем БД на `_test`. [Тестовый Compose](infra/docker-compose.test.yml)
- **Frontend.** В каталоге `apps/frontend/` выполните `npm ci`, затем `npm test`, `npm run lint`, `npm run typecheck` и `npm run build`. Для локального запуска подходит Node.js 20.19.x.
- **Сквозной сценарий.** Браузерные проверки проходят сохранение и сброс через интерфейс, потерю ответа сервера и восстановление команды после перезапуска. [Запуск Playwright с отдельной БД](infra/m4/README.md)

## Документация

- [Указатель знаний проекта](index.md) связывает [предметную область](Wiki/index.md), [DDD-модель](DDD_Wiki/index.md) и [техническую документацию](Code_wiki/index.md).
- [Архитектура backend](Code_wiki/архитектура/backend.md) и [архитектура frontend](Code_wiki/архитектура/frontend.md) описывают устройство приложения.
- [План Release 1](docs/release_1/README.md), [материалы Sprint 1](docs/release_1/sprint_1/README.md) и [приёмка Sprint 2](docs/sprint_2/README.md) описывают развитие рабочего сценария. [Материалы Release 2](docs/release_2/README.md) содержат проекты будущих изменений.
- [Порядок работы с источниками и wiki](docs/knowledge-pipeline/README.md) описывает, как знания попадают в репозиторий. Правила для агентов собраны в [AGENTS.md](AGENTS.md).
