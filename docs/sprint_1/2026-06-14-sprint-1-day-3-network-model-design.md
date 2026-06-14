# Спринт 1, День 3: Базовая Модель Сети

Дата: 2026-06-14
Статус: согласован пользователем

## Назначение

День 3 реализует persistence-модель для базового участка электрической сети.
Результат дня включает SQLAlchemy-модели, Alembic-миграцию и тесты ограничений
для `AOI`, `Feeder`, `NetworkFeature` и `NetworkAssociation`.

Seed `synthetic_utility_feeder_01`, repositories, services и API не входят в
День 3. Они относятся к следующим вертикальным задачам Спринта 1.

Связанные документы:

- `2026-06-12-sprint-1-day-1-domain-model-design.md`;
- `2026-06-12-sprint-1-day-1-vertical-backlog-design.md`;
- `2026-06-12-sprint-1-utility-workflow-calendar-design.md`.

## Выбранный Подход

Используется DB-centric relational model:

- отдельные таблицы `utility_network.aois`, `utility_network.feeders`,
  `utility_network.network_features` и
  `utility_network.network_associations`;
- основные инварианты обеспечиваются PostgreSQL/PostGIS;
- SQLAlchemy relationships дают навигацию между моделями, но не заменяют
  ограничения БД;
- существующие generic-таблицы `feature_point`, `feature_line` и другие не
  расширяются и не используются как storage для utility network.

Такой подход дает `Feeder` четкую границу агрегата и не позволяет seed,
миграциям или прямому SQL обойти правила целостности.

## Граница Python-Пакета И PostgreSQL Schema

Модели текущего Utility GIS Editor UseCase размещаются в отдельном пакете:

```text
models/
  base.py
  utility_network/
    __init__.py
    aoi.py
    feeder.py
    network_feature.py
    network_association.py
```

Пакет использует существующий общий `models.base.Base`.
`models.utility_network` публично экспортирует `AOI`, `Feeder`,
`NetworkFeature`, `FeatureType`, `NetworkAssociation` и `AssociationType`.

Все таблицы текущего Utility GIS Editor UseCase размещаются в PostgreSQL
schema `utility_network`. Для Day 3 это четыре сетевые сущности; будущие
use-case-specific сущности `WorkOrder`, `EditVersion`, conflicts и audit также
должны размещаться в этой schema. Если появится другой UseCase, совместно
используемые сущности выделяются отдельной миграцией в общую schema.

Каждая модель явно задает `schema="utility_network"`. Все FK используют
schema-qualified имена. PostgreSQL `search_path` не изменяется и не является
частью correctness-механизма.

## Модель Данных

### AOI

Таблица `utility_network.aois`:

| Поле | Тип | Правила |
|---|---|---|
| `id` | UUID | Primary key, генерируется приложением |
| `name` | String | Обязательно |
| `description` | Text | Nullable |
| `geometry` | PostGIS Geometry | `Polygon` или `MultiPolygon`, SRID 4326 |
| `created_at` | DateTime with timezone | Обязательно, текущее время по умолчанию |
| `updated_at` | DateTime with timezone | Обязательно, обновляется при изменении через ORM |

`AOI` является серверной границей доступного набора данных workspace. Extent
не хранится отдельно и в дальнейшем вычисляется из `geometry`.

### Feeder

Таблица `utility_network.feeders`:

| Поле | Тип | Правила |
|---|---|---|
| `id` | UUID | Primary key, генерируется приложением |
| `code` | String | Обязательно, глобально уникально |
| `name` | String | Обязательно |
| `description` | Text | Nullable |
| `is_active` | Boolean | Обязательно, `true` по умолчанию |
| `created_at` | DateTime with timezone | Обязательно, текущее время по умолчанию |
| `updated_at` | DateTime with timezone | Обязательно, обновляется при изменении через ORM |

`Feeder` является агрегатом demo-сети, но не моделью электрического расчета.

### NetworkFeature

Таблица `utility_network.network_features`:

| Поле | Тип | Правила |
|---|---|---|
| `id` | UUID | Primary key, генерируется приложением |
| `feeder_id` | UUID | Обязательный FK на `utility_network.feeders.id`, `ON DELETE RESTRICT` |
| `asset_code` | String | Обязательный человекочитаемый код |
| `feature_type` | Enum | `junction`, `line`, `device` |
| `geometry` | PostGIS Geometry | `Point` или `LineString`, SRID 4326 |
| `name` | String | Обязательно |
| `description` | Text | Nullable |
| `properties` | JSONB | Обязательно, пустой объект по умолчанию |
| `version` | Integer | Обязательно, `1` по умолчанию, значение не меньше `1` |
| `created_at` | DateTime with timezone | Обязательно, текущее время по умолчанию |
| `updated_at` | DateTime with timezone | Обязательно, обновляется при изменении через ORM |

Пара `(feeder_id, asset_code)` уникальна. В Release 1 `asset_code` является
человекочитаемым идентификатором внутри feeder: например, `J-001`, `L-003`
или `D-006`. UUID `id` остается техническим ключом для связей.

Пара `(feeder_id, id)` также объявляется уникальной. Она нужна как
candidate key для составных внешних ключей associations и гарантирует
принадлежность связанных объектов тому же feeder на уровне БД.

Тип объекта определяет допустимую геометрию:

- `junction` использует `Point`;
- `device` использует `Point`;
- `line` использует `LineString`.

`properties` содержит расширяемые предметные атрибуты. `name` и `description`
остаются отдельными колонками, чтобы основной UI и поиск не зависели от
структуры JSON.

### NetworkAssociation

Таблица `utility_network.network_associations`:

| Поле | Тип | Правила |
|---|---|---|
| `id` | UUID | Primary key, генерируется приложением |
| `feeder_id` | UUID | Обязательный FK на `utility_network.feeders.id`, `ON DELETE RESTRICT` |
| `from_feature_id` | UUID | Обязательная часть составного FK |
| `to_feature_id` | UUID | Обязательная часть составного FK |
| `association_type` | Enum | `connectivity`, `containment`, `attachment` |
| `version` | Integer | Обязательно, `1` по умолчанию, значение не меньше `1` |
| `created_at` | DateTime with timezone | Обязательно, текущее время по умолчанию |
| `updated_at` | DateTime with timezone | Обязательно, обновляется при изменении через ORM |

Составные внешние ключи:

- `(feeder_id, from_feature_id)` ссылается на
  `utility_network.network_features(feeder_id, id)`;
- `(feeder_id, to_feature_id)` ссылается на
  `utility_network.network_features(feeder_id, id)`.

Оба ключа используют `ON DELETE RESTRICT`. Поэтому association не может
ссылаться на отсутствующий объект или пересекать границу feeder, а feature
нельзя удалить, пока он участвует в association.

Association является направленной. Запрещены:

- self-reference: `from_feature_id = to_feature_id`;
- точный дубль `(feeder_id, from_feature_id, to_feature_id,
  association_type)`.

Обратная связь `B -> A` не считается дублем связи `A -> B`.

## Представление Enum

`FeatureType` и `AssociationType` реализуются как Python `str, enum.Enum` и
хранятся через ненативный SQLAlchemy `Enum` с CHECK constraint. Это
соответствует принятому для `UserRole` подходу:

- значения БД остаются читаемыми строками;
- миграция не создает PostgreSQL enum type;
- изменение набора значений остается управляемым через обычную миграцию.

## Пространственные Ограничения

Для `AOI.geometry` и `NetworkFeature.geometry` БД проверяет:

- geometry не является пустой;
- `ST_IsValid(geometry)` возвращает `true`;
- SRID равен 4326;
- тип geometry входит в разрешенный набор;
- для `NetworkFeature` тип geometry соответствует `feature_type`.

Ограничения задаются явно в Alembic-миграции через PostGIS CHECK expressions.
Невалидная запись должна отклоняться независимо от пути записи.

## Удаление И Каскады

Для доменных связей используется `RESTRICT`:

- непустой `Feeder` нельзя удалить;
- `NetworkFeature`, участвующий в association, нельзя удалить;
- ORM delete cascade для этих отношений не включается.

Soft delete для четырех моделей в День 3 не вводится. Поле `is_active`
существует только у `Feeder`, поскольку оно является частью согласованного
контракта агрегата, а не универсальным механизмом удаления.

## ORM И Alembic

Модели используют текущий SQLAlchemy 2 declarative style:

- `Mapped`;
- `mapped_column`;
- общий `models.base.Base`;
- PostgreSQL `UUID` и `JSONB`;
- GeoAlchemy2 `Geometry`.

Alembic metadata должен импортировать новые модели до чтения `Base.metadata`,
чтобы будущий autogenerate видел таблицы. `context.configure` использует
`include_schemas=True`, при этом существующие модели из `public` также
остаются в metadata. Миграция создается вручную и:

1. выполняет `CREATE SCHEMA utility_network`;
2. создает schema-qualified таблицы, FK, indexes и CHECK constraints;
3. не меняет PostgreSQL `search_path`.

Downgrade удаляет таблицы в обратном порядке зависимостей:

1. `utility_network.network_associations`;
2. `utility_network.network_features`;
3. `utility_network.feeders`;
4. `utility_network.aois`;
5. выполняет `DROP SCHEMA utility_network` без `CASCADE`.

Downgrade намеренно завершается ошибкой, если в schema остались неизвестные
объекты. Это запрещает скрыто удалять будущие таблицы.

## Обработка Ошибок

На этом этапе нарушение ограничения приводит к SQLAlchemy `IntegrityError`.
Преобразование таких ошибок в русскоязычные прикладные ошибки и HTTP responses
не входит в День 3 и будет спроектировано вместе с repositories/services/API.

## Тестирование

### Unit И Metadata Tests

Без обращения к API проверяются:

- имена таблиц и обязательные колонки;
- публичные exports `models.utility_network`;
- `__table__.schema == "utility_network"` для всех четырех моделей;
- строковые значения `FeatureType` и `AssociationType`;
- defaults `is_active`, `properties` и `version`;
- наличие relationships без ORM delete cascade;
- наличие unique, FK и CHECK constraints в metadata;
- schema-qualified targets всех FK;
- ровно один явный GiST spatial index на каждую geometry-колонку:
  `utility_network.aois.geometry` и
  `utility_network.network_features.geometry`.

### PostgreSQL/PostGIS Integration Tests

На реальной test database проверяются:

- таблицы существуют в `utility_network`, а не в `public`;
- для каждой geometry-колонки существует ровно один GiST index, без
  автоматического дубля от GeoAlchemy2;
- сохранение допустимых `Polygon`, `MultiPolygon`, `Point` и `LineString`;
- отклонение неверного SRID, пустой и невалидной geometry;
- отклонение geometry, несовместимой с `feature_type`;
- уникальность `(feeder_id, asset_code)` и возможность повторить
  `asset_code` в другом feeder;
- запрет отсутствующих и межфидерных концов association;
- запрет self-reference и точного дубля направленной association;
- допустимость обратной association;
- `RESTRICT` при удалении непустого feeder и связанного feature;
- default `version = 1` и запрет `version < 1`.

### Migration Tests

Проверяется полный цикл:

1. upgrade с предыдущей revision до новой;
2. наличие schema `utility_network`, четырех таблиц, constraints и spatial
   indexes внутри нее;
3. ровно один GiST index на `aois.geometry` и один на
   `network_features.geometry` после первого и повторного upgrade;
4. отсутствие одноименных таблиц в `public`;
5. неизменность `search_path`;
6. downgrade до предыдущей revision удаляет таблицы и schema;
7. повторный upgrade восстанавливает структуру.

## Критерии Готовности

День 3 завершен, когда:

1. четыре модели доступны через `models.utility_network` и SQLAlchemy metadata;
2. Alembic upgrade создает schema `utility_network` и согласованную структуру
   на PostgreSQL/PostGIS;
3. ограничения БД защищают геометрию и границу агрегата `Feeder`;
4. downgrade работает без ручного вмешательства;
5. unit и integration tests проходят;
6. существующие backend tests не регрессируют;
7. seed и API не добавлены преждевременно.

## Вне Scope

- `synthetic_utility_feeder_01` и любой другой seed;
- repositories, services, schemas и endpoints;
- `WorkOrder`, `Default` и `EditVersion`;
- редактирование network features;
- change set, validation, reconcile, conflicts, review и post;
- межфидерные associations;
- смена feeder у существующего feature;
- topology trace и электрические расчеты;
- external asset registry, `source_system` и `external_id`;
- автоматическая генерация `asset_code`;
- soft delete и полный audit trail.
