# День 13: End-to-end Интеграция

Дата: 2026-06-26
Статус: согласован для written spec
Расположение: `docs/release_1/sprint_1`

## Назначение

День 13 является облегченным интеграционным днем после реализации `Edit Workspace`.
Цель дня - добавить в CI проверку полного API/Compose пути:

```text
login -> assigned work order -> open/reopen edit version -> workspace
```

Новая пользовательская функциональность не добавляется. День 13 закрывает риск,
что backend endpoints, seed chain, auth, serialization и workspace aggregate
работают по отдельности, но не подтверждены как единый вертикальный сценарий в
стандартном Docker Compose окружении.

## Выбранный Подход

Используется легкий API/Compose smoke runner, вызываемый из существующего CI
`smoke_test`.

Сценарий остается легче браузерного E2E: он не добавляет Playwright, Cypress или
другой browser automation. Проверяется реальный HTTP path внутри поднятого
`utility_service`, поэтому smoke покрывает runtime wiring, auth, routes, response
serialization и demo seed.

Альтернативы были отклонены:

- inline Python прямо в `.github/workflows/ci.yml` слишком быстро раздувает YAML
  и усложняет локальный повтор;
- live HTTP pytest требует отдельного env-gate, чтобы обычный backend `pytest`
  не пытался обращаться к уже запущенному сервису.

Выбран отдельный маленький smoke-runner, потому что он переиспользуется локально
и в CI одной командой.

## Граница Scope

### Входит

- backend smoke-runner для живого HTTP сценария;
- запуск smoke-runner внутри существующего CI Docker Compose job;
- login seeded `Editor` через `POST /api/v1/auth/login`;
- чтение `GET /api/v1/work-orders/assigned-to-me`;
- поиск `WO-001` в списке назначенных work orders;
- открытие или повторное открытие `EditVersion` через
  `POST /api/v1/work-orders/{workOrderId}/edit-versions`;
- загрузка workspace через
  `GET /api/v1/work-orders/{workOrderId}/edit-versions/{editVersionId}/workspace`;
- проверки `workOrder.id`, `editVersion.id`, AOI id, 19 features и 9 associations;
- короткое обновление sprint README и verification notes.

### Не входит

- browser E2E;
- Playwright, Cypress, Selenium или новый frontend test runner;
- новые backend endpoints;
- изменения frontend поведения;
- изменение seed semantics;
- editing, validation, reconcile, review, post или audit workflow;
- performance benchmark.

## Архитектура

Добавляется backend script:

```text
apps/backend/tests/smoke/full_path_workspace_smoke.py
```

Скрипт является обычным Python entrypoint, а не pytest test module. Это важно:
обычный backend `pytest` остается быстрым и не требует live service. CI вызывает
smoke runner только после того, как Docker Compose поднял `postgis` и
`utility_service`, дождался healthcheck и выполнил базовые integration tests.

Параметры запуска читаются из environment:

| Переменная | Default |
|---|---|
| `GEOSERVICE_BASE_URL` | `http://127.0.0.1:8000` |
| `GEOSERVICE_EDITOR_EMAIL` | `alexey.editor@example.local` |
| `GEOSERVICE_EDITOR_PASSWORD` | `alexey-editor-password` |

Стабильные ожидаемые значения demo seed остаются внутри smoke runner:

- work order code: `WO-001`;
- work order id: `6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0401`;
- AOI id: `6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0100`;
- features count: `19`;
- associations count: `9`.

Эти значения уже являются частью seed contract и используются в существующих
integration/smoke проверках.

## Поток Данных

```text
POST /api/v1/auth/login
-> access_token
-> GET /api/v1/work-orders/assigned-to-me
-> выбрать WO-001 из response
-> POST /api/v1/work-orders/{workOrderId}/edit-versions
-> editVersion.id
-> GET /api/v1/work-orders/{workOrderId}/edit-versions/{editVersionId}/workspace
-> проверить workOrder, AOI, editVersion, features, associations
```

Smoke должен открывать `EditVersion` для `workOrderId`, найденного в списке
назначенных work orders. Это подтверждает связку `login -> assigned work order`,
а не только hardcoded workspace endpoint.

`POST /edit-versions` считается успешным в двух случаях:

- `201 created=true` на чистом seed;
- `200 created=false` при повторном запуске, когда open version уже существует.

## Обработка Ошибок

Smoke runner должен завершаться ненулевым кодом с диагностичным сообщением.

Ожидаемые категории отказа в сообщениях исключений:

- `Проверка входа не прошла`: login не вернул `access_token`;
- `Проверка назначенного наряда не прошла`: `WO-001` отсутствует в response;
- `Проверка EditVersion не прошла`: `POST /edit-versions` не вернул `editVersion.id`;
- `Агрегат workspace не совпадает`: response относится не к выбранному work order
  или не к открытому `EditVersion`;
- `Данные workspace не совпадают`: AOI id, count features или count associations
  не совпали с demo seed contract;
- HTTP-ошибка: выводятся status code и короткий response body.

Скрипт не должен скрывать ошибки retry/fallback логикой. Если runtime, seed или
contract повреждены, CI должен падать явно.

## CI Интеграция

В `.github/workflows/ci.yml` в job `smoke_test` добавляется отдельный step после
текущих backend integration checks и перед teardown:

```text
Full path workspace API smoke
```

Команда выполняется внутри контейнера `utility_service`, чтобы использовать тот
же Compose network и runtime dependencies, что и текущие smoke steps:

```powershell
docker compose -f docker-compose.yml exec -T utility_service \
  python tests/smoke/full_path_workspace_smoke.py
```

Существующие `Utility dataset authenticated API smoke` и `Workspace authenticated
API smoke` можно оставить или позже сократить отдельной implementation-задачей.
Дизайн Дня 13 не требует удалять старые проверки, потому что цель дня - добавить
полную связку через assigned work order list.

## Тестирование

### Smoke Runner Unit Shape

Если реализация выделит маленькие helper functions для HTTP request и assertions,
их можно покрыть unit tests без live server. Это полезно, но не обязательно для
облегченного дня, если script остается компактным и читаемым.

### CI Smoke

Главная проверка Дня 13 - успешный проход CI `smoke_test` в Docker Compose:

1. `utility_service` healthy;
2. demo users, utility dataset и work orders seeded startup script;
3. `Editor` входит по seeded credentials;
4. `WO-001` найден через assigned list;
5. `EditVersion` создана или переоткрыта idempotently;
6. workspace возвращает expected AOI, 19 features и 9 associations.

### Local Smoke

После локального запуска Compose тот же сценарий можно повторить:

```powershell
cd infra
docker compose --profile dev up --build
docker compose -f docker-compose.yml exec -T utility_service python tests/smoke/full_path_workspace_smoke.py
```

Если локальная среда не может запускать Docker Compose, это не блокирует design;
implementation report должен явно указать, что локальный Compose smoke не
выполнялся.

## Критерии Готовности

День 13 завершен, когда:

1. CI содержит full path smoke step.
2. Smoke runner проверяет путь через assigned work order list, а не только
   hardcoded workspace URL.
3. Повторный запуск сценария не падает из-за уже открытой `EditVersion`.
4. Ошибки smoke runner диагностичны и указывают на участок отказа.
5. Browser E2E остается вне scope и явно назван будущей отдельной задачей.
6. Sprint README ссылается на design Дня 13.

## Последствия Решения

- CI начинает проверять первый пользовательский участок Sprint 1 end-to-end на
  уровне API/Compose.
- Риск несовместимости auth, assigned work order list, edit version open и
  workspace response обнаруживается раньше, чем в ручной demo.
- Browser E2E tooling не добавляется преждевременно.
- День 14 может сосредоточиться на приемке, demo и исправлении блокеров, а не на
  первичном доказательстве backend vertical path.
