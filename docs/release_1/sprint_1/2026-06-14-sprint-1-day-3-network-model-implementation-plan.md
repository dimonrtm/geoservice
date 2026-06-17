# План Реализации Базовой Модели Сети Дня 3 Спринта 1

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Реализовать SQLAlchemy-модели, Alembic-миграцию и PostgreSQL/PostGIS-тесты для `AOI`, `Feeder`, `NetworkFeature` и `NetworkAssociation`.

**Architecture:** Модели текущего Utility GIS Editor UseCase живут в пакете `models.utility_network` и используют общий `models.base.Base`. PostgreSQL/PostGIS schema `utility_network` создается Alembic-миграцией; модели, FK и запросы используют явные schema-qualified имена без изменения `search_path`. БД обеспечивает геометрические CHECK constraints, границу агрегата `Feeder`, уникальность кодов и целостность направленных associations; ORM relationships служат только для навигации и не выполняют delete cascade.

**Tech Stack:** Python 3.12, SQLAlchemy 2.0, Alembic 1.14, PostgreSQL 16, PostGIS 3.4, GeoAlchemy2, asyncpg, pytest, Docker Compose.

---

## Предусловия Исполнения

- Работать в текущей ветке и учитывать существующие незакоммиченные файлы пользователя.
- Не менять generic-таблицы `feature_points`, `feature_lines` и другие.
- Не добавлять seed, repositories, services, schemas или API.
- Не изменять существующие staged-файлы пользователя.
- Не выполнять `git add`, `git commit` или другие операции записи в Git.
- Для Docker-команд использовать Compose из `infra/`.

## Граница Scope

План реализует:

- package `models.utility_network` с публичными exports;
- PostgreSQL schema `utility_network`;
- таблицы `utility_network.aois`, `utility_network.feeders`,
  `utility_network.network_features`, `utility_network.network_associations`;
- `FeatureType` и `AssociationType`;
- SQLAlchemy relationships без delete cascade;
- миграцию `d3a01f4e9c21`;
- metadata/unit tests;
- PostgreSQL/PostGIS integration tests;
- upgrade/downgrade migration test;
- запуск DB tests в CI smoke job.

План не реализует:

- `synthetic_utility_feeder_01`;
- `WorkOrder`, `Default`, `EditVersion`;
- network repositories и API;
- topology validation, trace, reconcile, conflicts или post;
- автоматическую генерацию `asset_code`;
- soft delete и audit trail.

## Карта Файлов

**ORM-модели**

- Create: `apps/backend/app/models/utility_network/__init__.py`
- Create: `apps/backend/app/models/utility_network/aoi.py`
- Create: `apps/backend/app/models/utility_network/feeder.py`
- Create: `apps/backend/app/models/utility_network/network_feature.py`
- Create: `apps/backend/app/models/utility_network/network_association.py`
- Modify: `apps/backend/app/alembic/env.py`

**Миграция**

- Create: `apps/backend/app/alembic/versions/d3a01f4e9c21_network_model.py`

**Тесты**

- Create: `apps/backend/app/tests/test_network_model_metadata.py`
- Create: `apps/backend/app/tests/network_db_support.py`
- Create: `apps/backend/app/tests/test_network_model_integration.py`
- Create: `apps/backend/app/tests/test_network_model_migration.py`

**CI и документация**

- Modify: `.github/workflows/ci.yml`
- Modify: `docs/release_1/sprint_1/README.md`

### Задача 1: Добавить AOI И Feeder С Metadata-Тестами

**Files:**

- Create: `apps/backend/app/tests/test_network_model_metadata.py`
- Create: `apps/backend/app/models/utility_network/__init__.py`
- Create: `apps/backend/app/models/utility_network/aoi.py`
- Create: `apps/backend/app/models/utility_network/feeder.py`

- [ ] **Шаг 1: Написать падающие metadata-тесты AOI и Feeder**

Создать `apps/backend/app/tests/test_network_model_metadata.py`:

```python
from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.orm import configure_mappers

from models.utility_network import AOI, Feeder


def constraint_names(model: type) -> set[str]:
    return {
        constraint.name
        for constraint in model.__table__.constraints
        if constraint.name is not None
    }


def test_aoi_metadata_contains_geometry_guards() -> None:
    assert AOI.__tablename__ == "aois"
    assert AOI.__table__.schema == "utility_network"
    assert {column.name for column in AOI.__table__.columns} == {
        "id",
        "name",
        "description",
        "geometry",
        "created_at",
        "updated_at",
    }
    assert {
        "ck_aois_geometry_not_empty",
        "ck_aois_geometry_valid",
        "ck_aois_geometry_srid",
        "ck_aois_geometry_type",
    }.issubset(constraint_names(AOI))


def test_feeder_metadata_contains_defaults_and_unique_code() -> None:
    assert Feeder.__tablename__ == "feeders"
    assert Feeder.__table__.schema == "utility_network"
    assert Feeder.__table__.c.is_active.default.arg is True
    assert str(Feeder.__table__.c.is_active.server_default.arg) == "true"
    assert any(
        isinstance(constraint, UniqueConstraint)
        and tuple(column.name for column in constraint.columns) == ("code",)
        for constraint in Feeder.__table__.constraints
    )


def test_aoi_check_constraints_are_named() -> None:
    checks = [
        constraint
        for constraint in AOI.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    ]
    assert checks
    assert all(constraint.name for constraint in checks)


def test_aoi_declares_exactly_one_spatial_index() -> None:
    indexes = [
        index
        for index in AOI.__table__.indexes
        if tuple(column.name for column in index.columns) == ("geometry",)
    ]
    assert len(indexes) == 1
    assert indexes[0].name == "ix_aois_geometry"
    assert indexes[0].dialect_options["postgresql"]["using"] == "gist"
    assert AOI.__table__.c.geometry.type.spatial_index is False


def test_initial_network_mappers_configure_without_errors() -> None:
    configure_mappers()


def test_utility_network_package_exports_initial_models() -> None:
    from models import utility_network

    assert utility_network.AOI is AOI
    assert utility_network.Feeder is Feeder
```

- [ ] **Шаг 2: Запустить тест и подтвердить ожидаемое падение**

Из `apps/backend/app`:

```powershell
pytest tests/test_network_model_metadata.py -q
```

Ожидается: FAIL во время collection с
`ModuleNotFoundError: No module named 'models.utility_network'`.

- [ ] **Шаг 3: Реализовать модель AOI**

Создать `apps/backend/app/models/utility_network/aoi.py`:

```python
import uuid
from datetime import datetime
from uuid import UUID

from geoalchemy2 import Geometry
from sqlalchemy import CheckConstraint, DateTime, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class AOI(Base):
    __tablename__ = "aois"
    __table_args__ = (
        CheckConstraint(
            "NOT ST_IsEmpty(geometry)",
            name="ck_aois_geometry_not_empty",
        ),
        CheckConstraint(
            "ST_IsValid(geometry)",
            name="ck_aois_geometry_valid",
        ),
        CheckConstraint(
            "ST_SRID(geometry) = 4326",
            name="ck_aois_geometry_srid",
        ),
        CheckConstraint(
            "GeometryType(geometry) IN ('POLYGON', 'MULTIPOLYGON')",
            name="ck_aois_geometry_type",
        ),
        Index("ix_aois_geometry", "geometry", postgresql_using="gist"),
        {"schema": "utility_network"},
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    geometry: Mapped[object] = mapped_column(
        Geometry(
            geometry_type="GEOMETRY",
            srid=4326,
            spatial_index=False,
        ),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
```

- [ ] **Шаг 4: Реализовать модель Feeder**

Создать `apps/backend/app/models/utility_network/feeder.py`:

```python
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base

if TYPE_CHECKING:
    from .network_association import NetworkAssociation
    from .network_feature import NetworkFeature


class Feeder(Base):
    __tablename__ = "feeders"
    __table_args__ = (
        UniqueConstraint("code", name="uq_feeders_code"),
        {"schema": "utility_network"},
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    features: Mapped[list[NetworkFeature]] = relationship(
        "NetworkFeature",
        back_populates="feeder",
        passive_deletes=True,
    )
    associations: Mapped[list[NetworkAssociation]] = relationship(
        "NetworkAssociation",
        back_populates="feeder",
        passive_deletes=True,
    )
```

Создать `apps/backend/app/models/utility_network/__init__.py`:

```python
from .aoi import AOI
from .feeder import Feeder

__all__ = ["AOI", "Feeder"]
```

- [ ] **Шаг 5: Запустить целевой тест**

```powershell
pytest tests/test_network_model_metadata.py -q
```

Ожидается: collection все еще FAIL, потому что `Feeder` ссылается на еще не созданные `NetworkFeature` и `NetworkAssociation`. Это ожидаемое промежуточное состояние TDD.

- [ ] **Шаг 6: Проверить diff**

```powershell
git diff -- apps/backend/app/models/utility_network apps/backend/app/tests/test_network_model_metadata.py
git status --short
```

Ожидается: только два новых model-файла и metadata-test текущей задачи.

### Задача 2: Добавить NetworkFeature И Его Инварианты

**Files:**

- Modify: `apps/backend/app/tests/test_network_model_metadata.py`
- Modify: `apps/backend/app/models/utility_network/__init__.py`
- Create: `apps/backend/app/models/utility_network/network_feature.py`

- [ ] **Шаг 1: Расширить падающие metadata-тесты NetworkFeature**

Добавить импорты:

```python
from sqlalchemy import CheckConstraint, ForeignKeyConstraint, UniqueConstraint

from models.utility_network import FeatureType, NetworkFeature
```

Добавить тесты:

```python
def test_feature_type_values_are_stable_strings() -> None:
    assert {item.value for item in FeatureType} == {
        "junction",
        "line",
        "device",
    }


def test_network_feature_metadata_contains_aggregate_guards() -> None:
    assert NetworkFeature.__tablename__ == "network_features"
    assert NetworkFeature.__table__.schema == "utility_network"
    assert NetworkFeature.__table__.c.properties.default.is_callable is True
    assert NetworkFeature.__table__.c.version.default.arg == 1
    assert str(NetworkFeature.__table__.c.version.server_default.arg) == "1"

    names = constraint_names(NetworkFeature)
    assert {
        "fk_network_features_feeder",
        "uq_network_features_feeder_asset_code",
        "uq_network_features_feeder_id_id",
        "ck_network_features_geometry_not_empty",
        "ck_network_features_geometry_valid",
        "ck_network_features_geometry_srid",
        "ck_network_features_geometry_matches_type",
        "ck_network_features_version_positive",
    }.issubset(names)


def test_network_feature_has_restrict_feeder_foreign_key() -> None:
    foreign_keys = [
        constraint
        for constraint in NetworkFeature.__table__.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    ]
    assert len(foreign_keys) == 1
    assert {
        element.ondelete
        for constraint in foreign_keys
        for element in constraint.elements
    } == {"RESTRICT"}
    assert {
        element.target_fullname
        for constraint in foreign_keys
        for element in constraint.elements
    } == {"utility_network.feeders.id"}


def test_network_feature_declares_exactly_one_spatial_index() -> None:
    indexes = [
        index
        for index in NetworkFeature.__table__.indexes
        if tuple(column.name for column in index.columns) == ("geometry",)
    ]
    assert len(indexes) == 1
    assert indexes[0].name == "ix_network_features_geometry"
    assert indexes[0].dialect_options["postgresql"]["using"] == "gist"
    assert NetworkFeature.__table__.c.geometry.type.spatial_index is False
```

- [ ] **Шаг 2: Запустить тест и подтвердить падение**

```powershell
pytest tests/test_network_model_metadata.py -q
```

Ожидается: FAIL, потому что `FeatureType` и `NetworkFeature` еще не
экспортируются из `models.utility_network`.

- [ ] **Шаг 3: Реализовать NetworkFeature**

Создать `apps/backend/app/models/utility_network/network_feature.py`:

```python
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from geoalchemy2 import Geometry
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base

if TYPE_CHECKING:
    from .feeder import Feeder
    from .network_association import NetworkAssociation


class FeatureType(str, enum.Enum):
    JUNCTION = "junction"
    LINE = "line"
    DEVICE = "device"


class NetworkFeature(Base):
    __tablename__ = "network_features"
    __table_args__ = (
        UniqueConstraint(
            "feeder_id",
            "asset_code",
            name="uq_network_features_feeder_asset_code",
        ),
        UniqueConstraint(
            "feeder_id",
            "id",
            name="uq_network_features_feeder_id_id",
        ),
        CheckConstraint(
            "NOT ST_IsEmpty(geometry)",
            name="ck_network_features_geometry_not_empty",
        ),
        CheckConstraint(
            "ST_IsValid(geometry)",
            name="ck_network_features_geometry_valid",
        ),
        CheckConstraint(
            "ST_SRID(geometry) = 4326",
            name="ck_network_features_geometry_srid",
        ),
        CheckConstraint(
            """
            (feature_type IN ('junction', 'device') AND GeometryType(geometry) = 'POINT')
            OR
            (feature_type = 'line' AND GeometryType(geometry) = 'LINESTRING')
            """,
            name="ck_network_features_geometry_matches_type",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_network_features_version_positive",
        ),
        Index(
            "ix_network_features_geometry",
            "geometry",
            postgresql_using="gist",
        ),
        {"schema": "utility_network"},
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    feeder_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "utility_network.feeders.id",
            name="fk_network_features_feeder",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    asset_code: Mapped[str] = mapped_column(String(100), nullable=False)
    feature_type: Mapped[FeatureType] = mapped_column(
        SAEnum(
            FeatureType,
            name="network_feature_type",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
            length=16,
        ),
        nullable=False,
    )
    geometry: Mapped[object] = mapped_column(
        Geometry(
            geometry_type="GEOMETRY",
            srid=4326,
            spatial_index=False,
        ),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    properties: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default=text("1"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    feeder: Mapped[Feeder] = relationship(
        "Feeder",
        back_populates="features",
    )
    outgoing_associations: Mapped[list[NetworkAssociation]] = relationship(
        "NetworkAssociation",
        foreign_keys=(
            "[NetworkAssociation.feeder_id, "
            "NetworkAssociation.from_feature_id]"
        ),
        viewonly=True,
    )
    incoming_associations: Mapped[list[NetworkAssociation]] = relationship(
        "NetworkAssociation",
        foreign_keys=(
            "[NetworkAssociation.feeder_id, "
            "NetworkAssociation.to_feature_id]"
        ),
        viewonly=True,
    )
```

Обновить `apps/backend/app/models/utility_network/__init__.py`:

```python
from .aoi import AOI
from .feeder import Feeder
from .network_feature import FeatureType, NetworkFeature

__all__ = ["AOI", "Feeder", "FeatureType", "NetworkFeature"]
```

- [ ] **Шаг 4: Запустить metadata-тест**

```powershell
pytest tests/test_network_model_metadata.py -q
```

Ожидается: collection все еще FAIL только из-за отсутствующей модели `NetworkAssociation`.

- [ ] **Шаг 5: Проверить форматирование файла**

```powershell
black --check models/utility_network tests/test_network_model_metadata.py
ruff check models/utility_network tests/test_network_model_metadata.py
```

Ожидается: обе команды завершаются с кодом `0`. Если Black требует изменения, выполнить:

```powershell
black models/utility_network tests/test_network_model_metadata.py
```

### Задача 3: Добавить NetworkAssociation И Завершить ORM Graph

**Files:**

- Modify: `apps/backend/app/tests/test_network_model_metadata.py`
- Modify: `apps/backend/app/models/utility_network/__init__.py`
- Create: `apps/backend/app/models/utility_network/network_association.py`
- Modify: `apps/backend/app/alembic/env.py`

- [ ] **Шаг 1: Добавить падающие metadata-тесты association**

Добавить импорт:

```python
from models.utility_network import AssociationType, NetworkAssociation
```

Добавить тесты:

```python
def test_association_type_values_are_stable_strings() -> None:
    assert {item.value for item in AssociationType} == {
        "connectivity",
        "containment",
        "attachment",
    }


def test_network_association_metadata_contains_all_guards() -> None:
    assert NetworkAssociation.__table__.schema == "utility_network"
    names = constraint_names(NetworkAssociation)
    assert {
        "fk_network_associations_feeder",
        "fk_network_associations_from_feature",
        "fk_network_associations_to_feature",
        "uq_network_associations_directed_edge",
        "ck_network_associations_no_self_reference",
        "ck_network_associations_version_positive",
    }.issubset(names)


def test_network_association_foreign_keys_use_restrict() -> None:
    foreign_keys = [
        constraint
        for constraint in NetworkAssociation.__table__.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    ]
    assert len(foreign_keys) == 3
    assert {
        element.ondelete
        for constraint in foreign_keys
        for element in constraint.elements
    } == {"RESTRICT"}
    assert {
        element.target_fullname
        for constraint in foreign_keys
        for element in constraint.elements
    } == {
        "utility_network.feeders.id",
        "utility_network.network_features.feeder_id",
        "utility_network.network_features.id",
    }


def test_network_relationships_do_not_delete_children_in_orm() -> None:
    configure_mappers()
    assert "delete" not in Feeder.features.property.cascade
    assert "delete" not in Feeder.associations.property.cascade
    assert NetworkFeature.outgoing_associations.property.viewonly is True
    assert NetworkFeature.incoming_associations.property.viewonly is True


def test_utility_network_package_exports_complete_public_contract() -> None:
    from models import utility_network

    assert set(utility_network.__all__) == {
        "AOI",
        "AssociationType",
        "Feeder",
        "FeatureType",
        "NetworkAssociation",
        "NetworkFeature",
    }
```

- [ ] **Шаг 2: Запустить тест и подтвердить падение**

```powershell
pytest tests/test_network_model_metadata.py -q
```

Ожидается: FAIL, потому что `AssociationType` и `NetworkAssociation` еще не
экспортируются из `models.utility_network`.

- [ ] **Шаг 3: Реализовать NetworkAssociation**

Создать `apps/backend/app/models/utility_network/network_association.py`:

```python
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base

if TYPE_CHECKING:
    from .feeder import Feeder
    from .network_feature import NetworkFeature


class AssociationType(str, enum.Enum):
    CONNECTIVITY = "connectivity"
    CONTAINMENT = "containment"
    ATTACHMENT = "attachment"


class NetworkAssociation(Base):
    __tablename__ = "network_associations"
    __table_args__ = (
        ForeignKeyConstraint(
            ["feeder_id", "from_feature_id"],
            [
                "utility_network.network_features.feeder_id",
                "utility_network.network_features.id",
            ],
            name="fk_network_associations_from_feature",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["feeder_id", "to_feature_id"],
            [
                "utility_network.network_features.feeder_id",
                "utility_network.network_features.id",
            ],
            name="fk_network_associations_to_feature",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "feeder_id",
            "from_feature_id",
            "to_feature_id",
            "association_type",
            name="uq_network_associations_directed_edge",
        ),
        CheckConstraint(
            "from_feature_id <> to_feature_id",
            name="ck_network_associations_no_self_reference",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_network_associations_version_positive",
        ),
        {"schema": "utility_network"},
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    feeder_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "utility_network.feeders.id",
            name="fk_network_associations_feeder",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    from_feature_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
    )
    to_feature_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
    )
    association_type: Mapped[AssociationType] = mapped_column(
        SAEnum(
            AssociationType,
            name="network_association_type",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
            length=16,
        ),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default=text("1"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    feeder: Mapped[Feeder] = relationship(
        "Feeder",
        back_populates="associations",
    )
    from_feature: Mapped[NetworkFeature] = relationship(
        "NetworkFeature",
        foreign_keys=[feeder_id, from_feature_id],
        viewonly=True,
    )
    to_feature: Mapped[NetworkFeature] = relationship(
        "NetworkFeature",
        foreign_keys=[feeder_id, to_feature_id],
        viewonly=True,
    )
```

Обновить `apps/backend/app/models/utility_network/__init__.py`:

```python
from .aoi import AOI
from .feeder import Feeder
from .network_association import AssociationType, NetworkAssociation
from .network_feature import FeatureType, NetworkFeature

__all__ = [
    "AOI",
    "AssociationType",
    "Feeder",
    "FeatureType",
    "NetworkAssociation",
    "NetworkFeature",
]
```

- [ ] **Шаг 4: Импортировать новые модели в Alembic metadata**

В `apps/backend/app/alembic/env.py` сразу после импорта `Base` добавить полный
набор model imports. Это не дает будущему autogenerate ошибочно считать
существующие legacy-таблицы удаленными:

```python
from models.feature_line import FeatureLine  # noqa: E402, F401
from models.feature_multiline import FeatureMultiLine  # noqa: E402, F401
from models.feature_multipoint import FeatureMultiPoint  # noqa: E402, F401
from models.feature_multipolygon import FeatureMultiPolygon  # noqa: E402, F401
from models.feature_point import FeaturePoint  # noqa: E402, F401
from models.feature_polygon import FeaturePolygon  # noqa: E402, F401
from models.layer import Layer  # noqa: E402, F401
from models.user import User  # noqa: E402, F401
from models.utility_network import (  # noqa: E402, F401
    AOI,
    AssociationType,
    Feeder,
    FeatureType,
    NetworkAssociation,
    NetworkFeature,
)
```

Импорты должны располагаться до:

```python
target_metadata = Base.metadata
```

В обоих вызовах `context.configure` добавить:

```python
include_schemas=True,
```

Это требуется и для offline, и для online migration paths.

- [ ] **Шаг 5: Запустить metadata-тест и весь unit suite**

```powershell
pytest tests/test_network_model_metadata.py -q
pytest -q
```

Ожидается: metadata-тест проходит; весь существующий suite также проходит без обращения к PostgreSQL.

- [ ] **Шаг 6: Выполнить quality checks ORM-файлов**

```powershell
black --check models/utility_network tests/test_network_model_metadata.py alembic/env.py
ruff check models/utility_network tests/test_network_model_metadata.py alembic/env.py
```

Ожидается: обе команды проходят.

### Задача 4: Добавить Управляемую Alembic-Миграцию

**Files:**

- Create: `apps/backend/app/alembic/versions/d3a01f4e9c21_network_model.py`

- [ ] **Шаг 1: Создать migration skeleton с фиксированной revision**

Создать `apps/backend/app/alembic/versions/d3a01f4e9c21_network_model.py`:

```python
"""add utility network model

Revision ID: d3a01f4e9c21
Revises: b82a5f2d91c3
"""

from typing import Sequence, Union

from alembic import op
import geoalchemy2
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "d3a01f4e9c21"
down_revision: Union[str, Sequence[str], None] = "b82a5f2d91c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
```

- [ ] **Шаг 2: Реализовать создание `aois` и `feeders`**

Добавить в `upgrade()`:

```python
def upgrade() -> None:
    op.execute(sa.text("CREATE SCHEMA utility_network"))

    op.create_table(
        "aois",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "geometry",
            geoalchemy2.Geometry(
                geometry_type="GEOMETRY",
                srid=4326,
                spatial_index=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "NOT ST_IsEmpty(geometry)",
            name="ck_aois_geometry_not_empty",
        ),
        sa.CheckConstraint(
            "ST_IsValid(geometry)",
            name="ck_aois_geometry_valid",
        ),
        sa.CheckConstraint(
            "ST_SRID(geometry) = 4326",
            name="ck_aois_geometry_srid",
        ),
        sa.CheckConstraint(
            "GeometryType(geometry) IN ('POLYGON', 'MULTIPOLYGON')",
            name="ck_aois_geometry_type",
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="utility_network",
    )
    op.create_index(
        "ix_aois_geometry",
        "aois",
        ["geometry"],
        unique=False,
        schema="utility_network",
        postgresql_using="gist",
    )

    op.create_table(
        "feeders",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_feeders_code"),
        schema="utility_network",
    )
```

- [ ] **Шаг 3: Добавить создание `network_features`**

Продолжить `upgrade()`:

```python
    op.create_table(
        "network_features",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("feeder_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_code", sa.String(length=100), nullable=False),
        sa.Column(
            "feature_type",
            sa.Enum(
                "junction",
                "line",
                "device",
                name="network_feature_type",
                native_enum=False,
                create_constraint=True,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column(
            "geometry",
            geoalchemy2.Geometry(
                geometry_type="GEOMETRY",
                srid=4326,
                spatial_index=False,
            ),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "properties",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "version",
            sa.Integer(),
            server_default=sa.text("1"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "NOT ST_IsEmpty(geometry)",
            name="ck_network_features_geometry_not_empty",
        ),
        sa.CheckConstraint(
            "ST_IsValid(geometry)",
            name="ck_network_features_geometry_valid",
        ),
        sa.CheckConstraint(
            "ST_SRID(geometry) = 4326",
            name="ck_network_features_geometry_srid",
        ),
        sa.CheckConstraint(
            """
            (feature_type IN ('junction', 'device') AND GeometryType(geometry) = 'POINT')
            OR
            (feature_type = 'line' AND GeometryType(geometry) = 'LINESTRING')
            """,
            name="ck_network_features_geometry_matches_type",
        ),
        sa.CheckConstraint(
            "version >= 1",
            name="ck_network_features_version_positive",
        ),
        sa.ForeignKeyConstraint(
            ["feeder_id"],
            ["utility_network.feeders.id"],
            name="fk_network_features_feeder",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "feeder_id",
            "asset_code",
            name="uq_network_features_feeder_asset_code",
        ),
        sa.UniqueConstraint(
            "feeder_id",
            "id",
            name="uq_network_features_feeder_id_id",
        ),
        schema="utility_network",
    )
    op.create_index(
        "ix_network_features_geometry",
        "network_features",
        ["geometry"],
        unique=False,
        schema="utility_network",
        postgresql_using="gist",
    )
```

- [ ] **Шаг 4: Добавить создание `network_associations`**

Продолжить `upgrade()`:

```python
    op.create_table(
        "network_associations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("feeder_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("from_feature_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("to_feature_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "association_type",
            sa.Enum(
                "connectivity",
                "containment",
                "attachment",
                name="network_association_type",
                native_enum=False,
                create_constraint=True,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column(
            "version",
            sa.Integer(),
            server_default=sa.text("1"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "from_feature_id <> to_feature_id",
            name="ck_network_associations_no_self_reference",
        ),
        sa.CheckConstraint(
            "version >= 1",
            name="ck_network_associations_version_positive",
        ),
        sa.ForeignKeyConstraint(
            ["feeder_id"],
            ["utility_network.feeders.id"],
            name="fk_network_associations_feeder",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["feeder_id", "from_feature_id"],
            [
                "utility_network.network_features.feeder_id",
                "utility_network.network_features.id",
            ],
            name="fk_network_associations_from_feature",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["feeder_id", "to_feature_id"],
            [
                "utility_network.network_features.feeder_id",
                "utility_network.network_features.id",
            ],
            name="fk_network_associations_to_feature",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "feeder_id",
            "from_feature_id",
            "to_feature_id",
            "association_type",
            name="uq_network_associations_directed_edge",
        ),
        schema="utility_network",
    )
```

- [ ] **Шаг 5: Реализовать downgrade в обратном порядке**

Добавить:

```python
def downgrade() -> None:
    op.drop_table("network_associations", schema="utility_network")
    op.drop_index(
        "ix_network_features_geometry",
        table_name="network_features",
        schema="utility_network",
    )
    op.drop_table("network_features", schema="utility_network")
    op.drop_table("feeders", schema="utility_network")
    op.drop_index(
        "ix_aois_geometry",
        table_name="aois",
        schema="utility_network",
    )
    op.drop_table("aois", schema="utility_network")
    op.execute(sa.text("DROP SCHEMA utility_network"))
```

- [ ] **Шаг 6: Проверить единственную голову Alembic**

Из `apps/backend/app`:

```powershell
alembic heads
alembic history
```

Ожидается: единственная голова `d3a01f4e9c21 (head)`; ее предок —
`b82a5f2d91c3`.

- [ ] **Шаг 7: Выполнить чистый migration smoke**

Из корня репозитория:

```powershell
docker compose -f infra/docker-compose.yml down -v
docker compose -f infra/docker-compose.yml up -d postgis
docker compose -f infra/docker-compose.yml --profile migrate up --build --abort-on-container-exit migrate
docker compose -f infra/docker-compose.yml exec -T postgis psql -U postgres -d geo -c "SELECT schemaname, tablename FROM pg_tables WHERE schemaname='utility_network' ORDER BY tablename;"
```

Ожидается: migration service завершается с кодом `0`; запрос возвращает четыре
таблицы в schema `utility_network`.

### Задача 5: Добавить PostgreSQL/PostGIS Integration Tests

**Files:**

- Create: `apps/backend/app/tests/network_db_support.py`
- Create: `apps/backend/app/tests/test_network_model_integration.py`

- [ ] **Шаг 1: Создать DB test helper**

Создать `apps/backend/app/tests/network_db_support.py`:

```python
import asyncio
import os
from collections.abc import Awaitable, Callable

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine


DB_TESTS_ENABLED = os.getenv("RUN_DB_TESTS") == "1"


def require_db_tests() -> None:
    if not DB_TESTS_ENABLED:
        pytest.skip("Установите RUN_DB_TESTS=1 для PostgreSQL/PostGIS tests.")


def run_in_rollback_transaction(
    scenario: Callable[[AsyncSession], Awaitable[None]],
) -> None:
    require_db_tests()

    async def run() -> None:
        engine = create_async_engine(os.environ["DATABASE_URL"])
        try:
            async with engine.connect() as connection:
                transaction = await connection.begin()
                session = AsyncSession(
                    bind=connection,
                    expire_on_commit=False,
                )
                try:
                    await scenario(session)
                finally:
                    if session.in_transaction():
                        await session.rollback()
                    await session.close()
                    if transaction.is_active:
                        await transaction.rollback()
        finally:
            await engine.dispose()

    asyncio.run(run())
```

- [ ] **Шаг 2: Написать happy-path и defaults tests**

Создать `apps/backend/app/tests/test_network_model_integration.py`:

```python
from uuid import uuid4

import pytest
from geoalchemy2.elements import WKTElement
from sqlalchemy import delete, text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models.utility_network import (
    AOI,
    AssociationType,
    Feeder,
    FeatureType,
    NetworkAssociation,
    NetworkFeature,
)
from tests.network_db_support import run_in_rollback_transaction


def point(x: float, y: float, srid: int = 4326) -> WKTElement:
    return WKTElement(f"POINT ({x} {y})", srid=srid)


def line(srid: int = 4326) -> WKTElement:
    return WKTElement("LINESTRING (0 0, 1 1)", srid=srid)


def polygon() -> WKTElement:
    return WKTElement(
        "POLYGON ((0 0, 0 2, 2 2, 2 0, 0 0))",
        srid=4326,
    )


def multipolygon() -> WKTElement:
    return WKTElement(
        "MULTIPOLYGON (((0 0, 0 2, 2 2, 2 0, 0 0)))",
        srid=4326,
    )


async def create_feeder(session: AsyncSession, code: str) -> Feeder:
    feeder = Feeder(code=code, name=f"Фидер {code}")
    session.add(feeder)
    await session.flush()
    return feeder


async def create_feature(
    session: AsyncSession,
    feeder: Feeder,
    asset_code: str,
    feature_type: FeatureType,
    geometry: WKTElement,
) -> NetworkFeature:
    feature = NetworkFeature(
        feeder_id=feeder.id,
        asset_code=asset_code,
        feature_type=feature_type,
        geometry=geometry,
        name=asset_code,
    )
    session.add(feature)
    await session.flush()
    return feature


def test_valid_network_graph_and_defaults_are_persisted() -> None:
    async def scenario(session: AsyncSession) -> None:
        aoi = AOI(name="Рабочая зона", geometry=polygon())
        feeder = await create_feeder(session, "F-001")
        junction = await create_feature(
            session,
            feeder,
            "J-001",
            FeatureType.JUNCTION,
            point(0, 0),
        )
        line_feature = await create_feature(
            session,
            feeder,
            "L-001",
            FeatureType.LINE,
            line(),
        )
        association = NetworkAssociation(
            feeder_id=feeder.id,
            from_feature_id=junction.id,
            to_feature_id=line_feature.id,
            association_type=AssociationType.CONNECTIVITY,
        )
        session.add_all([aoi, association])
        await session.flush()
        await session.refresh(feeder)
        await session.refresh(junction)
        await session.refresh(association)

        assert feeder.is_active is True
        assert junction.properties == {}
        assert junction.version == 1
        assert association.version == 1

    run_in_rollback_transaction(scenario)


def test_utility_tables_are_isolated_from_public_schema() -> None:
    async def scenario(session: AsyncSession) -> None:
        result = await session.execute(
            text(
                """
                SELECT schemaname, tablename
                FROM pg_tables
                WHERE tablename IN (
                    'aois',
                    'feeders',
                    'network_features',
                    'network_associations'
                )
                ORDER BY schemaname, tablename
                """
            )
        )
        assert set(result) == {
            ("utility_network", "aois"),
            ("utility_network", "feeders"),
            ("utility_network", "network_associations"),
            ("utility_network", "network_features"),
        }

    run_in_rollback_transaction(scenario)


def test_search_path_is_not_changed_for_utility_schema() -> None:
    async def scenario(session: AsyncSession) -> None:
        search_path = await session.scalar(text("SHOW search_path"))
        assert "utility_network" not in search_path

    run_in_rollback_transaction(scenario)


@pytest.mark.parametrize("geometry", [polygon(), multipolygon()])
def test_aoi_accepts_polygon_and_multipolygon(geometry: WKTElement) -> None:
    async def scenario(session: AsyncSession) -> None:
        session.add(AOI(name="AOI", geometry=geometry))
        await session.flush()

    run_in_rollback_transaction(scenario)
```

- [ ] **Шаг 3: Добавить geometry rejection tests**

Продолжить файл:

```python
@pytest.mark.parametrize(
    ("feature_type", "geometry"),
    [
        (FeatureType.JUNCTION, line()),
        (FeatureType.DEVICE, line()),
        (FeatureType.LINE, point(0, 0)),
    ],
)
def test_feature_type_rejects_incompatible_geometry(
    feature_type: FeatureType,
    geometry: WKTElement,
) -> None:
    async def scenario(session: AsyncSession) -> None:
        feeder = await create_feeder(session, f"F-{uuid4()}")
        session.add(
            NetworkFeature(
                feeder_id=feeder.id,
                asset_code="X-001",
                feature_type=feature_type,
                geometry=geometry,
                name="Некорректная геометрия",
            )
        )
        with pytest.raises(IntegrityError):
            await session.flush()

    run_in_rollback_transaction(scenario)


@pytest.mark.parametrize(
    "geometry",
    [
        WKTElement("POINT EMPTY", srid=4326),
        WKTElement("POINT (0 0)", srid=3857),
    ],
)
def test_network_feature_rejects_empty_or_wrong_srid_geometry(
    geometry: WKTElement,
) -> None:
    async def scenario(session: AsyncSession) -> None:
        feeder = await create_feeder(session, f"F-{uuid4()}")
        session.add(
            NetworkFeature(
                feeder_id=feeder.id,
                asset_code="J-001",
                feature_type=FeatureType.JUNCTION,
                geometry=geometry,
                name="Некорректный объект",
            )
        )
        with pytest.raises(DBAPIError):
            await session.flush()

    run_in_rollback_transaction(scenario)


def test_aoi_rejects_invalid_polygon() -> None:
    async def scenario(session: AsyncSession) -> None:
        invalid = WKTElement(
            "POLYGON ((0 0, 2 2, 0 2, 2 0, 0 0))",
            srid=4326,
        )
        session.add(AOI(name="Некорректная AOI", geometry=invalid))
        with pytest.raises(IntegrityError):
            await session.flush()

    run_in_rollback_transaction(scenario)


@pytest.mark.parametrize(
    "geometry",
    [
        WKTElement("POLYGON EMPTY", srid=4326),
        WKTElement(
            "POLYGON ((0 0, 0 2, 2 2, 2 0, 0 0))",
            srid=3857,
        ),
    ],
)
def test_aoi_rejects_empty_or_wrong_srid_geometry(
    geometry: WKTElement,
) -> None:
    async def scenario(session: AsyncSession) -> None:
        session.add(AOI(name="Некорректная AOI", geometry=geometry))
        with pytest.raises(DBAPIError):
            await session.flush()

    run_in_rollback_transaction(scenario)
```

- [ ] **Шаг 4: Добавить uniqueness, association и RESTRICT tests**

Продолжить файл:

```python
def test_asset_code_is_unique_only_inside_feeder() -> None:
    async def scenario(session: AsyncSession) -> None:
        first = await create_feeder(session, "F-101")
        second = await create_feeder(session, "F-102")
        await create_feature(
            session,
            first,
            "J-001",
            FeatureType.JUNCTION,
            point(0, 0),
        )
        await create_feature(
            session,
            second,
            "J-001",
            FeatureType.JUNCTION,
            point(1, 1),
        )
        duplicate = NetworkFeature(
            feeder_id=first.id,
            asset_code="J-001",
            feature_type=FeatureType.JUNCTION,
            geometry=point(2, 2),
            name="Дубль",
        )
        session.add(duplicate)
        with pytest.raises(IntegrityError):
            await session.flush()

    run_in_rollback_transaction(scenario)


def test_association_rejects_self_reference() -> None:
    async def scenario(session: AsyncSession) -> None:
        feeder = await create_feeder(session, "F-201")
        first = await create_feature(
            session,
            feeder,
            "J-001",
            FeatureType.JUNCTION,
            point(0, 0),
        )
        second = await create_feature(
            session,
            feeder,
            "J-002",
            FeatureType.JUNCTION,
            point(1, 1),
        )

        self_reference = NetworkAssociation(
            feeder_id=feeder.id,
            from_feature_id=first.id,
            to_feature_id=first.id,
            association_type=AssociationType.CONNECTIVITY,
        )
        session.add(self_reference)
        with pytest.raises(IntegrityError):
            await session.flush()

    run_in_rollback_transaction(scenario)


def test_association_rejects_exact_directed_duplicate() -> None:
    async def scenario(session: AsyncSession) -> None:
        feeder = await create_feeder(session, "F-202")
        first = await create_feature(
            session,
            feeder,
            "J-001",
            FeatureType.JUNCTION,
            point(0, 0),
        )
        second = await create_feature(
            session,
            feeder,
            "J-002",
            FeatureType.JUNCTION,
            point(1, 1),
        )
        session.add(
            NetworkAssociation(
                feeder_id=feeder.id,
                from_feature_id=first.id,
                to_feature_id=second.id,
                association_type=AssociationType.CONNECTIVITY,
            )
        )
        await session.flush()
        session.add(
            NetworkAssociation(
                feeder_id=feeder.id,
                from_feature_id=first.id,
                to_feature_id=second.id,
                association_type=AssociationType.CONNECTIVITY,
            )
        )
        with pytest.raises(IntegrityError):
            await session.flush()

    run_in_rollback_transaction(scenario)


def test_reverse_association_is_allowed() -> None:
    async def scenario(session: AsyncSession) -> None:
        feeder = await create_feeder(session, "F-203")
        first = await create_feature(
            session,
            feeder,
            "J-001",
            FeatureType.JUNCTION,
            point(0, 0),
        )
        second = await create_feature(
            session,
            feeder,
            "J-002",
            FeatureType.JUNCTION,
            point(1, 1),
        )
        session.add_all(
            [
                NetworkAssociation(
                    feeder_id=feeder.id,
                    from_feature_id=first.id,
                    to_feature_id=second.id,
                    association_type=AssociationType.CONNECTIVITY,
                ),
                NetworkAssociation(
                    feeder_id=feeder.id,
                    from_feature_id=second.id,
                    to_feature_id=first.id,
                    association_type=AssociationType.CONNECTIVITY,
                ),
            ]
        )
        await session.flush()

    run_in_rollback_transaction(scenario)


def test_cross_feeder_association_is_rejected() -> None:
    async def scenario(session: AsyncSession) -> None:
        first_feeder = await create_feeder(session, "F-204")
        second_feeder = await create_feeder(session, "F-205")
        first = await create_feature(
            session,
            first_feeder,
            "J-001",
            FeatureType.JUNCTION,
            point(0, 0),
        )
        second = await create_feature(
            session,
            second_feeder,
            "J-001",
            FeatureType.JUNCTION,
            point(1, 1),
        )
        session.add(
            NetworkAssociation(
                feeder_id=first_feeder.id,
                from_feature_id=first.id,
                to_feature_id=second.id,
                association_type=AssociationType.CONNECTIVITY,
            )
        )
        with pytest.raises(IntegrityError):
            await session.flush()

    run_in_rollback_transaction(scenario)


def test_association_with_missing_endpoint_is_rejected() -> None:
    async def scenario(session: AsyncSession) -> None:
        feeder = await create_feeder(session, "F-206")
        first = await create_feature(
            session,
            feeder,
            "J-001",
            FeatureType.JUNCTION,
            point(0, 0),
        )
        session.add(
            NetworkAssociation(
                feeder_id=feeder.id,
                from_feature_id=first.id,
                to_feature_id=uuid4(),
                association_type=AssociationType.CONNECTIVITY,
            )
        )
        with pytest.raises(IntegrityError):
            await session.flush()

    run_in_rollback_transaction(scenario)


def test_feature_version_must_be_positive() -> None:
    async def scenario(session: AsyncSession) -> None:
        feeder = await create_feeder(session, "F-301")
        session.add(
            NetworkFeature(
                feeder_id=feeder.id,
                asset_code="J-001",
                feature_type=FeatureType.JUNCTION,
                geometry=point(0, 0),
                name="Версия 0",
                version=0,
            )
        )
        with pytest.raises(IntegrityError):
            await session.flush()

    run_in_rollback_transaction(scenario)


def test_association_version_must_be_positive() -> None:
    async def scenario(session: AsyncSession) -> None:
        feeder = await create_feeder(session, "F-302")
        first = await create_feature(
            session,
            feeder,
            "J-001",
            FeatureType.JUNCTION,
            point(0, 0),
        )
        second = await create_feature(
            session,
            feeder,
            "J-002",
            FeatureType.JUNCTION,
            point(1, 1),
        )
        session.add(
            NetworkAssociation(
                feeder_id=feeder.id,
                from_feature_id=first.id,
                to_feature_id=second.id,
                association_type=AssociationType.CONNECTIVITY,
                version=0,
            )
        )
        with pytest.raises(IntegrityError):
            await session.flush()

    run_in_rollback_transaction(scenario)


def test_delete_restricts_non_empty_feeder() -> None:
    async def scenario(session: AsyncSession) -> None:
        feeder = await create_feeder(session, "F-401")
        await create_feature(
            session,
            feeder,
            "J-001",
            FeatureType.JUNCTION,
            point(0, 0),
        )
        with pytest.raises(IntegrityError):
            await session.execute(delete(Feeder).where(Feeder.id == feeder.id))
            await session.flush()

    run_in_rollback_transaction(scenario)


def test_delete_restricts_feature_used_by_association() -> None:
    async def scenario(session: AsyncSession) -> None:
        feeder = await create_feeder(session, "F-402")
        first = await create_feature(
            session,
            feeder,
            "J-001",
            FeatureType.JUNCTION,
            point(0, 0),
        )
        second = await create_feature(
            session,
            feeder,
            "J-002",
            FeatureType.JUNCTION,
            point(1, 1),
        )
        session.add(
            NetworkAssociation(
                feeder_id=feeder.id,
                from_feature_id=first.id,
                to_feature_id=second.id,
                association_type=AssociationType.CONNECTIVITY,
            )
        )
        await session.flush()

        with pytest.raises(IntegrityError):
            await session.execute(
                delete(NetworkFeature).where(NetworkFeature.id == first.id)
            )
            await session.flush()

    run_in_rollback_transaction(scenario)
```

- [ ] **Шаг 5: Запустить DB tests внутри Compose**

Из корня репозитория:

```powershell
docker compose -f infra/docker-compose.yml up -d --build postgis backend
docker compose -f infra/docker-compose.yml exec -T backend env RUN_DB_TESTS=1 pytest tests/test_network_model_integration.py -q
```

Ожидается: все integration tests проходят. Обычный запуск без флага:

```powershell
docker compose -f infra/docker-compose.yml exec -T backend pytest tests/test_network_model_integration.py -q
```

Ожидается: tests пропущены с понятным сообщением, а не падают из-за отсутствия
настройки.

### Задача 6: Добавить Migration Cycle Test И CI Gate

**Files:**

- Create: `apps/backend/app/tests/test_network_model_migration.py`
- Modify: `.github/workflows/ci.yml`

- [ ] **Шаг 1: Написать migration cycle test**

Создать `apps/backend/app/tests/test_network_model_migration.py`:

```python
import asyncio
import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from tests.network_db_support import require_db_tests


APP_ROOT = Path(__file__).resolve().parent.parent
PREVIOUS_REVISION = "b82a5f2d91c3"
NETWORK_REVISION = "d3a01f4e9c21"
NETWORK_TABLES = {
    "aois",
    "feeders",
    "network_features",
    "network_associations",
}
NETWORK_SCHEMA = "utility_network"
REQUIRED_CONSTRAINTS = {
    "fk_network_features_feeder",
    "uq_network_features_feeder_asset_code",
    "fk_network_associations_from_feature",
    "fk_network_associations_to_feature",
    "uq_network_associations_directed_edge",
    "ck_network_associations_no_self_reference",
}
REQUIRED_INDEXES = {
    "ix_aois_geometry",
    "ix_network_features_geometry",
}
EXPECTED_SPATIAL_INDEXES = {
    ("aois", "geometry"): "ix_aois_geometry",
    ("network_features", "geometry"): "ix_network_features_geometry",
}


def alembic_config() -> Config:
    return Config(str(APP_ROOT / "alembic.ini"))


def read_network_tables() -> set[str]:
    async def read() -> set[str]:
        engine = create_async_engine(os.environ["DATABASE_URL"])
        try:
            async with engine.connect() as connection:
                result = await connection.execute(
                    text(
                        """
                        SELECT tablename
                        FROM pg_tables
                        WHERE schemaname = :schema_name
                          AND tablename IN (
                              :aoi_table,
                              :feeder_table,
                              :feature_table,
                              :association_table
                          )
                        """
                    ),
                    {
                        "schema_name": NETWORK_SCHEMA,
                        "aoi_table": "aois",
                        "feeder_table": "feeders",
                        "feature_table": "network_features",
                        "association_table": "network_associations",
                    },
                )
                return set(result.scalars())
        finally:
            await engine.dispose()

    return asyncio.run(read())


def schema_exists() -> bool:
    async def read() -> bool:
        engine = create_async_engine(os.environ["DATABASE_URL"])
        try:
            async with engine.connect() as connection:
                return bool(
                    await connection.scalar(
                        text(
                            """
                            SELECT EXISTS (
                                SELECT 1
                                FROM pg_namespace
                                WHERE nspname = :schema_name
                            )
                            """
                        ),
                        {"schema_name": NETWORK_SCHEMA},
                    )
                )
        finally:
            await engine.dispose()

    return asyncio.run(read())


def read_public_name_collisions() -> set[str]:
    async def read() -> set[str]:
        engine = create_async_engine(os.environ["DATABASE_URL"])
        try:
            async with engine.connect() as connection:
                result = await connection.execute(
                    text(
                        """
                        SELECT tablename
                        FROM pg_tables
                        WHERE schemaname = 'public'
                          AND tablename IN (
                              :aoi_table,
                              :feeder_table,
                              :feature_table,
                              :association_table
                          )
                        """
                    ),
                    {
                        "aoi_table": "aois",
                        "feeder_table": "feeders",
                        "feature_table": "network_features",
                        "association_table": "network_associations",
                    },
                )
                return set(result.scalars())
        finally:
            await engine.dispose()

    return asyncio.run(read())


def read_network_constraints() -> set[str]:
    async def read() -> set[str]:
        engine = create_async_engine(os.environ["DATABASE_URL"])
        try:
            async with engine.connect() as connection:
                result = await connection.execute(
                    text(
                        """
                        SELECT conname
                        FROM pg_constraint AS constraint_info
                        JOIN pg_class AS table_info
                          ON table_info.oid = constraint_info.conrelid
                        JOIN pg_namespace AS schema_info
                          ON schema_info.oid = table_info.relnamespace
                        WHERE schema_info.nspname = :schema_name
                        """
                    ),
                    {"schema_name": NETWORK_SCHEMA},
                )
                return set(result.scalars())
        finally:
            await engine.dispose()

    return asyncio.run(read())


def read_network_indexes() -> set[str]:
    async def read() -> set[str]:
        engine = create_async_engine(os.environ["DATABASE_URL"])
        try:
            async with engine.connect() as connection:
                result = await connection.execute(
                    text(
                        """
                        SELECT indexname
                        FROM pg_indexes
                        WHERE schemaname = :schema_name
                        """
                    ),
                    {"schema_name": NETWORK_SCHEMA},
                )
                return set(result.scalars())
        finally:
            await engine.dispose()

    return asyncio.run(read())


def read_geometry_gist_indexes() -> dict[tuple[str, str], list[str]]:
    async def read() -> dict[tuple[str, str], list[str]]:
        engine = create_async_engine(os.environ["DATABASE_URL"])
        try:
            async with engine.connect() as connection:
                result = await connection.execute(
                    text(
                        """
                        SELECT
                            table_info.relname AS table_name,
                            attribute_info.attname AS column_name,
                            index_info.relname AS index_name
                        FROM pg_index AS index_metadata
                        JOIN pg_class AS table_info
                          ON table_info.oid = index_metadata.indrelid
                        JOIN pg_namespace AS schema_info
                          ON schema_info.oid = table_info.relnamespace
                        JOIN pg_class AS index_info
                          ON index_info.oid = index_metadata.indexrelid
                        JOIN pg_am AS access_method
                          ON access_method.oid = index_info.relam
                        JOIN LATERAL unnest(index_metadata.indkey)
                          WITH ORDINALITY AS indexed_column(attnum, position)
                          ON true
                        JOIN pg_attribute AS attribute_info
                          ON attribute_info.attrelid = table_info.oid
                         AND attribute_info.attnum = indexed_column.attnum
                        WHERE schema_info.nspname = :schema_name
                          AND access_method.amname = 'gist'
                          AND table_info.relname IN ('aois', 'network_features')
                          AND attribute_info.attname = 'geometry'
                        ORDER BY table_info.relname, index_info.relname
                        """
                    ),
                    {"schema_name": NETWORK_SCHEMA},
                )
                indexes: dict[tuple[str, str], list[str]] = {}
                for table_name, column_name, index_name in result:
                    indexes.setdefault((table_name, column_name), []).append(
                        index_name
                    )
                return indexes
        finally:
            await engine.dispose()

    return asyncio.run(read())


def assert_exactly_one_geometry_gist_index() -> None:
    indexes = read_geometry_gist_indexes()
    assert set(indexes) == set(EXPECTED_SPATIAL_INDEXES)
    for target, expected_name in EXPECTED_SPATIAL_INDEXES.items():
        assert indexes[target] == [expected_name]


def read_search_path() -> str:
    async def read() -> str:
        engine = create_async_engine(os.environ["DATABASE_URL"])
        try:
            async with engine.connect() as connection:
                return str(await connection.scalar(text("SHOW search_path")))
        finally:
            await engine.dispose()

    return asyncio.run(read())


def test_network_migration_upgrade_downgrade_upgrade_cycle() -> None:
    require_db_tests()
    config = alembic_config()

    try:
        command.downgrade(config, PREVIOUS_REVISION)
        assert schema_exists() is False
        assert read_network_tables() == set()

        command.upgrade(config, NETWORK_REVISION)
        assert schema_exists() is True
        assert read_network_tables() == NETWORK_TABLES
        assert read_public_name_collisions() == set()
        assert REQUIRED_CONSTRAINTS.issubset(read_network_constraints())
        assert REQUIRED_INDEXES.issubset(read_network_indexes())
        assert_exactly_one_geometry_gist_index()
        assert NETWORK_SCHEMA not in read_search_path()

        command.downgrade(config, PREVIOUS_REVISION)
        assert schema_exists() is False
        assert read_network_tables() == set()

        command.upgrade(config, NETWORK_REVISION)
        assert schema_exists() is True
        assert read_network_tables() == NETWORK_TABLES
        assert read_public_name_collisions() == set()
        assert REQUIRED_CONSTRAINTS.issubset(read_network_constraints())
        assert REQUIRED_INDEXES.issubset(read_network_indexes())
        assert_exactly_one_geometry_gist_index()
        assert NETWORK_SCHEMA not in read_search_path()
    finally:
        command.upgrade(config, "head")
```

- [ ] **Шаг 2: Запустить migration cycle локально в Compose**

```powershell
docker compose -f infra/docker-compose.yml exec -T backend env RUN_DB_TESTS=1 pytest tests/test_network_model_migration.py -q
docker compose -f infra/docker-compose.yml exec -T backend alembic current
```

Ожидается: test проходит; текущая revision после `finally` —
`d3a01f4e9c21 (head)`.

- [ ] **Шаг 3: Добавить DB tests в существующий CI smoke job**

В `.github/workflows/ci.yml` после шага `GET /health inside container` добавить:

```yaml
      - name: PostgreSQL/PostGIS network model tests
        working-directory: infra
        run: |
          docker compose -f docker-compose.yml exec -T backend env RUN_DB_TESTS=1 \
            pytest tests/test_network_model_integration.py -q
          docker compose -f docker-compose.yml exec -T backend env RUN_DB_TESTS=1 \
            pytest tests/test_network_model_migration.py -q
```

Не добавлять PostgreSQL service в `backend_test`: быстрый unit job остается
изолированным, а DB tests живут в уже существующем Compose smoke.

- [ ] **Шаг 4: Повторить локальный CI smoke**

```powershell
docker compose -f infra/docker-compose.yml down -v
docker compose -f infra/docker-compose.yml up -d --build postgis backend
docker compose -f infra/docker-compose.yml exec -T backend python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2); print('health ok')"
docker compose -f infra/docker-compose.yml exec -T backend env RUN_DB_TESTS=1 pytest tests/test_network_model_integration.py -q
docker compose -f infra/docker-compose.yml exec -T backend env RUN_DB_TESTS=1 pytest tests/test_network_model_migration.py -q
docker compose -f infra/docker-compose.yml down -v
```

Ожидается: health, integration tests и migration cycle проходят; teardown
удаляет test volume.

### Задача 7: Выполнить Финальную Проверку И Закрыть Документацию

**Files:**

- Modify: `docs/release_1/sprint_1/README.md`
- Verify: `docs/release_1/sprint_1/2026-06-14-sprint-1-day-3-network-model-design.md`
- Verify: `docs/release_1/sprint_1/2026-06-14-sprint-1-day-3-network-model-implementation-plan.md`

- [ ] **Шаг 1: Проверить implementation plan в индексе Спринта 1**

Убедиться, что в `docs/release_1/sprint_1/README.md` рядом с design Дня 3 сохранена строка:

```markdown
- [План реализации базовой модели сети Дня 3](2026-06-14-sprint-1-day-3-network-model-implementation-plan.md)
```

- [ ] **Шаг 2: Выполнить backend unit quality gates**

Из `apps/backend/app`:

```powershell
black --check .
ruff check .
pytest -q
```

Ожидается: все команды проходят; DB integration tests в обычном suite
пропускаются, если `RUN_DB_TESTS` не установлен.

- [ ] **Шаг 3: Выполнить полный DB verification**

Из корня репозитория:

```powershell
docker compose -f infra/docker-compose.yml down -v
docker compose -f infra/docker-compose.yml up -d --build postgis backend
docker compose -f infra/docker-compose.yml exec -T backend env RUN_DB_TESTS=1 pytest tests/test_network_model_integration.py tests/test_network_model_migration.py -q
docker compose -f infra/docker-compose.yml exec -T postgis psql -U postgres -d geo -c "SELECT schemaname, tablename FROM pg_tables WHERE schemaname IN ('public','utility_network') AND tablename IN ('aois','feeders','network_features','network_associations') ORDER BY schemaname, tablename;"
docker compose -f infra/docker-compose.yml exec -T postgis psql -U postgres -d geo -c "SELECT constraint_info.conname FROM pg_constraint AS constraint_info JOIN pg_class AS table_info ON table_info.oid=constraint_info.conrelid JOIN pg_namespace AS schema_info ON schema_info.oid=table_info.relnamespace WHERE schema_info.nspname='utility_network' ORDER BY constraint_info.conname;"
docker compose -f infra/docker-compose.yml exec -T postgis psql -U postgres -d geo -c "SELECT tablename, indexname, indexdef FROM pg_indexes WHERE schemaname='utility_network' AND indexdef ILIKE '%USING gist%' ORDER BY tablename, indexname;"
docker compose -f infra/docker-compose.yml exec -T postgis psql -U postgres -d geo -c "SHOW search_path;"
```

Ожидается: DB tests проходят; четыре таблицы существуют только в
`utility_network`; запрос показывает именованные FK, unique и CHECK constraints;
GiST-запрос возвращает ровно `ix_aois_geometry` и
`ix_network_features_geometry`, без автоматически созданных дублей;
`search_path` не содержит `utility_network`.

- [ ] **Шаг 4: Проверить Compose startup с новой миграцией**

```powershell
docker compose -f infra/docker-compose.yml restart backend
docker compose -f infra/docker-compose.yml exec -T backend alembic current
docker compose -f infra/docker-compose.yml exec -T backend python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2); print('health ok')"
```

Ожидается: повторный `alembic upgrade head` идемпотентен; revision остается
`d3a01f4e9c21`; backend healthy.

- [ ] **Шаг 5: Проверить необходимость repository-change ingest**

Сначала определить, содержит ли реализация новую durable technical knowledge,
которой нет в design, code или существующем `Code_wiki`.

- Если уникального знания нет, `/ingest repository-change` не запускать.
- Если обнаружена новая устойчивая operational constraint или неочевидная
  архитектурная причина, запустить `/ingest repository-change` через
  `.agents/skills/source-command-ingest/SKILL.md`.
- Ingest может менять только `Code_wiki`; code, migrations и tests он не меняет.

- [ ] **Шаг 6: Выполнить repository checks**

```powershell
git diff --check
git status --short
```

Если менялись `docs/agent-memory`, `AGENTS.md`, `CONTRIBUTING.md`,
`docs/knowledge-pipeline` или repo-local skills, дополнительно:

```powershell
python scripts/check-memory-needed.py --check
```

Ожидается: whitespace errors отсутствуют; изменены только ожидаемые файлы.

## Проверка Покрытия Design

- Пакет `models.utility_network` и публичные exports: Tasks 1-3.
- PostgreSQL schema `utility_network` создается и удаляется миграцией:
  Tasks 4 и 6.
- Явные schema-qualified ORM tables и FK без изменения `search_path`:
  Tasks 1-6.
- Отсутствие одноименных таблиц в `public`: Tasks 5-7.
- Защита от дублирования spatial indexes GeoAlchemy2 + Alembic: Tasks 1, 2,
  4, 6 и 7.
- Четыре отдельные таблицы и модели: Tasks 1-4.
- `AOI` как `Polygon | MultiPolygon`, SRID 4326: Tasks 1, 4, 5.
- `NetworkFeature` как `Point | LineString` с type matching: Tasks 2, 4, 5.
- `properties JSONB`, `name`, `description`, `version`: Tasks 2, 4, 5.
- Уникальность `(feeder_id, asset_code)`: Tasks 2, 4, 5.
- Candidate key `(feeder_id, id)`: Tasks 2 и 4.
- Directed associations, self-reference и exact duplicate guards: Tasks 3-5.
- Межфидерные association запрещены составными FK: Tasks 3-5.
- `RESTRICT` для feeder и связанных features: Tasks 2-5.
- ORM relationships без delete cascade: Tasks 1-3.
- Ненативные строковые enum: Tasks 2-4.
- Alembic upgrade/downgrade/re-upgrade: Tasks 4 и 6.
- Unit tests без обязательной БД: Tasks 1-3 и 7.
- PostgreSQL/PostGIS integration tests: Tasks 5-7.
- CI enforcement: Task 6.
- Seed и API явно вне scope: предусловия и граница scope.
