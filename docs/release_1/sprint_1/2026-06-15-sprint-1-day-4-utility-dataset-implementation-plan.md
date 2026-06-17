# План Реализации Utility Dataset И Read-Only Backend API Дня 4

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:subagent-driven-development` (recommended) or
> `superpowers:executing-plans` to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Создать атомарный create-once seed `synthetic_utility_feeder_01` и
защищенный read-only endpoint
`GET /api/v1/utility-network/feeders/{feederId}`, возвращающий полный feeder,
его associations и все пространственно пересекающиеся AOI.

**Architecture:** Вся seed-логика приложения изолирована в пакете `seeds` с
подпакетами `repositories`, `services`, `specs` и `runners`; имена seed-файлов
и классов имеют префикс `seed_` / `Seed`. `SeedUtilityDatasetService` создает
отсутствующий агрегат одной транзакцией и не изменяет существующий feeder.
Read path остается в runtime-слоях и разделен на `UtilityNetworkRepository`,
`UtilityNetworkService`, Pydantic DTO и отдельный FastAPI router; PostGIS
формирует GeoJSON и находит AOI через `ST_Intersects`. Repository загружает
feeder, features, associations и AOI за один SQL round trip с тремя независимыми
correlated JSONB subqueries, чтобы не создавать декартово размножение коллекций.

**Tech Stack:** Python 3.12, FastAPI 0.115, Pydantic 2.10, SQLAlchemy 2.0,
PostgreSQL 16, PostGIS 3.4, GeoAlchemy2, asyncpg, pytest, Docker Compose.

---

## Правило Работы С Git

В этом репозитории агент не выполняет `git add`, `git commit` и не создает
commit без отдельной прямой просьбы пользователя. Поэтому план не содержит
commit-шагов. После каждого task выполняются только тесты и
`git diff --check`; изменения остаются в working tree для пользовательской
проверки.

## Предусловия

- Design: `docs/release_1/sprint_1/2026-06-15-sprint-1-day-4-utility-dataset-design.md`.
- Модели День 3 уже существуют в `models.utility_network`.
- Миграция `d3a01f4e9c21` является текущим head и не изменяется.
- Generic `Layer`/feature API не используется как storage или API для
  utility dataset.
- `WorkOrder`, `EditVersion`, reset и workspace API не добавляются.
- Все application messages и logs пишутся на русском языке; API paths,
  JSON keys, enum values и error codes остаются на английском.

## Карта Файлов

### Dataset И Seed

- Create: `apps/backend/app/seeds/__init__.py`
- Create: `apps/backend/app/seeds/repositories/__init__.py`
- Create: `apps/backend/app/seeds/repositories/seed_user_repository.py`
- Create: `apps/backend/app/seeds/repositories/seed_utility_dataset_repository.py`
- Create: `apps/backend/app/seeds/services/__init__.py`
- Create: `apps/backend/app/seeds/services/seed_demo_user_service.py`
- Create: `apps/backend/app/seeds/services/seed_utility_dataset_service.py`
- Create: `apps/backend/app/seeds/specs/__init__.py`
- Create: `apps/backend/app/seeds/specs/seed_demo_user_specs.py`
- Create: `apps/backend/app/seeds/specs/seed_utility_dataset_specs.py`
- Create: `apps/backend/app/seeds/runners/__init__.py`
- Create: `apps/backend/app/seeds/runners/seed_demo_users.py`
- Create: `apps/backend/app/seeds/runners/seed_utility_dataset.py`
- Create: `apps/backend/app/core/passwords.py`
- Delete: `apps/backend/app/services/demo_user_seed_service.py`
- Delete: `apps/backend/app/services/password_service.py`
- Delete: `apps/backend/app/seed_demo_users.py`
- Modify: `apps/backend/app/services/auth_service.py`
- Move: `apps/backend/app/tests/test_demo_user_seed_service.py` to
  `apps/backend/app/tests/test_seed_demo_user_service.py`
- Move: `apps/backend/app/tests/test_password_service.py` to
  `apps/backend/app/tests/test_passwords.py`
- Modify: `apps/backend/app/tests/test_auth_service.py`
- Create: `apps/backend/app/tests/test_seed_utility_dataset_specs.py`
- Create: `apps/backend/app/tests/test_seed_utility_dataset_service.py`
- Create: `apps/backend/app/tests/test_seed_utility_dataset_integration.py`

### Read API

- Create: `apps/backend/app/repositories/utility_network_repository.py`
- Create: `apps/backend/app/services/utility_network_service.py`
- Create: `apps/backend/app/schemas/utility_network/__init__.py`
- Create: `apps/backend/app/schemas/utility_network/geojson_feature_out.py`
- Create: `apps/backend/app/schemas/utility_network/feature_collection_out.py`
- Create: `apps/backend/app/schemas/utility_network/association_out.py`
- Create: `apps/backend/app/schemas/utility_network/feeder_out.py`
- Create: `apps/backend/app/tests/test_utility_network_schemas.py`
- Create: `apps/backend/app/domain/exceptions/utility_network_api_error.py`
- Create: `apps/backend/app/api/utility_network.py`
- Create: `apps/backend/app/tests/test_utility_network_repository_integration.py`
- Create: `apps/backend/app/tests/test_utility_network_service.py`
- Create: `apps/backend/app/tests/test_utility_network_api.py`
- Modify: `apps/backend/app/api/deps.py`
- Modify: `apps/backend/app/api/exception_handlers.py`
- Modify: `apps/backend/app/main.py`

### Startup И CI

- Modify: `infra/docker-compose.yml`
- Modify: `infra/docker-compose.override.yml`
- Modify: `.github/workflows/ci.yml`
- Modify: `docs/release_1/sprint_1/README.md`

## Стабильные Идентификаторы Dataset

Использовать эти значения во всех specs и тестах:

| Entity | Identifier |
|---|---|
| AOI | `6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0100` |
| Feeder | `6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0101` |
| `J-001..J-007` | `6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0201..0207` |
| `L-001..L-006` | `6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0211..0216` |
| `D-001..D-006` | `6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0221..0226` |
| Associations 1..9 | `6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0301..0309` |

## Геометрия Dataset

Использовать SRID 4326:

| Asset | Geometry |
|---|---|
| AOI | `POLYGON ((65.495 44.795, 65.545 44.795, 65.545 44.835, 65.495 44.835, 65.495 44.795))` |
| `J-001` | `POINT (65.500 44.820)` |
| `J-002` | `POINT (65.510 44.820)` |
| `J-003` | `POINT (65.520 44.820)` |
| `J-004` | `POINT (65.530 44.820)` |
| `J-005` | `POINT (65.535 44.812)` |
| `J-006` | `POINT (65.540 44.805)` |
| `J-007` | `POINT (65.525 44.830)` |
| `L-001` | `LINESTRING (65.500 44.820, 65.510 44.820)` |
| `L-002` | `LINESTRING (65.510 44.820, 65.520 44.820)` |
| `L-003` | `LINESTRING (65.520 44.820, 65.530 44.820)` |
| `L-004` | `LINESTRING (65.530 44.820, 65.535 44.812)` |
| `L-005` | `LINESTRING (65.535 44.812, 65.540 44.805)` |
| `L-006` | `LINESTRING (65.520 44.820, 65.525 44.830)` |
| `D-001` | `POINT (65.500 44.820)` |
| `D-002` | `POINT (65.520 44.820)` |
| `D-003` | `POINT (65.530 44.820)` |
| `D-004` | `POINT (65.535 44.812)` |
| `D-005` | `POINT (65.525 44.830)` |
| `D-006` | `POINT (65.540 44.805)` |

### Task 0: Создать Пакет Seeds И Перенести Demo User Seed

**Files:**

- Create: `apps/backend/app/seeds/__init__.py`
- Create: `apps/backend/app/seeds/repositories/__init__.py`
- Create: `apps/backend/app/seeds/repositories/seed_user_repository.py`
- Create: `apps/backend/app/seeds/services/__init__.py`
- Create: `apps/backend/app/seeds/services/seed_demo_user_service.py`
- Create: `apps/backend/app/seeds/specs/__init__.py`
- Create: `apps/backend/app/seeds/specs/seed_demo_user_specs.py`
- Create: `apps/backend/app/seeds/runners/__init__.py`
- Create: `apps/backend/app/seeds/runners/seed_demo_users.py`
- Create: `apps/backend/app/core/passwords.py`
- Delete: `apps/backend/app/services/demo_user_seed_service.py`
- Delete: `apps/backend/app/services/password_service.py`
- Delete: `apps/backend/app/seed_demo_users.py`
- Modify: `apps/backend/app/services/auth_service.py`
- Move: `apps/backend/app/tests/test_demo_user_seed_service.py` to
  `apps/backend/app/tests/test_seed_demo_user_service.py`
- Move: `apps/backend/app/tests/test_password_service.py` to
  `apps/backend/app/tests/test_passwords.py`
- Modify: `apps/backend/app/tests/test_auth_service.py`

- [ ] **Step 1: Перенести tests на новые seed imports и имена**

Переместить test-файл и заменить imports:

```python
from seeds.services.seed_demo_user_service import SeedDemoUserService
from seeds.specs.seed_demo_user_specs import SEED_DEMO_USER_SPECS
```

Заменить все:

```text
DEMO_USER_SPECS -> SEED_DEMO_USER_SPECS
DemoUserSeedService -> SeedDemoUserService
```

В перенесенном test использовать:

```python
from core.passwords import hash_password, verify_password
```

Имена test functions сохранить, поскольку они описывают поведение, а не
архитектурный слой.

- [ ] **Step 2: Запустить test и подтвердить ожидаемое падение**

Run:

```powershell
Set-Location apps/backend/app
pytest tests/test_seed_demo_user_service.py -q
```

Expected: collection error, потому что package `seeds` еще не создан.

- [ ] **Step 3: Создать seed user specs**

Создать пустые `__init__.py` во всех четырех seed package directories.

Создать `seeds/specs/seed_demo_user_specs.py`:

```python
from dataclasses import dataclass
from uuid import UUID

from models.user import UserRole


@dataclass(frozen=True)
class SeedDemoUserSpec:
    id: UUID
    email: str
    password: str
    role: UserRole


SEED_DEMO_USER_SPECS: tuple[SeedDemoUserSpec, ...] = (
    SeedDemoUserSpec(
        id=UUID("10000000-0000-4000-8000-000000000001"),
        email="alexey.editor@example.local",
        password="alexey-editor-password",
        role=UserRole.EDITOR,
    ),
    SeedDemoUserSpec(
        id=UUID("10000000-0000-4000-8000-000000000002"),
        email="bolat.editor@example.local",
        password="bolat-editor-password",
        role=UserRole.EDITOR,
    ),
    SeedDemoUserSpec(
        id=UUID("10000000-0000-4000-8000-000000000003"),
        email="marina.reviewer@example.local",
        password="marina-reviewer-password",
        role=UserRole.REVIEWER,
    ),
)
```

- [ ] **Step 4: Создать отдельный seed repository**

Создать `seeds/repositories/seed_user_repository.py`:

```python
from uuid import UUID

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User, UserRole


class SeedUserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalars().one_or_none()

    async def create_user(
        self,
        *,
        email: str,
        role: UserRole,
        password_hash: str,
        user_id: UUID,
    ) -> User:
        result = await self.session.execute(
            insert(User)
            .values(
                id=user_id,
                email=email,
                role=role,
                password_hash=password_hash,
            )
            .returning(User)
        )
        return result.scalar_one()
```

Не импортировать runtime
`repositories.user_repository.UserRepository`: seed repository имеет
собственную узкую ответственность.

- [ ] **Step 5: Вынести общую password logic в core**

Переместить содержимое `services/password_service.py` в
`core/passwords.py` без изменения функций:

```python
from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, password_hash: str | None) -> bool:
    if password_hash is None:
        return False
    return pwd_context.verify(plain_password, password_hash)
```

Обновить imports в:

```text
services/auth_service.py
tests/test_auth_service.py
tests/test_passwords.py
tests/test_seed_demo_user_service.py
```

Новый import:

```python
from core.passwords import hash_password, verify_password
```

`services/auth_service.py` и `tests/test_auth_service.py` импортируют только
нужные им функции.

- [ ] **Step 6: Перенести service с Seed-префиксом**

Создать `seeds/services/seed_demo_user_service.py`:

```python
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from seeds.repositories.seed_user_repository import SeedUserRepository
from seeds.specs.seed_demo_user_specs import SEED_DEMO_USER_SPECS
from core.passwords import hash_password, verify_password


class SeedDemoUserService:
    def __init__(
        self,
        session: AsyncSession,
        repository: SeedUserRepository,
    ):
        self.session = session
        self.repository = repository

    async def ensure_demo_users(self) -> list[User]:
        seeded_users: list[User] = []

        async with self.session.begin():
            for spec in SEED_DEMO_USER_SPECS:
                user = await self.repository.get_by_email(spec.email)
                if user is None:
                    user = await self.repository.create_user(
                        email=spec.email,
                        role=spec.role,
                        password_hash=hash_password(spec.password),
                        user_id=spec.id,
                    )
                else:
                    role_changed = user.role != spec.role
                    password_changed = not verify_password(
                        spec.password,
                        user.password_hash,
                    )
                    active_changed = not user.is_active
                    if role_changed:
                        user.role = spec.role
                    if password_changed:
                        user.password_hash = hash_password(spec.password)
                    if active_changed:
                        user.is_active = True
                    if role_changed or password_changed or active_changed:
                        await self.session.flush()
                seeded_users.append(user)

        return seeded_users


async def run_seed_demo_users() -> list[User]:
    from db.session import SessionFactory

    async with SessionFactory() as session:
        return await SeedDemoUserService(
            session,
            SeedUserRepository(session),
        ).ensure_demo_users()
```

- [ ] **Step 7: Создать module runner**

Создать `seeds/runners/seed_demo_users.py`:

```python
import asyncio

from seeds.services.seed_demo_user_service import run_seed_demo_users


def main() -> None:
    asyncio.run(run_seed_demo_users())


if __name__ == "__main__":
    main()
```

- [ ] **Step 8: Удалить старые seed-файлы**

Удалить:

```text
apps/backend/app/services/demo_user_seed_service.py
apps/backend/app/services/password_service.py
apps/backend/app/seed_demo_users.py
```

Проверить, что runtime `repositories/user_repository.py` не изменен и остается
зависимостью `AuthService`.

- [ ] **Step 9: Запустить user seed tests**

Run:

```powershell
Set-Location apps/backend/app
pytest tests/test_seed_demo_user_service.py tests/test_passwords.py tests/test_auth_service.py -q
```

Expected: demo seed и auth tests проходят.

- [ ] **Step 10: Проверить отсутствие старых imports**

Run:

```powershell
rg -n "demo_user_seed_service|DemoUserSeedService|\bDEMO_USER_SPECS\b|services.password_service" .
if (Test-Path 'seed_demo_users.py') { throw 'Старый root runner не удален' }
black --check seeds core/passwords.py services/auth_service.py tests/test_seed_demo_user_service.py tests/test_passwords.py tests/test_auth_service.py
ruff check seeds core/passwords.py services/auth_service.py tests/test_seed_demo_user_service.py tests/test_passwords.py tests/test_auth_service.py
git diff --check
```

Expected:

- `rg` не находит старые module/class/constant names;
- formatting, lint и whitespace checks проходят.

### Task 1: Зафиксировать Канонические Dataset Specs

**Files:**

- Create: `apps/backend/app/seeds/specs/seed_utility_dataset_specs.py`
- Create: `apps/backend/app/tests/test_seed_utility_dataset_specs.py`

- [ ] **Step 1: Написать failing tests для состава и ссылочной целостности specs**

Создать `tests/test_seed_utility_dataset_specs.py`:

```python
from uuid import UUID

from models.utility_network import AssociationType, FeatureType
from seeds.specs.seed_utility_dataset_specs import (
    UTILITY_DATASET_SPEC,
    UTILITY_FEEDER_CODE,
    UTILITY_FEEDER_ID,
)


def test_utility_dataset_has_stable_identity_and_expected_counts() -> None:
    spec = UTILITY_DATASET_SPEC

    assert UTILITY_FEEDER_ID == UUID("6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0101")
    assert UTILITY_FEEDER_CODE == "synthetic_utility_feeder_01"
    assert spec.feeder.id == UTILITY_FEEDER_ID
    assert spec.feeder.code == UTILITY_FEEDER_CODE
    assert len(spec.features) == 19
    assert len(spec.associations) == 9


def test_utility_dataset_has_expected_feature_breakdown() -> None:
    counts = {
        feature_type: sum(
            feature.feature_type is feature_type
            for feature in UTILITY_DATASET_SPEC.features
        )
        for feature_type in FeatureType
    }

    assert counts == {
        FeatureType.JUNCTION: 7,
        FeatureType.LINE: 6,
        FeatureType.DEVICE: 6,
    }


def test_asset_codes_ids_and_association_edges_are_unique_and_valid() -> None:
    spec = UTILITY_DATASET_SPEC
    asset_codes = [feature.asset_code for feature in spec.features]
    feature_ids = [feature.id for feature in spec.features]
    feature_ids_set = set(feature_ids)
    edges = [
        (
            association.from_feature_id,
            association.to_feature_id,
            association.association_type,
        )
        for association in spec.associations
    ]

    assert len(asset_codes) == len(set(asset_codes))
    assert len(feature_ids) == len(feature_ids_set)
    assert len(edges) == len(set(edges))
    assert all(
        association.association_type is AssociationType.CONNECTIVITY
        for association in spec.associations
    )
    assert all(
        association.from_feature_id in feature_ids_set
        and association.to_feature_id in feature_ids_set
        and association.from_feature_id != association.to_feature_id
        for association in spec.associations
    )
```

- [ ] **Step 2: Запустить tests и подтвердить ожидаемое падение**

Run:

```powershell
Set-Location apps/backend/app
pytest tests/test_seed_utility_dataset_specs.py -q
```

Expected: collection error
`ModuleNotFoundError: No module named 'seeds.specs.seed_utility_dataset_specs'`.

- [ ] **Step 3: Создать immutable dataclasses и полный dataset**

Создать `seeds/specs/seed_utility_dataset_specs.py` с dataclasses:

```python
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from models.utility_network import AssociationType, FeatureType


UTILITY_FEEDER_ID = UUID("6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0101")
UTILITY_FEEDER_CODE = "synthetic_utility_feeder_01"


@dataclass(frozen=True)
class SeedAOISpec:
    id: UUID
    name: str
    description: str
    geometry_wkt: str


@dataclass(frozen=True)
class SeedFeederSpec:
    id: UUID
    code: str
    name: str
    description: str
    is_active: bool = True


@dataclass(frozen=True)
class SeedNetworkFeatureSpec:
    id: UUID
    asset_code: str
    feature_type: FeatureType
    geometry_wkt: str
    name: str
    description: str
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SeedNetworkAssociationSpec:
    id: UUID
    from_feature_id: UUID
    to_feature_id: UUID
    association_type: AssociationType = AssociationType.CONNECTIVITY


@dataclass(frozen=True)
class SeedUtilityDatasetSpec:
    aoi: SeedAOISpec
    feeder: SeedFeederSpec
    features: tuple[SeedNetworkFeatureSpec, ...]
    associations: tuple[SeedNetworkAssociationSpec, ...]
```

Добавить helper:

```python
def stable_uuid(suffix: str) -> UUID:
    return UUID(f"6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f{suffix}")
```

Сформировать `UTILITY_DATASET_SPEC` по таблицам из разделов
«Стабильные Идентификаторы Dataset» и «Геометрия Dataset». Использовать
следующие properties:

| Asset | properties |
|---|---|
| `J-001` | `{"junctionType": "busbar"}` |
| `J-002` | `{"junctionType": "junction"}` |
| `J-003` | `{"junctionType": "switch_node"}` |
| `J-004` | `{"junctionType": "branch"}` |
| `J-005` | `{"junctionType": "transformer_tap"}` |
| `J-006` | `{"junctionType": "service_point"}` |
| `J-007` | `{"junctionType": "tie_point"}` |
| `L-001..L-004`, `L-006` | `{"status": "in_service", "voltageKv": 10.0}` |
| `L-005` | `{"status": "in_service", "voltageKv": 0.4}` |
| `D-001` | `{"deviceType": "breaker", "status": "closed", "normalState": "closed"}` |
| `D-002` | `{"deviceType": "switch", "status": "closed", "normalState": "closed"}` |
| `D-003` | `{"deviceType": "fuse", "status": "closed", "normalState": "closed"}` |
| `D-004` | `{"deviceType": "transformer", "status": "in_service", "normalState": "in_service"}` |
| `D-005` | `{"deviceType": "switch", "status": "open", "normalState": "open"}` |
| `D-006` | `{"deviceType": "meter", "status": "active", "normalState": "active"}` |

Зафиксировать AOI и feeder:

```python
SeedAOISpec(
    id=stable_uuid("0100"),
    name="Район-1",
    description="Рабочая область демонстрационного фидера.",
    geometry_wkt=(
        "POLYGON ((65.495 44.795, 65.545 44.795, "
        "65.545 44.835, 65.495 44.835, 65.495 44.795))"
    ),
)
SeedFeederSpec(
    id=UTILITY_FEEDER_ID,
    code=UTILITY_FEEDER_CODE,
    name="Демонстрационный фидер 10 кВ",
    description="Малый synthetic feeder для Utility GIS workflow.",
)
```

Использовать точные `name` и `description`:

| Asset | name | description |
|---|---|---|
| `J-001` | `Шина подстанции` | `Начальная точка демонстрационного фидера.` |
| `J-002` | `Промежуточный узел 1` | `Узел основного участка фидера.` |
| `J-003` | `Узел секционного выключателя` | `Точка установки SW-01 и начала tie branch.` |
| `J-004` | `Узел ответвления` | `Ответвление к трансформаторному участку.` |
| `J-005` | `Отвод трансформатора` | `Точка подключения TX-01.` |
| `J-006` | `Точка потребителя` | `Конечная точка низковольтного участка.` |
| `J-007` | `Точка tie switch` | `Точка normally-open связи.` |
| `L-001` | `Основная линия 1` | `Участок J-001 -> J-002.` |
| `L-002` | `Основная линия 2` | `Участок J-002 -> J-003.` |
| `L-003` | `Основная линия 3` | `Участок J-003 -> J-004.` |
| `L-004` | `Отвод к трансформатору` | `Участок J-004 -> J-005.` |
| `L-005` | `Линия к потребителю` | `Низковольтный участок J-005 -> J-006.` |
| `L-006` | `Tie line` | `Normally-open ветвь J-003 -> J-007.` |
| `D-001` | `Выключатель BR-01` | `Головной выключатель фидера.` |
| `D-002` | `Секционный выключатель SW-01` | `Устройство будущего work order WO-001.` |
| `D-003` | `Предохранитель FU-01` | `Защита трансформаторного ответвления.` |
| `D-004` | `Трансформатор TX-01` | `Переход с 10 кВ на 0.4 кВ.` |
| `D-005` | `Tie switch SW-TIE-01` | `Normally-open tie switch.` |
| `D-006` | `Счетчик M-01` | `Учетная точка потребителя.` |

Каждый feature создавать по единому полному шаблону:

```python
SeedNetworkFeatureSpec(
    id=stable_uuid("0201"),
    asset_code="J-001",
    feature_type=FeatureType.JUNCTION,
    geometry_wkt="POINT (65.500 44.820)",
    name="Шина подстанции",
    description="Начальная точка демонстрационного фидера.",
    properties={"junctionType": "busbar"},
)
```

Associations зафиксировать точно:

```python
association_edges = (
    ("0301", "0221", "0211"),  # D-001 -> L-001
    ("0302", "0222", "0212"),  # D-002 -> L-002
    ("0303", "0222", "0213"),  # D-002 -> L-003
    ("0304", "0223", "0213"),  # D-003 -> L-003
    ("0305", "0223", "0214"),  # D-003 -> L-004
    ("0306", "0224", "0214"),  # D-004 -> L-004
    ("0307", "0224", "0215"),  # D-004 -> L-005
    ("0308", "0225", "0216"),  # D-005 -> L-006
    ("0309", "0224", "0226"),  # D-004 -> D-006
)
```

- [ ] **Step 4: Запустить unit tests**

Run:

```powershell
Set-Location apps/backend/app
pytest tests/test_seed_utility_dataset_specs.py -q
```

Expected: `3 passed`.

- [ ] **Step 5: Проверить formatting task**

Run:

```powershell
Set-Location apps/backend/app
black --check seeds/specs/seed_utility_dataset_specs.py tests/test_seed_utility_dataset_specs.py
ruff check seeds/specs/seed_utility_dataset_specs.py tests/test_seed_utility_dataset_specs.py
git diff --check
```

Expected: все команды завершаются с exit code `0`.

### Task 2: Реализовать Create-Once Seed Service

**Files:**

- Create: `apps/backend/app/seeds/repositories/seed_utility_dataset_repository.py`
- Create: `apps/backend/app/seeds/services/seed_utility_dataset_service.py`
- Create: `apps/backend/app/seeds/runners/seed_utility_dataset.py`
- Create: `apps/backend/app/tests/test_seed_utility_dataset_service.py`

- [ ] **Step 1: Написать failing unit tests для create и no-op веток**

Создать `tests/test_seed_utility_dataset_service.py`:

```python
import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock

from seeds.services.seed_utility_dataset_service import SeedUtilityDatasetService
from seeds.specs.seed_utility_dataset_specs import UTILITY_DATASET_SPEC


class FakeSession:
    def __init__(self) -> None:
        self.begin_calls = 0

    @asynccontextmanager
    async def begin(self):
        self.begin_calls += 1
        yield self


def test_seed_creates_complete_dataset_when_feeder_is_absent() -> None:
    session = FakeSession()
    repository = AsyncMock()
    repository.get_feeder_by_code.return_value = None
    repository.create_dataset.return_value = SimpleNamespace(
        id=UTILITY_DATASET_SPEC.feeder.id,
        code=UTILITY_DATASET_SPEC.feeder.code,
    )
    service = SeedUtilityDatasetService(session, repository)

    result = asyncio.run(service.ensure_utility_dataset())

    assert result.created is True
    assert result.feeder_id == UTILITY_DATASET_SPEC.feeder.id
    assert session.begin_calls == 1
    repository.create_dataset.assert_awaited_once_with(UTILITY_DATASET_SPEC)


def test_seed_is_noop_when_feeder_already_exists() -> None:
    session = FakeSession()
    existing = SimpleNamespace(
        id=UTILITY_DATASET_SPEC.feeder.id,
        code=UTILITY_DATASET_SPEC.feeder.code,
    )
    repository = AsyncMock()
    repository.get_feeder_by_code.return_value = existing
    service = SeedUtilityDatasetService(session, repository)

    result = asyncio.run(service.ensure_utility_dataset())

    assert result.created is False
    assert result.feeder_id == existing.id
    repository.create_dataset.assert_not_awaited()
```

- [ ] **Step 2: Запустить tests и подтвердить collection failure**

Run:

```powershell
Set-Location apps/backend/app
pytest tests/test_seed_utility_dataset_service.py -q
```

Expected: отсутствуют seed repository/service modules.

- [ ] **Step 3: Реализовать seed repository**

Создать `seeds/repositories/seed_utility_dataset_repository.py`:

```python
from geoalchemy2.elements import WKTElement
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.utility_network import AOI, Feeder, NetworkAssociation, NetworkFeature
from seeds.specs.seed_utility_dataset_specs import SeedUtilityDatasetSpec


class SeedUtilityDatasetRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_feeder_by_code(self, code: str) -> Feeder | None:
        result = await self.session.execute(select(Feeder).where(Feeder.code == code))
        return result.scalars().one_or_none()

    async def create_dataset(self, spec: SeedUtilityDatasetSpec) -> Feeder:
        aoi = AOI(
            id=spec.aoi.id,
            name=spec.aoi.name,
            description=spec.aoi.description,
            geometry=WKTElement(spec.aoi.geometry_wkt, srid=4326),
        )
        feeder = Feeder(
            id=spec.feeder.id,
            code=spec.feeder.code,
            name=spec.feeder.name,
            description=spec.feeder.description,
            is_active=spec.feeder.is_active,
        )
        features = [
            NetworkFeature(
                id=feature.id,
                feeder_id=spec.feeder.id,
                asset_code=feature.asset_code,
                feature_type=feature.feature_type,
                geometry=WKTElement(feature.geometry_wkt, srid=4326),
                name=feature.name,
                description=feature.description,
                properties=feature.properties,
            )
            for feature in spec.features
        ]
        associations = [
            NetworkAssociation(
                id=association.id,
                feeder_id=spec.feeder.id,
                from_feature_id=association.from_feature_id,
                to_feature_id=association.to_feature_id,
                association_type=association.association_type,
            )
            for association in spec.associations
        ]
        self.session.add_all([aoi, feeder, *features, *associations])
        await self.session.flush()
        return feeder
```

- [ ] **Step 4: Реализовать seed service и result contract**

Создать `seeds/services/seed_utility_dataset_service.py`:

```python
import logging
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from seeds.repositories.seed_utility_dataset_repository import (
    SeedUtilityDatasetRepository,
)
from seeds.specs.seed_utility_dataset_specs import (
    UTILITY_DATASET_SPEC,
    UTILITY_FEEDER_CODE,
)


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SeedUtilityDatasetResult:
    feeder_id: UUID
    created: bool


class SeedUtilityDatasetService:
    def __init__(
        self,
        session: AsyncSession,
        repository: SeedUtilityDatasetRepository,
    ):
        self.session = session
        self.repository = repository

    async def ensure_utility_dataset(self) -> SeedUtilityDatasetResult:
        async with self.session.begin():
            existing = await self.repository.get_feeder_by_code(UTILITY_FEEDER_CODE)
            if existing is not None:
                logger.info(
                    "Utility dataset уже существует; startup seed не изменяет агрегат.",
                    extra={"feeder_id": str(existing.id), "feeder_code": existing.code},
                )
                return SeedUtilityDatasetResult(
                    feeder_id=existing.id,
                    created=False,
                )

            feeder = await self.repository.create_dataset(UTILITY_DATASET_SPEC)
            logger.info(
                "Utility dataset создан.",
                extra={"feeder_id": str(feeder.id), "feeder_code": feeder.code},
            )
            return SeedUtilityDatasetResult(feeder_id=feeder.id, created=True)


async def run_seed_utility_dataset() -> SeedUtilityDatasetResult:
    from db.session import SessionFactory

    async with SessionFactory() as session:
        service = SeedUtilityDatasetService(
            session,
            SeedUtilityDatasetRepository(session),
        )
        return await service.ensure_utility_dataset()
```

- [ ] **Step 5: Создать CLI entry point**

Создать `seeds/runners/seed_utility_dataset.py`:

```python
import asyncio

from seeds.services.seed_utility_dataset_service import run_seed_utility_dataset


def main() -> None:
    asyncio.run(run_seed_utility_dataset())


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Запустить unit tests**

Run:

```powershell
Set-Location apps/backend/app
pytest tests/test_seed_utility_dataset_service.py -q
```

Expected: `2 passed`.

- [ ] **Step 7: Проверить formatting и lint**

Run:

```powershell
Set-Location apps/backend/app
black --check seeds/repositories/seed_utility_dataset_repository.py seeds/services/seed_utility_dataset_service.py seeds/runners/seed_utility_dataset.py tests/test_seed_utility_dataset_service.py
ruff check seeds/repositories/seed_utility_dataset_repository.py seeds/services/seed_utility_dataset_service.py seeds/runners/seed_utility_dataset.py tests/test_seed_utility_dataset_service.py
git diff --check
```

Expected: exit code `0`.

### Task 3: Проверить Seed На PostgreSQL/PostGIS

**Files:**

- Create: `apps/backend/app/tests/test_seed_utility_dataset_integration.py`

- [ ] **Step 1: Написать integration test полного dataset**

Создать `tests/test_seed_utility_dataset_integration.py` и использовать
`run_in_rollback_transaction`:

```python
from dataclasses import replace

import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models.utility_network import AOI, Feeder, NetworkAssociation, NetworkFeature
from seeds.repositories.seed_utility_dataset_repository import (
    SeedUtilityDatasetRepository,
)
from seeds.services.seed_utility_dataset_service import SeedUtilityDatasetService
from seeds.specs.seed_utility_dataset_specs import (
    UTILITY_DATASET_SPEC,
    UTILITY_FEEDER_CODE,
)
from tests.network_db_support import run_in_rollback_transaction


async def remove_canonical_dataset(session: AsyncSession) -> None:
    feeder_id = UTILITY_DATASET_SPEC.feeder.id
    await session.execute(
        delete(NetworkAssociation).where(NetworkAssociation.feeder_id == feeder_id)
    )
    await session.execute(
        delete(NetworkFeature).where(NetworkFeature.feeder_id == feeder_id)
    )
    await session.execute(delete(Feeder).where(Feeder.id == feeder_id))
    await session.execute(delete(AOI).where(AOI.id == UTILITY_DATASET_SPEC.aoi.id))
    await session.commit()


def test_seed_persists_complete_valid_dataset() -> None:
    async def scenario(session: AsyncSession) -> None:
        await remove_canonical_dataset(session)
        repository = SeedUtilityDatasetRepository(session)
        result = await SeedUtilityDatasetService(
            session,
            repository,
        ).ensure_utility_dataset()

        feature_count = await session.scalar(
            select(func.count(NetworkFeature.id)).where(
                NetworkFeature.feeder_id == result.feeder_id
            )
        )
        association_count = await session.scalar(
            select(func.count(NetworkAssociation.id)).where(
                NetworkAssociation.feeder_id == result.feeder_id
            )
        )
        aoi_count = await session.scalar(
            select(func.count(AOI.id)).where(AOI.id == UTILITY_DATASET_SPEC.aoi.id)
        )

        assert result.created is True
        assert feature_count == 19
        assert association_count == 9
        assert aoi_count == 1

    run_in_rollback_transaction(scenario)
```

- [ ] **Step 2: Добавить rollback test**

В тот же файл добавить:

```python
def test_seed_rolls_back_everything_when_dataset_is_invalid() -> None:
    async def scenario(session: AsyncSession) -> None:
        await remove_canonical_dataset(session)
        duplicate = replace(
            UTILITY_DATASET_SPEC.features[1],
            id=UTILITY_DATASET_SPEC.features[0].id,
        )
        invalid_spec = replace(
            UTILITY_DATASET_SPEC,
            features=(UTILITY_DATASET_SPEC.features[0], duplicate),
            associations=(),
        )
        repository = SeedUtilityDatasetRepository(session)

        with pytest.raises(IntegrityError):
            async with session.begin():
                await repository.create_dataset(invalid_spec)

        feeder = await session.scalar(
            select(Feeder).where(Feeder.code == UTILITY_FEEDER_CODE)
        )
        assert feeder is None

    run_in_rollback_transaction(scenario)
```

- [ ] **Step 3: Добавить restart/no-op test**

```python
def test_repeated_seed_preserves_existing_changes_and_extra_feature() -> None:
    async def scenario(session: AsyncSession) -> None:
        await remove_canonical_dataset(session)
        repository = SeedUtilityDatasetRepository(session)
        service = SeedUtilityDatasetService(session, repository)
        first = await service.ensure_utility_dataset()

        feeder = await session.get(Feeder, first.feeder_id)
        feeder.name = "Измененное имя"
        existing_feature = await session.scalar(
            select(NetworkFeature).where(
                NetworkFeature.feeder_id == first.feeder_id,
                NetworkFeature.asset_code == "D-002",
            )
        )
        existing_feature.properties = {"status": "maintenance"}
        extra = NetworkFeature(
            feeder_id=first.feeder_id,
            asset_code="D-999",
            feature_type=existing_feature.feature_type,
            geometry=existing_feature.geometry,
            name="Дополнительное устройство",
            properties={"status": "temporary"},
        )
        session.add(extra)
        await session.commit()

        second = await service.ensure_utility_dataset()
        await session.refresh(feeder)
        await session.refresh(existing_feature)
        count = await session.scalar(
            select(func.count(NetworkFeature.id)).where(
                NetworkFeature.feeder_id == first.feeder_id
            )
        )

        assert second.created is False
        assert feeder.name == "Измененное имя"
        assert existing_feature.properties == {"status": "maintenance"}
        assert count == 20

    run_in_rollback_transaction(scenario)
```

`run_in_rollback_transaction` держит внешний connection transaction, поэтому
`session.commit()` завершает текущую ORM-транзакцию для следующего
`session.begin()`, а внешний rollback в helper восстанавливает исходную БД.

- [ ] **Step 4: Запустить DB tests**

Run:

```powershell
docker compose -f infra/docker-compose.yml up -d --build postgis backend
docker compose -f infra/docker-compose.yml exec -T backend env RUN_DB_TESTS=1 pytest tests/test_seed_utility_dataset_integration.py -q
```

Expected: `3 passed`.

- [ ] **Step 5: Проверить seed вручную в чистой БД**

Run:

```powershell
docker compose -f infra/docker-compose.yml down -v
docker compose -f infra/docker-compose.yml up -d --build postgis backend
docker compose -f infra/docker-compose.yml exec -T backend python -m seeds.runners.seed_utility_dataset
docker compose -f infra/docker-compose.yml exec -T postgis psql -U postgres -d geo -c "SELECT id, code, name, is_active FROM utility_network.feeders WHERE code='synthetic_utility_feeder_01';"
docker compose -f infra/docker-compose.yml exec -T postgis psql -U postgres -d geo -c "SELECT feature_type, count(*) FROM utility_network.network_features WHERE feeder_id='6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0101' GROUP BY feature_type ORDER BY feature_type;"
docker compose -f infra/docker-compose.yml exec -T postgis psql -U postgres -d geo -c "SELECT count(*) FROM utility_network.network_associations WHERE feeder_id='6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0101';"
```

Expected:

- feeder UUID совпадает со spec;
- counts: `device=6`, `junction=7`, `line=6`;
- association count равен `9`.

### Task 4: Реализовать Read Repository И Response DTO

**Files:**

- Create: `apps/backend/app/repositories/utility_network_repository.py`
- Create: `apps/backend/app/schemas/utility_network/__init__.py`
- Create: `apps/backend/app/schemas/utility_network/geojson_feature_out.py`
- Create: `apps/backend/app/schemas/utility_network/feature_collection_out.py`
- Create: `apps/backend/app/schemas/utility_network/association_out.py`
- Create: `apps/backend/app/schemas/utility_network/feeder_out.py`
- Create: `apps/backend/app/tests/test_utility_network_schemas.py`
- Create: `apps/backend/app/tests/test_utility_network_repository_integration.py`

- [ ] **Step 1: Написать failing repository integration tests**

Создать `tests/test_utility_network_repository_integration.py`. В setup
каждого scenario вызвать seed service. Проверить:

```python
from seeds.repositories.seed_utility_dataset_repository import (
    SeedUtilityDatasetRepository,
)
from seeds.services.seed_utility_dataset_service import (
    SeedUtilityDatasetService,
)
from seeds.specs.seed_utility_dataset_specs import (
    UTILITY_FEEDER_CODE,
    UTILITY_FEEDER_ID,
)


def test_repository_loads_ordered_feeder_aggregate_and_intersecting_aois() -> None:
    async def scenario(session: AsyncSession) -> None:
        await SeedUtilityDatasetService(
            session,
            SeedUtilityDatasetRepository(session),
        ).ensure_utility_dataset()
        repository = UtilityNetworkRepository(session)

        aggregate = await repository.get_feeder_aggregate(UTILITY_FEEDER_ID)

        assert aggregate is not None
        assert aggregate.code == UTILITY_FEEDER_CODE
        assert [item["asset_code"] for item in aggregate.features_data] == sorted(
            item["asset_code"] for item in aggregate.features_data
        )
        assert len(aggregate.features_data) == 19
        assert len(aggregate.associations_data) == 9
        assert [item["name"] for item in aggregate.aois_data] == ["Район-1"]

    run_in_rollback_transaction(scenario)
```

Добавить scenario с дополнительным пересекающим и непересекающим AOI:

```python
session.add_all(
    [
        AOI(
            name="Район-2",
            geometry=WKTElement(
                "POLYGON ((65.519 44.819, 65.521 44.819, "
                "65.521 44.821, 65.519 44.821, 65.519 44.819))",
                srid=4326,
            ),
        ),
        AOI(
            name="Внешний район",
            geometry=WKTElement(
                "POLYGON ((66 45, 66.1 45, 66.1 45.1, 66 45.1, 66 45))",
                srid=4326,
            ),
        ),
    ]
)
```

После `flush` вызвать `get_feeder_aggregate()` и проверить:

```python
aggregate = await repository.get_feeder_aggregate(UTILITY_FEEDER_ID)

assert [item["name"] for item in aggregate.aois_data] == [
    "Район-1",
    "Район-2",
]
```

`Район-2` присутствует один раз, хотя AOI может пересекать несколько
features. `Внешний район` отсутствует.

Добавить отдельный scenario для feeder с feature вне всех AOI:

```python
outside_feeder = Feeder(code="outside-feeder", name="Внешний фидер")
session.add(outside_feeder)
await session.flush()
session.add(
    NetworkFeature(
        feeder_id=outside_feeder.id,
        asset_code="J-OUT",
        feature_type=FeatureType.JUNCTION,
        geometry=WKTElement("POINT (66.5 45.5)", srid=4326),
        name="Внешний узел",
    )
)
await session.flush()

aggregate = await repository.get_feeder_aggregate(outside_feeder.id)

assert aggregate is not None
assert len(aggregate.features_data) == 1
assert aggregate.associations_data == []
assert aggregate.aois_data == []
```

Добавить проверку неизвестного UUID:

```python
assert await repository.get_feeder_aggregate(uuid4()) is None
```

Добавить unit test одного round trip с `AsyncMock` session:

```python
def test_repository_executes_one_statement() -> None:
    session = AsyncMock()
    session.execute.return_value.one_or_none.return_value = None
    repository = UtilityNetworkRepository(session)

    result = asyncio.run(repository.get_feeder_aggregate(uuid4()))

    assert result is None
    session.execute.assert_awaited_once()
```

- [ ] **Step 2: Написать failing schema contract test**

Создать `tests/test_utility_network_schemas.py`:

```python
from uuid import UUID

from models.utility_network import AssociationType
from schemas.utility_network import (
    UtilityAssociationOut,
    UtilityFeatureCollectionOut,
    UtilityFeederOut,
)


def test_utility_schema_package_exports_and_serializes_wire_aliases() -> None:
    feeder_id = UUID("6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0101")
    from_id = UUID("6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0221")
    to_id = UUID("6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0211")
    association = UtilityAssociationOut(
        id=UUID("6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0301"),
        from_feature_id=from_id,
        to_feature_id=to_id,
        association_type=AssociationType.CONNECTIVITY,
        version=1,
    )
    response = UtilityFeederOut(
        id=feeder_id,
        code="synthetic_utility_feeder_01",
        name="Демонстрационный фидер 10 кВ",
        is_active=True,
        aois=UtilityFeatureCollectionOut(features=[]),
        network=UtilityFeatureCollectionOut(features=[]),
        associations=[association],
    )

    payload = response.model_dump(mode="json", by_alias=True)

    assert payload["isActive"] is True
    assert payload["associations"][0]["fromFeatureId"] == str(from_id)
    assert payload["associations"][0]["toFeatureId"] == str(to_id)
    assert payload["associations"][0]["associationType"] == "connectivity"
```

- [ ] **Step 3: Запустить schema test и подтвердить collection failure**

Run:

```powershell
Set-Location apps/backend/app
pytest tests/test_utility_network_schemas.py -q
```

Expected: `ModuleNotFoundError: No module named 'schemas.utility_network'`.

- [ ] **Step 4: Реализовать пакет response schemas**

Создать `schemas/utility_network/geojson_feature_out.py`:

```python
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from schemas.geojson import FeatureGeometry


class UtilityGeoJSONFeatureOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    type: Literal["Feature"] = "Feature"
    geometry: FeatureGeometry
    properties: dict[str, Any] = Field(default_factory=dict)
```

Создать `schemas/utility_network/feature_collection_out.py`:

```python
from typing import Literal

from pydantic import BaseModel, ConfigDict

from schemas.utility_network.geojson_feature_out import (
    UtilityGeoJSONFeatureOut,
)


class UtilityFeatureCollectionOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[UtilityGeoJSONFeatureOut]
```

Создать `schemas/utility_network/association_out.py`:

```python
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from models.utility_network import AssociationType


class UtilityAssociationOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    from_feature_id: UUID = Field(serialization_alias="fromFeatureId")
    to_feature_id: UUID = Field(serialization_alias="toFeatureId")
    association_type: AssociationType = Field(serialization_alias="associationType")
    version: int
```

Создать `schemas/utility_network/feeder_out.py`:

```python
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from schemas.utility_network.association_out import UtilityAssociationOut
from schemas.utility_network.feature_collection_out import (
    UtilityFeatureCollectionOut,
)


class UtilityFeederOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    code: str
    name: str
    is_active: bool = Field(serialization_alias="isActive")
    aois: UtilityFeatureCollectionOut
    network: UtilityFeatureCollectionOut
    associations: list[UtilityAssociationOut]
```

Создать `schemas/utility_network/__init__.py`:

```python
from schemas.utility_network.association_out import UtilityAssociationOut
from schemas.utility_network.feature_collection_out import (
    UtilityFeatureCollectionOut,
)
from schemas.utility_network.feeder_out import UtilityFeederOut
from schemas.utility_network.geojson_feature_out import (
    UtilityGeoJSONFeatureOut,
)

__all__ = [
    "UtilityAssociationOut",
    "UtilityFeatureCollectionOut",
    "UtilityFeederOut",
    "UtilityGeoJSONFeatureOut",
]
```

- [ ] **Step 5: Запустить schema test**

Run:

```powershell
Set-Location apps/backend/app
pytest tests/test_utility_network_schemas.py -q
```

Expected: `1 passed`.

- [ ] **Step 6: Реализовать repository с одним aggregate query**

Создать `repositories/utility_network_repository.py`:

```python
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import cast, func, literal, select
from sqlalchemy.dialects.postgresql import JSONB, aggregate_order_by
from sqlalchemy.ext.asyncio import AsyncSession

from models.utility_network import AOI, Feeder, NetworkAssociation, NetworkFeature


@dataclass(frozen=True)
class FeederAggregateRow:
    id: UUID
    code: str
    name: str
    is_active: bool
    features_data: list[dict[str, Any]]
    associations_data: list[dict[str, Any]]
    aois_data: list[dict[str, Any]]


class UtilityNetworkRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_feeder_aggregate(
        self,
        feeder_id: UUID,
    ) -> FeederAggregateRow | None:
        empty_array = cast(literal("[]"), JSONB)

        feature_json = func.jsonb_build_object(
            "id",
            NetworkFeature.id,
            "asset_code",
            NetworkFeature.asset_code,
            "feature_type",
            NetworkFeature.feature_type,
            "name",
            NetworkFeature.name,
            "description",
            NetworkFeature.description,
            "properties",
            NetworkFeature.properties,
            "version",
            NetworkFeature.version,
            "geometry_data",
            cast(func.ST_AsGeoJSON(NetworkFeature.geometry), JSONB),
        )
        features_data = (
            select(
                func.coalesce(
                    func.jsonb_agg(
                        aggregate_order_by(
                            feature_json,
                            NetworkFeature.asset_code,
                            NetworkFeature.id,
                        )
                    ),
                    empty_array,
                )
            )
            .where(NetworkFeature.feeder_id == Feeder.id)
            .correlate(Feeder)
            .scalar_subquery()
        )

        association_json = func.jsonb_build_object(
            "id",
            NetworkAssociation.id,
            "from_feature_id",
            NetworkAssociation.from_feature_id,
            "to_feature_id",
            NetworkAssociation.to_feature_id,
            "association_type",
            NetworkAssociation.association_type,
            "version",
            NetworkAssociation.version,
        )
        associations_data = (
            select(
                func.coalesce(
                    func.jsonb_agg(
                        aggregate_order_by(
                            association_json,
                            NetworkAssociation.from_feature_id,
                            NetworkAssociation.to_feature_id,
                            NetworkAssociation.association_type,
                            NetworkAssociation.id,
                        )
                    ),
                    empty_array,
                )
            )
            .where(NetworkAssociation.feeder_id == Feeder.id)
            .correlate(Feeder)
            .scalar_subquery()
        )

        intersecting_feature_exists = (
            select(literal(1))
            .select_from(NetworkFeature)
            .where(
                NetworkFeature.feeder_id == Feeder.id,
                func.ST_Intersects(AOI.geometry, NetworkFeature.geometry),
            )
            .correlate(Feeder, AOI)
            .exists()
        )
        aoi_json = func.jsonb_build_object(
            "id",
            AOI.id,
            "name",
            AOI.name,
            "description",
            AOI.description,
            "geometry_data",
            cast(func.ST_AsGeoJSON(AOI.geometry), JSONB),
        )
        aois_data = (
            select(
                func.coalesce(
                    func.jsonb_agg(
                        aggregate_order_by(
                            aoi_json,
                            AOI.name,
                            AOI.id,
                        )
                    ),
                    empty_array,
                )
            )
            .where(intersecting_feature_exists)
            .correlate(Feeder)
            .scalar_subquery()
        )

        result = await self.session.execute(
            select(
                Feeder.id,
                Feeder.code,
                Feeder.name,
                Feeder.is_active,
                features_data.label("features_data"),
                associations_data.label("associations_data"),
                aois_data.label("aois_data"),
            ).where(Feeder.id == feeder_id)
        )
        row = result.one_or_none()
        if row is None:
            return None
        return FeederAggregateRow(
            id=row.id,
            code=row.code,
            name=row.name,
            is_active=row.is_active,
            features_data=row.features_data,
            associations_data=row.associations_data,
            aois_data=row.aois_data,
        )
```

Нельзя заменять независимые subqueries одним плоским:

```python
select(Feeder).join(NetworkFeature).join(NetworkAssociation).join(AOI)
```

Такой запрос размножает collections и требует последующего удаления
дубликатов.

- [ ] **Step 7: Запустить repository tests**

Run:

```powershell
Set-Location apps/backend/app
pytest tests/test_utility_network_repository_integration.py -q
```

Expected без `RUN_DB_TESTS=1`: DB scenarios пропущены, unit test одного
`session.execute` проходит.

Run:

```powershell
docker compose -f infra/docker-compose.yml exec -T backend env RUN_DB_TESTS=1 pytest tests/test_utility_network_repository_integration.py -q
```

Expected: все repository tests проходят.

- [ ] **Step 8: Проверить форму aggregate SQL вручную**

Run:

```powershell
docker compose -f infra/docker-compose.yml exec -T postgis psql -U postgres -d geo -c "SELECT f.id, (SELECT count(*) FROM utility_network.network_features nf WHERE nf.feeder_id=f.id) AS feature_count, (SELECT count(*) FROM utility_network.network_associations na WHERE na.feeder_id=f.id) AS association_count, (SELECT count(*) FROM utility_network.aois a WHERE EXISTS (SELECT 1 FROM utility_network.network_features nf WHERE nf.feeder_id=f.id AND ST_Intersects(a.geometry,nf.geometry))) AS aoi_count FROM utility_network.feeders f WHERE f.id='6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0101';"
```

Expected: одна строка с `feature_count=19`, `association_count=9`,
`aoi_count>=1`.

### Task 5: Реализовать Mapping Service И Structured Utility Errors

**Files:**

- Create: `apps/backend/app/domain/exceptions/utility_network_api_error.py`
- Create: `apps/backend/app/services/utility_network_service.py`
- Create: `apps/backend/app/tests/test_utility_network_service.py`
- Modify: `apps/backend/app/api/exception_handlers.py`
- Modify: `apps/backend/app/tests/test_exception_handlers.py`

- [ ] **Step 1: Написать failing service tests**

Создать `tests/test_utility_network_service.py` с `AsyncMock` repository.
Проверить:

1. отсутствующий feeder вызывает `404 FEEDER_NOT_FOUND`;
2. system properties перекрывают конфликтующие JSONB keys;
3. association на отсутствующий feature вызывает
   `500 UTILITY_DATASET_INVALID`;
4. невалидная geometry вызывает `500 UTILITY_DATASET_INVALID`;
5. пустой AOI list допустим.

Каждый test задает единственный repository result:

```python
feature_data = {
    "id": FEATURE_ID,
    "asset_code": "D-001",
    "feature_type": "device",
    "name": "Breaker",
    "description": "Start breaker",
    "properties": {
        "assetCode": "spoofed",
        "featureType": "line",
        "name": "spoofed",
        "description": "spoofed",
        "version": 999,
        "status": "closed",
    },
    "version": 1,
    "geometry_data": {
        "type": "Point",
        "coordinates": [65.52, 44.82],
    },
}
association_data = {
    "id": ASSOCIATION_ID,
    "from_feature_id": FEATURE_ID,
    "to_feature_id": FEATURE_ID,
    "association_type": "connectivity",
    "version": 1,
}
repository.get_feeder_aggregate.return_value = FeederAggregateRow(
    id=FEEDER_ID,
    code="synthetic_utility_feeder_01",
    name="Демонстрационный фидер 10 кВ",
    is_active=True,
    features_data=[feature_data],
    associations_data=[association_data],
    aois_data=[],
)
```

И проверяет:

```python
repository.get_feeder_aggregate.assert_awaited_once_with(FEEDER_ID)
```

Ключевой happy-path assert:

```python
response = asyncio.run(service.get_feeder(FEEDER_ID))
payload = response.model_dump(by_alias=True, mode="json")

assert payload["id"] == str(FEEDER_ID)
assert payload["network"]["features"][0]["properties"] == {
    "assetCode": "D-001",
    "featureType": "device",
    "name": "Breaker",
    "description": "Start breaker",
    "version": 1,
    "status": "closed",
}
```

Для проверки integrity error заменить `association_data["to_feature_id"]` на
UUID, которого нет в `features_data`.

- [ ] **Step 2: Создать utility exception**

Создать `domain/exceptions/utility_network_api_error.py`:

```python
class UtilityNetworkApiError(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
```

- [ ] **Step 3: Добавить structured exception handler**

В `api/exception_handlers.py` импортировать
`UtilityNetworkApiError` и добавить handler с тем же response contract, что у
`AuthApiError`:

```python
    @app.exception_handler(UtilityNetworkApiError)
    async def utility_network_api_error(
        request: Request,
        error: UtilityNetworkApiError,
    ):
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid4())
        return JSONResponse(
            status_code=error.status_code,
            content={
                "code": error.code,
                "message": error.message,
                "correlationId": correlation_id,
                "details": {},
            },
        )
```

Расширить `tests/test_exception_handlers.py` endpoint, который вызывает
`UtilityNetworkApiError(404, "FEEDER_NOT_FOUND", "Фидер не найден.")`, и
проверить `status_code`, `code`, `message`, `correlationId`, `details`.

- [ ] **Step 4: Реализовать UtilityNetworkService**

Создать `services/utility_network_service.py`:

```python
from typing import Any
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from domain.exceptions.utility_network_api_error import UtilityNetworkApiError
from repositories.utility_network_repository import UtilityNetworkRepository
from schemas.utility_network import (
    UtilityAssociationOut,
    UtilityFeatureCollectionOut,
    UtilityFeederOut,
    UtilityGeoJSONFeatureOut,
)


class UtilityNetworkService:
    def __init__(
        self,
        session: AsyncSession,
        repository: UtilityNetworkRepository,
    ):
        self.session = session
        self.repository = repository

    async def get_feeder(self, feeder_id: UUID) -> UtilityFeederOut:
        aggregate = await self.repository.get_feeder_aggregate(feeder_id)
        if aggregate is None:
            raise UtilityNetworkApiError(
                404,
                "FEEDER_NOT_FOUND",
                "Фидер не найден.",
            )

        try:
            feature_ids = {
                UUID(str(feature["id"]))
                for feature in aggregate.features_data
            }
            if any(
                UUID(str(association["from_feature_id"])) not in feature_ids
                or UUID(str(association["to_feature_id"])) not in feature_ids
                for association in aggregate.associations_data
            ):
                raise self.invalid_dataset_error()

            network_features = [
                UtilityGeoJSONFeatureOut(
                    id=feature["id"],
                    geometry=feature["geometry_data"],
                    properties=self.network_properties(feature),
                )
                for feature in aggregate.features_data
            ]
            aoi_features = [
                UtilityGeoJSONFeatureOut(
                    id=aoi["id"],
                    geometry=aoi["geometry_data"],
                    properties={
                        "name": aoi["name"],
                        "description": aoi["description"],
                    },
                )
                for aoi in aggregate.aois_data
            ]
            return UtilityFeederOut(
                id=aggregate.id,
                code=aggregate.code,
                name=aggregate.name,
                is_active=aggregate.is_active,
                aois=UtilityFeatureCollectionOut(features=aoi_features),
                network=UtilityFeatureCollectionOut(features=network_features),
                associations=[
                    UtilityAssociationOut(**association)
                    for association in aggregate.associations_data
                ],
            )
        except UtilityNetworkApiError:
            raise
        except (TypeError, ValueError, ValidationError) as exc:
            raise self.invalid_dataset_error() from exc

    def network_properties(self, feature: dict[str, Any]) -> dict[str, Any]:
        stored_properties = dict(feature["properties"])
        return {
            **stored_properties,
            "assetCode": feature["asset_code"],
            "featureType": feature["feature_type"],
            "name": feature["name"],
            "description": feature["description"],
            "version": feature["version"],
        }

    def invalid_dataset_error(self) -> UtilityNetworkApiError:
        return UtilityNetworkApiError(
            500,
            "UTILITY_DATASET_INVALID",
            "Utility dataset поврежден и не может быть прочитан.",
        )
```

- [ ] **Step 5: Запустить unit tests**

Run:

```powershell
Set-Location apps/backend/app
pytest tests/test_utility_network_service.py tests/test_exception_handlers.py -q
```

Expected: все tests проходят.

- [ ] **Step 6: Проверить formatting и lint**

Run:

```powershell
Set-Location apps/backend/app
black --check domain/exceptions/utility_network_api_error.py services/utility_network_service.py tests/test_utility_network_service.py api/exception_handlers.py tests/test_exception_handlers.py
ruff check domain/exceptions/utility_network_api_error.py services/utility_network_service.py tests/test_utility_network_service.py api/exception_handlers.py tests/test_exception_handlers.py
git diff --check
```

Expected: exit code `0`.

### Task 6: Подключить Editor-Only HTTP Endpoint

**Files:**

- Create: `apps/backend/app/api/utility_network.py`
- Create: `apps/backend/app/tests/test_utility_network_api.py`
- Modify: `apps/backend/app/api/deps.py`
- Modify: `apps/backend/app/main.py`

- [ ] **Step 1: Написать failing API tests**

Создать `tests/test_utility_network_api.py`. Построить test app:

```python
def build_app(auth_service: object, utility_service: object) -> FastAPI:
    app = FastAPI()
    install_exception_handlers(app)
    app.include_router(utility_network_router)
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_utility_network_service] = lambda: utility_service
    return app
```

Добавить tests:

- active Editor получает `200` и camelCase keys;
- Reviewer получает `403 ROLE_NOT_ALLOWED`, utility service не вызывается;
- inactive Editor получает `403 USER_INACTIVE`;
- запрос без token получает `401 AUTH_REQUIRED`;
- invalid UUID получает стандартный `422`;
- service `FEEDER_NOT_FOUND` становится structured `404`.

Happy path:

```python
response = TestClient(build_app(auth_service, utility_service)).get(
    f"/api/v1/utility-network/feeders/{FEEDER_ID}",
    headers={"Authorization": f"Bearer {token}"},
)

assert response.status_code == 200
assert response.json()["id"] == str(FEEDER_ID)
assert response.json()["isActive"] is True
assert response.json()["associations"][0]["fromFeatureId"] == str(FROM_ID)
```

- [ ] **Step 2: Добавить dependency factory**

В `api/deps.py` импортировать repository/service и добавить:

```python
def get_utility_network_service(
    session: AsyncSession = Depends(get_session),
) -> UtilityNetworkService:
    return UtilityNetworkService(
        session,
        UtilityNetworkRepository(session),
    )
```

- [ ] **Step 3: Создать router**

Создать `api/utility_network.py`:

```python
from uuid import UUID

from fastapi import APIRouter, Depends

from api.auth import require_editor
from api.deps import get_utility_network_service
from models.user import User
from schemas.utility_network import UtilityFeederOut
from services.utility_network_service import UtilityNetworkService


utility_network_router = APIRouter(
    prefix="/api/v1/utility-network",
    tags=["utility-network"],
)


@utility_network_router.get(
    "/feeders/{feederId}",
    response_model=UtilityFeederOut,
)
async def get_feeder(
    feederId: UUID,
    _: User = Depends(require_editor),
    service: UtilityNetworkService = Depends(get_utility_network_service),
) -> UtilityFeederOut:
    feeder_id = feederId
    return await service.get_feeder(feeder_id)
```

Исключение `feederId` в сигнатуре router необходимо, потому что FastAPI
связывает имя аргумента с именем path placeholder. Сразу после binding
значение переводится во внутреннее `feeder_id`; service и repository сохраняют
snake_case. FastAPI сериализует response model с aliases.

- [ ] **Step 4: Зарегистрировать router**

В `main.py`:

```python
from api.utility_network import utility_network_router
```

и после auth router:

```python
app.include_router(utility_network_router)
```

- [ ] **Step 5: Запустить API tests**

Run:

```powershell
Set-Location apps/backend/app
pytest tests/test_utility_network_api.py tests/test_auth_access.py -q
```

Expected: все tests проходят.

- [ ] **Step 6: Проверить OpenAPI contract**

Run после запуска backend:

```powershell
docker compose -f infra/docker-compose.yml exec -T backend python -c "import json, urllib.request; schema=json.load(urllib.request.urlopen('http://127.0.0.1:8000/openapi.json')); path='/api/v1/utility-network/feeders/{feederId}'; assert path in schema['paths']; parameter=schema['paths'][path]['get']['parameters'][0]; assert parameter['name']=='feederId'; assert parameter['schema']['format']=='uuid'; print('utility endpoint openapi ok')"
```

Expected: `utility endpoint openapi ok`.

### Task 7: Подключить Startup Seed И CI Smoke

**Files:**

- Modify: `infra/docker-compose.yml`
- Modify: `infra/docker-compose.override.yml`
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1: Добавить utility seed в оба backend commands**

Заменить command в `infra/docker-compose.yml` и
`infra/docker-compose.override.yml`:

```yaml
command:
  [
    "bash",
    "-lc",
    "set -euo pipefail; alembic upgrade head; python -m seeds.runners.seed_demo_users; python -m seeds.runners.seed_utility_dataset; uvicorn main:app --host 0.0.0.0 --port 8000"
  ]
```

Порядок обязателен: migrations, users, utility dataset, API.

- [ ] **Step 2: Проверить Compose config**

Run:

```powershell
Set-Location infra
docker compose -f docker-compose.yml config --quiet
docker compose config --quiet
docker compose --profile dev config --quiet
docker compose --profile prod config --quiet
```

Expected: все команды завершаются с exit code `0`.

- [ ] **Step 3: Расширить CI DB tests**

В `.github/workflows/ci.yml` в шаге
`PostgreSQL/PostGIS network model tests` добавить:

```yaml
          docker compose -f docker-compose.yml exec -T backend env RUN_DB_TESTS=1 \
            pytest tests/test_seed_utility_dataset_integration.py -q
          docker compose -f docker-compose.yml exec -T backend env RUN_DB_TESTS=1 \
            pytest tests/test_utility_network_repository_integration.py -q
```

- [ ] **Step 4: Добавить authenticated endpoint smoke в CI**

После DB tests добавить шаг:

```yaml
      - name: Utility dataset authenticated API smoke
        working-directory: infra
        run: |
          docker compose -f docker-compose.yml exec -T backend \
            python -m seeds.runners.seed_utility_dataset
          docker compose -f docker-compose.yml exec -T backend python -c \
            "import json, urllib.request; \
            login=urllib.request.Request( \
              'http://127.0.0.1:8000/api/v1/auth/login', \
              data=json.dumps({ \
                'email':'alexey.editor@example.local', \
                'password':'alexey-editor-password' \
              }).encode(), \
              headers={'Content-Type':'application/json'} \
            ); \
            token=json.load(urllib.request.urlopen(login))['access_token']; \
            request=urllib.request.Request( \
              'http://127.0.0.1:8000/api/v1/utility-network/feeders/6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0101', \
              headers={'Authorization':'Bearer '+token} \
            ); \
            payload=json.load(urllib.request.urlopen(request)); \
            assert payload['code']=='synthetic_utility_feeder_01'; \
            assert len(payload['network']['features'])==19; \
            assert len(payload['associations'])==9; \
            print('utility dataset api ok')"
```

- [ ] **Step 5: Проверить restart preservation**

Run:

```powershell
docker compose -f infra/docker-compose.yml exec -T postgis psql -U postgres -d geo -c "UPDATE utility_network.feeders SET name='Измененное имя' WHERE id='6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0101';"
docker compose -f infra/docker-compose.yml restart backend
docker compose -f infra/docker-compose.yml exec -T postgis psql -U postgres -d geo -tAc "SELECT name FROM utility_network.feeders WHERE id='6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0101';"
```

Expected: результат остается `Измененное имя`.

- [ ] **Step 6: Проверить Reviewer denial вручную**

Run:

```powershell
docker compose -f infra/docker-compose.yml exec -T backend python -c "import json, urllib.error, urllib.request; login=urllib.request.Request('http://127.0.0.1:8000/api/v1/auth/login', data=json.dumps({'email':'marina.reviewer@example.local','password':'marina-reviewer-password'}).encode(), headers={'Content-Type':'application/json'}); token=json.load(urllib.request.urlopen(login))['access_token']; request=urllib.request.Request('http://127.0.0.1:8000/api/v1/utility-network/feeders/6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0101', headers={'Authorization':'Bearer '+token}); exec(\"try:\\n urllib.request.urlopen(request)\\n raise SystemExit('expected 403')\\nexcept urllib.error.HTTPError as error:\\n assert error.code == 403\\n assert json.load(error)['code'] == 'ROLE_NOT_ALLOWED'\\n print('reviewer denied')\")"
```

Expected: `reviewer denied`.

### Task 8: Финальная Проверка И Документация

**Files:**

- Modify: `docs/release_1/sprint_1/README.md`
- Verify: `docs/release_1/sprint_1/2026-06-15-sprint-1-day-4-utility-dataset-design.md`
- Verify: `docs/release_1/sprint_1/2026-06-15-sprint-1-day-4-utility-dataset-implementation-plan.md`

- [ ] **Step 1: Добавить implementation plan в Sprint 1 index**

В `docs/release_1/sprint_1/README.md` после design Дня 4 добавить:

```markdown
- [План реализации utility dataset и read-only backend API Дня 4](2026-06-15-sprint-1-day-4-utility-dataset-implementation-plan.md)
```

- [ ] **Step 2: Запустить backend unit suite**

Run:

```powershell
Set-Location apps/backend/app
black --check .
ruff check .
pytest -q
```

Expected:

- Black и Ruff проходят;
- unit/API tests проходят;
- DB integration tests пропускаются без `RUN_DB_TESTS=1`.

- [ ] **Step 3: Запустить полный DB suite**

Run:

```powershell
docker compose -f infra/docker-compose.yml down -v
docker compose -f infra/docker-compose.yml up -d --build postgis backend
docker compose -f infra/docker-compose.yml exec -T backend env RUN_DB_TESTS=1 pytest tests/test_network_model_integration.py tests/test_network_model_migration.py tests/test_seed_utility_dataset_integration.py tests/test_utility_network_repository_integration.py -q
```

Expected: все network model и utility dataset DB tests проходят.

- [ ] **Step 4: Выполнить полный authenticated smoke**

Run:

```powershell
docker compose -f infra/docker-compose.yml exec -T backend python -c "import json, urllib.request; login=urllib.request.Request('http://127.0.0.1:8000/api/v1/auth/login', data=json.dumps({'email':'alexey.editor@example.local','password':'alexey-editor-password'}).encode(), headers={'Content-Type':'application/json'}); token=json.load(urllib.request.urlopen(login))['access_token']; request=urllib.request.Request('http://127.0.0.1:8000/api/v1/utility-network/feeders/6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0101', headers={'Authorization':'Bearer '+token}); payload=json.load(urllib.request.urlopen(request)); assert payload['id']=='6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0101'; assert payload['code']=='synthetic_utility_feeder_01'; assert payload['isActive'] is True; assert len(payload['aois']['features']) >= 1; assert len(payload['network']['features']) == 19; assert len(payload['associations']) == 9; feature_ids={feature['id'] for feature in payload['network']['features']}; assert all(item['fromFeatureId'] in feature_ids and item['toFeatureId'] in feature_ids for item in payload['associations']); print('utility endpoint verified')"
```

Expected: `utility endpoint verified`.

- [ ] **Step 5: Проверить отсутствие scope creep**

Run:

```powershell
git status --short
git diff --name-only
git diff --check
```

Expected:

- отсутствуют изменения migrations и моделей День 3;
- отсутствуют `WorkOrder`, `EditVersion`, validation, reset и frontend files;
- пользовательские `.obsidian` changes не изменены агентом;
- whitespace errors отсутствуют.

- [ ] **Step 6: Выполнить repository-change ingest**

Новая граница пакета `seeds`, разделение runtime и seed repositories и перенос
общей password logic в `core/passwords.py` являются устойчивым техническим
знанием, которого нет в текущем `Code_wiki`. После завершения реализации
запустить `/ingest repository-change` через
`.agents/skills/source-command-ingest/SKILL.md`.

- Ingest может менять только `Code_wiki`; code, migrations и tests он не
  меняет.

- [ ] **Step 7: Оставить изменения без staging и commit**

Не выполнять `git add`, `git commit` или push. Сообщить пользователю:

- какие проверки прошли;
- какие файлы изменены;
- есть ли незапущенные проверки;
- что working tree готов для пользовательского review.

## Проверка Покрытия Design

- Изолированный пакет `seeds` и Seed-префиксы: Task 0 и Tasks 1-3.
- Отдельный `SeedUserRepository` без зависимости от runtime repository:
  Task 0.
- Общий password hashing в `core/passwords.py`: Task 0.
- Полный dataset `1 AOI / 1 feeder / 19 features / 9 associations`: Tasks 1-3.
- Стабильный UUID feeder и business code: Tasks 1-3.
- Create-once startup semantics: Tasks 2, 3 и 7.
- Атомарное создание и rollback: Tasks 2-3.
- Отсутствие скрытой синхронизации существующего feeder: Tasks 2, 3 и 7.
- Все features feeder независимо от AOI: Tasks 4-5.
- Один SQL round trip для feeder aggregate: Task 4.
- Все пересекающиеся AOI через correlated `EXISTS` и `ST_Intersects`: Task 4.
- GeoJSON и system-property precedence: Tasks 4-5.
- Association integrity guard: Task 5.
- Editor-only auth и Reviewer `403`: Task 6.
- UUID path parameter, `404`, standard `422`, structured `500`: Tasks 5-6.
- Startup order migrations/users/utility/API: Task 7.
- CI, Compose smoke и restart preservation: Tasks 7-8.
- Отсутствие reset, WorkOrder, EditVersion и frontend scope: Tasks 1-8.
