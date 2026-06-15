# Спринт 1, День 4: Utility Dataset И Read-Only Backend API

Дата: 2026-06-15
Статус: согласован пользователем
Расположение: `docs/sprint_1`

## Назначение

Интенсив 4 создает базовый `synthetic_utility_feeder_01` и делает весь
агрегат demo-сети доступным через read-only backend API.

Результат дня:

- воспроизводимый create-once seed для одного AOI и одного feeder;
- полный базовый набор `NetworkFeature` и `NetworkAssociation`;
- агрегированный HTTP endpoint для чтения feeder;
- доступ к endpoint только для активного пользователя с ролью `Editor`;
- PostgreSQL/PostGIS integration tests для seed и пространственного поиска
  AOI.

Дизайн опирается на модели `AOI`, `Feeder`, `NetworkFeature` и
`NetworkAssociation`, реализованные в День 3.

## Выбранный Подход

Используется create-once seed и один агрегированный read-only endpoint.

При старте backend:

1. выполняются Alembic migrations;
2. создаются или восстанавливаются demo users существующим user seed;
3. запускается utility dataset seed;
4. запускается FastAPI application.

Utility seed проверяет наличие feeder с кодом
`synthetic_utility_feeder_01`.

- Если feeder отсутствует, весь dataset создается одной транзакцией.
- Если feeder существует, seed не изменяет и не удаляет его AOI, features
  или associations.
- Ошибка при создании нового dataset откатывает всю транзакцию.

Обычный restart сохраняет существующие данные. Полное восстановление
эталонного dataset относится к будущей явной reset-команде и не входит в
Интенсив 4.

## Граница Scope

### Входит

- пакет `seeds` для всей seed-логики приложения;
- перенос существующего demo user seed в `seeds`;
- `SeedUtilityDatasetService`;
- автоматический запуск utility seed при старте backend;
- repository для чтения всего feeder aggregate одним SQL query;
- service для авторизации, проверки целостности и формирования ответа;
- пакет `schemas.utility_network` с отдельным файлом для каждого DTO
  агрегированного GeoJSON-ответа;
- `GET /api/v1/utility-network/feeders/{feederId}`;
- unit tests и PostgreSQL/PostGIS integration tests;
- русскоязычные прикладные сообщения и logs.

### Не Входит

- `WorkOrder`, `Default` и `EditVersion`;
- workspace API;
- изменение network features или associations;
- validation, reconcile, conflicts, review и post;
- topology trace и электрические расчеты;
- явный reset или `full-clean`;
- восстановление, синхронизация или удаление отдельных записей уже
  существующего feeder;
- изменение модели День 3 для добавления FK между `Feeder` и `AOI`.

## Состав Dataset

Dataset имеет код:

```text
synthetic_utility_feeder_01
```

Seed задает feeder стабильный UUID, чтобы endpoint по `feederId`,
integration tests и demo-сценарий были воспроизводимы без отдельного
list/search endpoint:

```text
6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0101
```

UUID фиксируется в dataset specs и не генерируется заново при каждом чистом
seed.

Он содержит:

| Сущность | Количество |
|---|---:|
| `AOI` | 1 |
| `Feeder` | 1 |
| Junction | 7 |
| Line | 6 |
| Device | 6 |
| `NetworkAssociation` | 9 |

Всего feeder содержит 19 `NetworkFeature`.

### AOI

Создается один валидный Polygon с SRID 4326, покрывающий все объекты
demo feeder. Связь AOI с feeder не хранится отдельным FK. Backend определяет
релевантные AOI пространственным запросом.

### Junctions

Используются стабильные `asset_code`:

```text
J-001
J-002
J-003
J-004
J-005
J-006
J-007
```

Они представляют шину подстанции, промежуточные узлы, узел секционного
выключателя, точку ветвления, отвод трансформатора, точку потребителя и tie
point.

### Lines

Используются стабильные `asset_code`:

```text
L-001
L-002
L-003
L-004
L-005
L-006
```

Линии формируют основную цепь feeder, отвод к трансформатору, низковольтный
участок и normally-open tie line. Geometry каждой линии согласована с
координатами соответствующих junctions.

### Devices

Используются стабильные `asset_code`:

```text
D-001
D-002
D-003
D-004
D-005
D-006
```

Набор включает breaker, sectional switch, fuse, transformer, tie switch и
meter. Тип, status, normal state, voltage и другие предметные атрибуты
хранятся в `NetworkFeature.properties`.

### Associations

Создаются 9 направленных associations между features:

```text
D-001 -> L-001  connectivity
D-002 -> L-002  connectivity
D-002 -> L-003  connectivity
D-003 -> L-003  connectivity
D-003 -> L-004  connectivity
D-004 -> L-004  connectivity
D-004 -> L-005  connectivity
D-005 -> L-006  connectivity
D-004 -> D-006  connectivity
```

Исходные предметные формулировки `connected_to` и `feeds` для базового
dataset нормализуются в поддерживаемый моделью День 3 тип `connectivity`.
Типы `containment` и `attachment` в Интенсиве 4 не используются. Связь AOI с
feeder или feature не записывается как
`NetworkAssociation`, поскольку оба конца association обязаны быть
`NetworkFeature` одного feeder.

## Seed Архитектура

### Граница Пакета

Вся seed-логика приложения размещается в отдельном пакете:

```text
seeds/
  repositories/
    seed_user_repository.py
    seed_utility_dataset_repository.py
  services/
    seed_demo_user_service.py
    seed_utility_dataset_service.py
  specs/
    seed_demo_user_specs.py
    seed_utility_dataset_specs.py
  runners/
    seed_demo_users.py
    seed_utility_dataset.py
```

Каждая папка содержит `__init__.py`. Все имена seed-файлов начинаются с
`seed_`, а все объявленные в них классы — с `Seed`.

Seed-код не размещается в runtime-пакетах `services/` и `repositories/` и не
импортирует runtime service или repository для выполнения seed-операций.
Общая password hashing logic размещается в нейтральном
`core/passwords.py`, которым независимо пользуются auth и user seed. Существующий
`repositories.user_repository.UserRepository` остается runtime-зависимостью
auth service. Для user seed создается отдельный
`seeds.repositories.seed_user_repository.SeedUserRepository`.

### Компоненты Utility Dataset

`SeedUtilityDatasetRepository` отвечает за:

- поиск feeder по `code`;
- добавление AOI, feeder, features и associations в session;
- минимальные read-операции, необходимые seed service.

`SeedUtilityDatasetService` отвечает за:

- create-once решение;
- использование канонического `SeedUtilityDatasetSpec`;
- создание ORM entities со стабильными business codes;
- разрешение association endpoints через созданные features;
- единый transaction boundary;
- русскоязычные logs результата.

### Компоненты Demo Users

Существующий user seed переносится без изменения поведения:

- `SeedDemoUserSpec` и `SEED_DEMO_USER_SPECS` задают трех стабильных users;
- `SeedUserRepository` содержит только операции, необходимые seed;
- `SeedDemoUserService` создает отсутствующих users и восстанавливает role,
  password и `is_active`;
- runtime `UserRepository` продолжает обслуживать auth и не используется
  seed service.

### Runners

CLI entry points запускаются как Python modules:

```text
python -m seeds.runners.seed_demo_users
python -m seeds.runners.seed_utility_dataset
```

Каждый runner вызывает `run_seed_*`, который создает отдельную async session
через `SessionFactory` и запускает соответствующий seed service. Runner не
содержит business logic.

### Транзакционность

Новый dataset создается атомарно:

```text
begin
  create AOI
  create Feeder
  create 19 NetworkFeature
  flush and resolve UUID
  create 9 NetworkAssociation
commit
```

При любой ошибке выполняется rollback. Частично созданный feeder не должен
оставаться в БД.

### Повторный Запуск

Наличие feeder с кодом `synthetic_utility_feeder_01` является границей
create-once поведения.

Повторный запуск:

- не создает дубликат feeder;
- не сравнивает существующие записи с эталоном;
- не добавляет отсутствующие отдельные features или associations;
- не восстанавливает измененные properties или geometry;
- не удаляет дополнительные записи;
- завершает seed успешно и пишет информационный log.

Такое поведение сохраняет данные при обычном restart и исключает скрытые
изменения пользовательского состояния.

## Read-Only API

### Пакет Response Schemas

Response DTO разделяются по одной ответственности:

```text
schemas/
  utility_network/
    __init__.py
    geojson_feature_out.py
    feature_collection_out.py
    association_out.py
    feeder_out.py
```

Каждый файл содержит один публичный Pydantic-класс. `__init__.py`
re-export'ит `UtilityGeoJSONFeatureOut`, `UtilityFeatureCollectionOut`,
`UtilityAssociationOut` и `UtilityFeederOut`, поэтому service и router
импортируют DTO из `schemas.utility_network`, не завися от внутренней
структуры файлов.

### Endpoint

```http
GET /api/v1/utility-network/feeders/{feederId}
Authorization: Bearer <editor-token>
```

Endpoint доступен только активному пользователю с ролью `Editor`.
Активный `Reviewer` получает `403`.

`feederId` является UUID primary key. `Feeder.code` остается
человекочитаемым бизнес-атрибутом ответа, но не используется для адресации
этого ресурса.

### Ответ

Успешный ответ `200`:

```json
{
  "id": "6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0101",
  "code": "synthetic_utility_feeder_01",
  "name": "Демонстрационный фидер 10 кВ",
  "isActive": true,
  "aois": {
    "type": "FeatureCollection",
    "features": []
  },
  "network": {
    "type": "FeatureCollection",
    "features": []
  },
  "associations": []
}
```

Используется существующее правило сериализации API: JSON keys остаются на
английском языке. Внутренние имена Python-полей остаются в `snake_case`.
Публичные поля `isActive`, `assetCode`, `featureType`, `fromFeatureId`,
`toFeatureId` и `associationType` задаются явными Pydantic serialization
aliases. Wire contract использует показанные camelCase keys.

### AOI GeoJSON

`aois` является GeoJSON `FeatureCollection`.

Repository включает все AOI, для которых существует хотя бы один feature
запрошенного feeder, удовлетворяющий:

```sql
ST_Intersects(utility_network.aois.geometry,
              utility_network.network_features.geometry)
```

Correlated `EXISTS` проверяет наличие пересечения, не присоединяя features к
результату AOI. Поэтому один AOI возвращается один раз независимо от количества
пересекающих его features, и дополнительный `DISTINCT` не требуется.

Один feeder может пересекать несколько AOI. Все они включаются в ответ.
Если пересечений нет, endpoint возвращает пустой `FeatureCollection` и
остается успешным.

Каждый AOI сериализуется как GeoJSON `Feature`:

- `id` содержит UUID;
- `geometry` содержит Polygon или MultiPolygon;
- `properties` содержит `name` и `description`.

AOI сортируются детерминированно по `name`, затем по UUID.

### Network GeoJSON

`network` является GeoJSON `FeatureCollection` и содержит все features
запрошенного feeder независимо от найденных AOI.

Каждый feature сериализуется как GeoJSON `Feature`:

- `id` содержит UUID;
- `geometry` содержит Point или LineString;
- `properties` содержит `assetCode`, `featureType`, `name`, `description`,
  `version` и все доменные значения из сохраненного `properties`.

Системные поля имеют приоритет над одноименными ключами из JSONB
`properties`, чтобы сохраненные данные не могли подменить `assetCode`,
`featureType`, `name`, `description` или `version`.

Features сортируются по `assetCode`, затем по UUID.

### Associations

Каждый элемент `associations` содержит:

```json
{
  "id": "uuid",
  "fromFeatureId": "uuid",
  "toFeatureId": "uuid",
  "associationType": "connectivity",
  "version": 1
}
```

Associations сортируются по `fromFeatureId`, `toFeatureId`,
`associationType`, затем по UUID.

Service проверяет, что оба конца каждой association входят в набор features
ответа. Нарушение считается ошибкой целостности dataset.

## Поток Данных

```text
HTTP request
-> JWT authentication
-> active user lookup
-> Editor role guard
-> FastAPI validates feederId as UUID
-> UtilityNetworkService.get_feeder(feederId)
-> repository executes one aggregate SQL query
-> query returns one feeder row with features_data, associations_data, aois_data
-> service validates aggregate references
-> service maps geometry to GeoJSON
-> Pydantic response
```

Чтение не изменяет feeder, version или timestamps.

## Single-Query Repository

`UtilityNetworkRepository` предоставляет один read method:

```python
async def get_feeder_aggregate(
    feeder_id: UUID,
) -> FeederAggregateRow | None:
```

Запрос возвращает одну строку feeder. Три независимых correlated subquery
формируют JSONB-массивы:

- все features feeder с GeoJSON geometry;
- все associations feeder;
- все AOI, для которых `EXISTS` пересекающий feature feeder.

Обычный плоский `JOIN` всех коллекций запрещен, поскольку он создает
размножение `features × associations × AOI`. Каждая JSONB-агрегация имеет
собственную детерминированную сортировку и возвращает `[]`, если коллекция
пуста. Service сохраняет проверку того, что оба конца каждой association
присутствуют в `features_data`.

## Ошибки

| HTTP | Code | Условие |
|---:|---|---|
| `401` | `AUTH_REQUIRED` | Токен отсутствует или недействителен |
| `403` | `USER_INACTIVE` | Учетная запись пользователя отключена |
| `403` | `ROLE_NOT_ALLOWED` | Пользователь не имеет роли `Editor` |
| `404` | `FEEDER_NOT_FOUND` | Feeder с указанным `feederId` отсутствует |
| `422` | стандартная ошибка FastAPI | `feederId` не является допустимым UUID |
| `500` | `UTILITY_DATASET_INVALID` | Агрегат нарушает ожидаемую целостность или geometry нельзя сериализовать |

Error body следует существующему structured error contract. Человекочитаемое
`message` и application logs пишутся на русском языке, а `code` остается
стабильным английским идентификатором.

Отдельный application error code для неверного UUID не вводится: стандартная
ошибка валидации FastAPI остается достаточной.

## Тестирование

### Unit Tests

Проверяются:

- стабильный состав dataset specs;
- стабильный UUID feeder;
- 7 junctions, 6 lines, 6 devices и 9 associations;
- уникальность всех `asset_code`;
- все association endpoints существуют в specs;
- create-once ветвление seed service;
- отсутствие записей при существующем feeder;
- mapping ORM geometry и properties в GeoJSON;
- приоритет системных properties над JSONB;
- проверка association references;
- role guard для `Editor`.

### PostgreSQL/PostGIS Integration Tests

На реальной test database проверяются:

- создание полного dataset одной транзакцией;
- rollback всего dataset при ошибке;
- повторный запуск не создает дубликаты;
- повторный запуск не изменяет geometry, properties и дополнительные записи
  существующего feeder;
- все geometry валидны и имеют SRID 4326;
- все features принадлежат одному feeder;
- все associations принадлежат тому же feeder и ссылаются на существующие
  features;
- пространственный запрос возвращает demo AOI;
- дополнительный пересекающий AOI включается в ответ;
- непересекающийся AOI не включается;
- feeder без пересекающихся AOI возвращает пустой список AOI.

### API Tests

Проверяются:

- активный `Editor` получает `200`;
- активный `Reviewer` получает `403`;
- запрос без авторизации получает `401`;
- неизвестный корректный UUID получает `404 FEEDER_NOT_FOUND`;
- некорректный UUID получает стандартный `422`;
- ответ содержит 19 network features и 9 associations;
- ответ содержит все пересекающиеся AOI;
- возвращаются все features feeder, а не только features внутри AOI;
- GeoJSON geometry и доменные properties сериализуются без потерь;
- порядок AOI, features и associations детерминирован;
- каждая association ссылается на feature из ответа;
- поврежденный агрегат приводит к `500 UTILITY_DATASET_INVALID`.

### Startup Smoke

Compose smoke должен подтверждать:

1. migrations выполняются успешно;
2. demo users создаются;
3. utility dataset создается;
4. backend становится healthy;
5. авторизованный `Editor` читает seeded feeder по его стабильному UUID через
   `/api/v1/utility-network/feeders/{feederId}`;
6. restart backend не изменяет существующий feeder.

## Критерии Готовности

Интенсив 4 завершен, когда:

1. чистый startup создает полный `synthetic_utility_feeder_01`;
2. создание dataset атомарно;
3. обычный restart не изменяет существующий feeder;
4. активный `Editor` получает полный агрегированный GeoJSON-ответ;
5. `Reviewer` не получает доступ к endpoint;
6. endpoint возвращает все features feeder и все пересекающиеся AOI;
7. unit, API и PostgreSQL/PostGIS integration tests проходят;
8. существующие backend tests и Compose startup не регрессируют.

## Последствия Решения

- День 4 дает отдельный проверяемый backend result до появления
  `WorkOrder/EditVersion`.
- Endpoint является read-only диагностическим и demo-контуром, а не
  окончательным workspace API.
- Пространственная связь feeder с AOI допускает несколько AOI и не требует
  преждевременного изменения схемы.
- Create-once startup seed сохраняет данные, но не исправляет частично
  поврежденный существующий dataset.
- Явный reset должен быть спроектирован отдельно и сможет канонически
  восстановить dataset без изменения startup semantics.
