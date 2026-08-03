# Sprint 2 Day 1 Coordinate Grid and Demo Fixture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Добавить строгую конфигурацию координатной сетки, сделать `L-003` единственной трёхвершинной demo line и атомарно обновлять её безопасные двухвершинные materialized-копии без automatic `full-clean`.

**Architecture:** Create-once seeds сохраняют текущее поведение. После seed chain отдельный `DemoFixtureUpgradeService` загружает и блокирует hierarchy `Feeder -> DefaultState -> EditVersion`, сначала рассчитывает все geometry updates, затем применяет их одной transaction. Существующие трёхвершинные geometry не меняются.

**Tech Stack:** Python 3.12, Pydantic Settings 2.6, SQLAlchemy 2 async, PostgreSQL 16/PostGIS 3.4, GeoAlchemy2, Shapely 2.0, Pytest, Docker Compose.

## Global Constraints

- `UTILITY_GEOMETRY_XY_RESOLUTION` имеет default `Decimal("0.0000001")` и принимает любое конечное `Decimal > 0` без искусственной верхней границы.
- `UTILITY_GEOMETRY_ROUNDING_MODE` поддерживает только регистрозависимое значение `ROUND_HALF_AWAY_FROM_ZERO`.
- Будущий canonicalizer сопоставит `ROUND_HALF_AWAY_FROM_ZERO -> decimal.ROUND_HALF_UP`; сам canonicalizer в план не входит.
- Fresh fixture содержит ровно `19 features`, `9 associations`, `7 junctions`, `6 lines` и `6 devices`.
- Fresh `L-003` имеет `LINESTRING (65.520 44.820, 65.525 44.8205, 65.530 44.820)`.
- Structural eligibility: `FeatureType.LINE + LineString + ровно 3 coordinates`; рабочая логика не использует `assetCode` как allowlist.
- Upgrade изменяет только двухвершинные copies `L-003`; существующие трёхвершинные coordinates сохраняются.
- Двухвершинная `EditVersionFeature` обновляется только при `operation=unchanged`.
- Upgrade не меняет UUID, properties, associations, versions, operation и не создаёт audit/change events.
- Unsafe/invalid hierarchy вызывает rollback и блокирует demo startup; automatic `down -v` запрещён.
- Production `start_api.sh` не запускает demo seeds или fixture upgrade.
- Новые runtime dependencies не добавляются.
- Документация пишется на русском; пути, команды, типы и identifiers не переводятся.
- `git add`, `git commit` и `git push` запрещены. Все изменения остаются unstaged; вместо commit используется review checkpoint.
- Все backend `python`/`pytest`/`ruff`/`black` команды выполняются из `apps/backend`
  внутри project venv или backend container; команды с `infra/...` и итоговый Git
  review — из repository root. `infra/dev-up.cmd` не вызывает host Python.

---

## File Structure

### Новые файлы

- `apps/backend/seeds/contracts/__init__.py` — exports контрактов upgrade.
- `apps/backend/seeds/contracts/demo_fixture_upgrade.py` — immutable dataclasses и source enum.
- `apps/backend/seeds/services/demo_fixture_upgrade_service.py` — validation, propagation и transaction.
- `apps/backend/seeds/repositories/demo_fixture_upgrade_repository.py` — ordered row locks и geometry-only updates.
- `apps/backend/seeds/runners/upgrade_demo_fixture.py` — startup entry point.
- `apps/backend/seeds/tests/test_demo_fixture_upgrade_service.py` — service matrix.
- `apps/backend/tests/integration_tests/test_demo_fixture_upgrade_integration.py` — PostGIS proof.

### Изменяемые файлы

- `apps/backend/utility_service/utils/settings.py`
- `apps/backend/utility_service/utils/tests/test_settings.py`
- `infra/docker-compose.yml`
- `infra/demo.env`
- `apps/backend/tests/test_compose_security_contract.py`
- `apps/backend/seeds/specs/seed_utility_dataset_specs.py`
- `apps/backend/seeds/tests/test_seed_utility_dataset_specs.py`
- `apps/backend/scripts/start_utility_service.sh`
- `apps/backend/tests/test_compose_startup_contract.py`
- `README.md`
- `docs/sprint_2/2026-07-31-sprint-2-calendar-plan.md`
- `docs/sprint_2/2026-07-31-sprint-2-technical-requirements.md`

---

### Task 1: Geometry Settings and Compose Propagation

**Files:**

- Modify: `apps/backend/utility_service/utils/tests/test_settings.py`
- Modify: `apps/backend/utility_service/utils/settings.py`
- Modify: `apps/backend/tests/test_compose_security_contract.py`
- Modify: `infra/docker-compose.yml`
- Modify: `infra/demo.env`

**Interfaces:**

- Consumes: существующий `Settings(BaseSettings)` и Compose `utility_service.environment`.
- Produces: `UtilityGeometryRoundingMode`, `utility_geometry_xy_resolution: Decimal` и `utility_geometry_rounding_mode: UtilityGeometryRoundingMode`.

- [ ] **Step 1: Добавить failing settings tests**

В `test_settings.py` импортировать `Decimal` и `UtilityGeometryRoundingMode`, затем добавить:

```python
from decimal import Decimal


def test_settings_defaults_utility_geometry_grid() -> None:
    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/geo",
        DEV_MODE=True,
        JWT_SECRET="CHANGE_ME_IN_ENV",
    )

    assert settings.utility_geometry_xy_resolution == Decimal("0.0000001")
    assert (
        settings.utility_geometry_rounding_mode
        is UtilityGeometryRoundingMode.HALF_AWAY_FROM_ZERO
    )


def test_settings_read_utility_geometry_grid_from_env_aliases() -> None:
    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/geo",
        DEV_MODE=True,
        JWT_SECRET="CHANGE_ME_IN_ENV",
        UTILITY_GEOMETRY_XY_RESOLUTION="0.00000025",
        UTILITY_GEOMETRY_ROUNDING_MODE="ROUND_HALF_AWAY_FROM_ZERO",
    )

    assert settings.utility_geometry_xy_resolution == Decimal("0.00000025")
    assert (
        settings.utility_geometry_rounding_mode
        is UtilityGeometryRoundingMode.HALF_AWAY_FROM_ZERO
    )


def test_settings_accepts_any_large_finite_positive_resolution() -> None:
    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/geo",
        DEV_MODE=True,
        JWT_SECRET="CHANGE_ME_IN_ENV",
        UTILITY_GEOMETRY_XY_RESOLUTION="1E+1000",
    )

    assert settings.utility_geometry_xy_resolution == Decimal("1E+1000")


@pytest.mark.parametrize(
    "resolution",
    ["0", "-0.0000001", "NaN", "Infinity", "-Infinity", "", "not-a-number"],
)
def test_settings_reject_invalid_utility_geometry_resolution(resolution: str) -> None:
    with pytest.raises(ValidationError):
        Settings(
            DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/geo",
            DEV_MODE=True,
            JWT_SECRET="CHANGE_ME_IN_ENV",
            UTILITY_GEOMETRY_XY_RESOLUTION=resolution,
        )


@pytest.mark.parametrize(
    "rounding_mode",
    ["ROUND_HALF_UP", "round_half_away_from_zero", "ROUND_HALF_TO_EVEN"],
)
def test_settings_reject_unsupported_utility_geometry_rounding_mode(
    rounding_mode: str,
) -> None:
    with pytest.raises(ValidationError):
        Settings(
            DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/geo",
            DEV_MODE=True,
            JWT_SECRET="CHANGE_ME_IN_ENV",
            UTILITY_GEOMETRY_ROUNDING_MODE=rounding_mode,
        )
```

- [ ] **Step 2: Запустить settings tests и подтвердить red state**

Run from `apps/backend`:

```powershell
python -m pytest utility_service/utils/tests/test_settings.py -q
```

Expected: import/attribute FAIL, потому что enum и fields отсутствуют.

- [ ] **Step 3: Реализовать минимальный settings contract**

В `settings.py` добавить:

```python
import enum
from decimal import Decimal


class UtilityGeometryRoundingMode(str, enum.Enum):
    HALF_AWAY_FROM_ZERO = "ROUND_HALF_AWAY_FROM_ZERO"
```

После `legacy_gis_api_enabled` добавить:

```python
    utility_geometry_xy_resolution: Decimal = Field(
        Decimal("0.0000001"),
        gt=0,
        allow_inf_nan=False,
        alias="UTILITY_GEOMETRY_XY_RESOLUTION",
    )
    utility_geometry_rounding_mode: UtilityGeometryRoundingMode = Field(
        UtilityGeometryRoundingMode.HALF_AWAY_FROM_ZERO,
        alias="UTILITY_GEOMETRY_ROUNDING_MODE",
    )
```

- [ ] **Step 4: Запустить settings tests**

```powershell
python -m pytest utility_service/utils/tests/test_settings.py -q
```

Expected: PASS.

- [ ] **Step 5: Добавить failing Compose/env contract tests**

В `test_compose_security_contract.py` добавить:

```python
def test_base_compose_passes_utility_geometry_settings() -> None:
    compose = read_infra_file("docker-compose.yml")
    utility_service = service_block(compose, "utility_service")

    assert (
        "UTILITY_GEOMETRY_XY_RESOLUTION: "
        "${UTILITY_GEOMETRY_XY_RESOLUTION:-0.0000001}"
    ) in utility_service
    assert (
        "UTILITY_GEOMETRY_ROUNDING_MODE: "
        "${UTILITY_GEOMETRY_ROUNDING_MODE:-ROUND_HALF_AWAY_FROM_ZERO}"
    ) in utility_service


def test_demo_env_fixes_utility_geometry_defaults() -> None:
    demo_env = read_infra_file("demo.env")

    assert "UTILITY_GEOMETRY_XY_RESOLUTION=0.0000001" in demo_env
    assert "UTILITY_GEOMETRY_ROUNDING_MODE=ROUND_HALF_AWAY_FROM_ZERO" in demo_env
```

- [ ] **Step 6: Запустить contract tests и подтвердить red state**

```powershell
python -m pytest tests/test_compose_security_contract.py -q
```

Expected: new tests FAIL на отсутствующих markers.

- [ ] **Step 7: Передать settings через Compose и demo.env**

В `utility_service.environment` добавить:

```yaml
      UTILITY_GEOMETRY_XY_RESOLUTION: ${UTILITY_GEOMETRY_XY_RESOLUTION:-0.0000001}
      UTILITY_GEOMETRY_ROUNDING_MODE: ${UTILITY_GEOMETRY_ROUNDING_MODE:-ROUND_HALF_AWAY_FROM_ZERO}
```

В `infra/demo.env` добавить:

```dotenv
UTILITY_GEOMETRY_XY_RESOLUTION=0.0000001
UTILITY_GEOMETRY_ROUNDING_MODE=ROUND_HALF_AWAY_FROM_ZERO
```

- [ ] **Step 8: Запустить focused tests и review checkpoint**

```powershell
python -m pytest utility_service/utils/tests/test_settings.py tests/test_compose_security_contract.py -q
python -m ruff check utility_service/utils/settings.py utility_service/utils/tests/test_settings.py tests/test_compose_security_contract.py
python -m black --check utility_service/utils/settings.py utility_service/utils/tests/test_settings.py tests/test_compose_security_contract.py
git diff --check
git status --short
```

Expected: tests/lint PASS; Compose tests могут быть SKIPPED только без repository `infra/`; изменения unstaged.

---

### Task 2: Three-Vertex L-003 Seed Specification

**Files:**

- Modify: `apps/backend/seeds/specs/seed_utility_dataset_specs.py:50-281`
- Modify: `apps/backend/seeds/tests/test_seed_utility_dataset_specs.py`

**Interfaces:**

- Consumes: `UTILITY_FEATURE_SPECS`, `UTILITY_DATASET_SPEC` и `SEED_WORK_ORDER_AOI_SPEC`.
- Produces: `UTILITY_EDITABLE_LINE_ASSET_CODE = "L-003"` и `UTILITY_EDITABLE_LINE_SPEC`.

- [ ] **Step 1: Добавить failing fixture tests**

Добавить imports `Decimal`, `shapely.wkt.loads`, `Point` и `SEED_WORK_ORDER_AOI_SPEC`, затем:

```python
def test_l003_is_the_only_structurally_eligible_demo_line() -> None:
    lines = [
        feature
        for feature in UTILITY_DATASET_SPEC.features
        if feature.feature_type is FeatureType.LINE
    ]
    eligible = [
        feature for feature in lines if len(loads(feature.geometry_wkt).coords) == 3
    ]

    assert [feature.asset_code for feature in eligible] == ["L-003"]
    assert sum(len(loads(feature.geometry_wkt).coords) == 2 for feature in lines) == 5


def test_l003_has_exact_safe_internal_vertex_and_unchanged_endpoints() -> None:
    by_code = {
        feature.asset_code: feature for feature in UTILITY_DATASET_SPEC.features
    }
    line = loads(by_code["L-003"].geometry_wkt)
    aoi = loads(SEED_WORK_ORDER_AOI_SPEC.geometry_wkt)
    point_coordinates = {
        tuple(loads(feature.geometry_wkt).coords[0])
        for feature in UTILITY_DATASET_SPEC.features
        if feature.feature_type in {FeatureType.JUNCTION, FeatureType.DEVICE}
    }

    assert list(line.coords) == [
        (65.520, 44.820),
        (65.525, 44.8205),
        (65.530, 44.820),
    ]
    assert tuple(line.coords[0]) == tuple(loads(by_code["J-003"].geometry_wkt).coords[0])
    assert tuple(line.coords[-1]) == tuple(loads(by_code["J-004"].geometry_wkt).coords[0])
    assert tuple(line.coords[1]) not in point_coordinates
    assert aoi.covers(line)
    assert line.is_valid and line.is_simple and not line.is_empty
    assert Point(line.coords[1]).within(aoi)
    for coordinate in line.coords:
        for ordinate in coordinate:
            assert Decimal(str(ordinate)) % Decimal("0.0000001") == 0


def test_l003_keeps_expected_association_edges() -> None:
    by_id = {feature.id: feature.asset_code for feature in UTILITY_DATASET_SPEC.features}
    edges = {
        (by_id[item.from_feature_id], by_id[item.to_feature_id])
        for item in UTILITY_DATASET_SPEC.associations
        if "L-003" in {by_id[item.from_feature_id], by_id[item.to_feature_id]}
    }

    assert edges == {("D-002", "L-003"), ("D-003", "L-003")}
```

- [ ] **Step 2: Запустить seed tests и подтвердить red state**

```powershell
python -m pytest seeds/tests/test_seed_utility_dataset_specs.py -q
```

Expected: eligibility/exact geometry tests FAIL.

- [ ] **Step 3: Изменить только L-003 и экспортировать constants**

Перед tuple объявить `UTILITY_EDITABLE_LINE_ASSET_CODE = "L-003"`. В `L-003` использовать:

```python
        asset_code=UTILITY_EDITABLE_LINE_ASSET_CODE,
        feature_type=FeatureType.LINE,
        geometry_wkt=(
            "LINESTRING (65.520 44.820, 65.525 44.8205, 65.530 44.820)"
        ),
```

После tuple объявить:

```python
UTILITY_EDITABLE_LINE_SPEC = next(
    feature
    for feature in UTILITY_FEATURE_SPECS
    if feature.asset_code == UTILITY_EDITABLE_LINE_ASSET_CODE
)
```

- [ ] **Step 4: Запустить seed tests и review checkpoint**

```powershell
python -m pytest seeds/tests/test_seed_utility_dataset_specs.py seeds/tests/test_seed_utility_dataset_service.py -q
python -m ruff check seeds/specs/seed_utility_dataset_specs.py seeds/tests/test_seed_utility_dataset_specs.py
python -m black --check seeds/specs/seed_utility_dataset_specs.py seeds/tests/test_seed_utility_dataset_specs.py
git diff --check
git status --short
```

Expected: PASS; counts `19/9`, IDs, properties и association tuples сохранены.

### Task 3: Fixture Upgrade Contracts and Happy Path

**Files:**

- Create: `apps/backend/seeds/contracts/__init__.py`
- Create: `apps/backend/seeds/contracts/demo_fixture_upgrade.py`
- Create: `apps/backend/seeds/services/demo_fixture_upgrade_service.py`
- Test: `apps/backend/seeds/tests/test_demo_fixture_upgrade_service.py`

- [ ] **Step 1: Написать unit tests для безопасных переходов 2 → 3**

Собрать в test module `FakeRepository`, который возвращает hierarchy snapshot, записывает вызовы `update_geometry()` и умеет аварийно падать на заданной записи. Зафиксировать шесть сценариев:

1. feeder/default/edit имеют по две вершины → три update на exact seed WKT;
2. mixed `3/2/2`: feeder уже имеет три пользовательские вершины, default/edit имеют две → обе копии получают feeder WKT;
3. mixed `2/3/2`: feeder имеет две вершины, default — три пользовательские, edit — две → feeder получает seed WKT, default сохраняется, edit получает default WKT;
4. feeder/default имеют разные допустимые трёхвершинные WKT, edit имеет две вершины → edit получает default WKT;
5. все три copies имеют разные трёхвершинные `3A/3B/3C` geometries, а edit может иметь `operation=updated` → zero-write no-op с полным сохранением coordinates;
6. fresh feeder/default имеют три вершины, а edit versions ещё не существуют → valid zero-write no-op.

Ключевые assertions:

```python
result = await service.upgrade_demo_fixture()

assert result.updated_copy_count == 3
assert repository.updates == (
    DemoFixtureGeometryUpdate(
        source=DemoFixtureCopySource.FEEDER,
        owner_id=FEEDER_ID,
        geometry_wkt=UTILITY_EDITABLE_LINE_SPEC.geometry_wkt,
    ),
    DemoFixtureGeometryUpdate(
        source=DemoFixtureCopySource.DEFAULT_STATE,
        owner_id=DEFAULT_STATE_ID,
        geometry_wkt=UTILITY_EDITABLE_LINE_SPEC.geometry_wkt,
    ),
    DemoFixtureGeometryUpdate(
        source=DemoFixtureCopySource.EDIT_VERSION,
        owner_id=EDIT_VERSION_ID,
        geometry_wkt=UTILITY_EDITABLE_LINE_SPEC.geometry_wkt,
    ),
)
```

- [ ] **Step 2: Запустить новый test module и подтвердить red state**

```powershell
python -m pytest seeds/tests/test_demo_fixture_upgrade_service.py -q
```

Expected: collection FAIL, потому что contracts и service ещё не существуют.

- [ ] **Step 3: Ввести immutable contracts**

В `demo_fixture_upgrade.py` определить:

```python
class DemoFixtureCopySource(str, enum.Enum):
    FEEDER = "feeder"
    DEFAULT_STATE = "default_state"
    EDIT_VERSION = "edit_version"


class DemoFixtureUpgradeError(RuntimeError):
    pass


@dataclass(frozen=True)
class DemoFixtureFeatureSnapshot:
    owner_id: UUID
    geometry_wkt: str
    geometry_type: str
    vertex_count: int
    network_version: int
    operation: EditVersionOperationState | None = None


@dataclass(frozen=True)
class DemoFixtureEditVersionSnapshot:
    edit_version_id: UUID
    default_state_id: UUID
    feature: DemoFixtureFeatureSnapshot | None


@dataclass(frozen=True)
class DemoFixtureHierarchy:
    feeder_id: UUID | None
    feeder_feature: DemoFixtureFeatureSnapshot | None
    work_order_id: UUID | None
    default_state_id: UUID | None
    default_feature: DemoFixtureFeatureSnapshot | None
    edit_versions: tuple[DemoFixtureEditVersionSnapshot, ...]


@dataclass(frozen=True)
class DemoFixtureGeometryUpdate:
    source: DemoFixtureCopySource
    owner_id: UUID
    geometry_wkt: str


@dataclass(frozen=True)
class DemoFixtureUpgradeResult:
    updates: tuple[DemoFixtureGeometryUpdate, ...]

    @property
    def updated_copy_count(self) -> int:
        return len(self.updates)

    @property
    def updated_sources(self) -> tuple[DemoFixtureCopySource, ...]:
        return tuple(update.source for update in self.updates)
```

Экспортировать public contracts из `contracts/__init__.py`.

- [ ] **Step 4: Реализовать service через repository port**

В `demo_fixture_upgrade_service.py` определить `DemoFixtureUpgradeRepositoryPort` и
`DemoFixtureUpgradeService`. `DemoFixtureUpgradeError` импортировать из contracts,
чтобы service и repository не зависели друг от друга. Service не знает ORM models и
PostGIS functions; `AsyncSession` используется только как transaction boundary:

```python
class DemoFixtureUpgradeRepositoryPort(Protocol):
    async def load_hierarchy_for_update(self) -> DemoFixtureHierarchy: ...

    async def update_geometry(
        self,
        update: DemoFixtureGeometryUpdate,
    ) -> None: ...


class DemoFixtureUpgradeService:
    def __init__(
        self,
        session: AsyncSession,
        repository: DemoFixtureUpgradeRepositoryPort,
    ) -> None:
        self._session = session
        self._repository = repository

    async def upgrade_demo_fixture(self) -> DemoFixtureUpgradeResult:
        async with self._session.begin():
            hierarchy = await self._repository.load_hierarchy_for_update()
            updates = self._plan_updates(hierarchy)
            for update in updates:
                await self._repository.update_geometry(update)
        return DemoFixtureUpgradeResult(updates=updates)
```

`_plan_updates()` обязан сначала построить полный immutable tuple, и только после успешной валидации всех копий service начинает writes. Для happy path использовать exact `UTILITY_EDITABLE_LINE_SPEC.geometry_wkt` как feeder target, а затем каскад `feeder target → default target → edit target`.

- [ ] **Step 5: Запустить happy-path tests и review checkpoint**

```powershell
python -m pytest seeds/tests/test_demo_fixture_upgrade_service.py -q
python -m ruff check seeds/contracts seeds/services/demo_fixture_upgrade_service.py seeds/tests/test_demo_fixture_upgrade_service.py
python -m black --check seeds/contracts seeds/services/demo_fixture_upgrade_service.py seeds/tests/test_demo_fixture_upgrade_service.py
git diff --check
git status --short
```

Expected: шесть happy-path сценариев PASS; изменения остаются unstaged.

### Task 4: Validation, Validate-First Semantics, and Rollback

**Files:**

- Modify: `apps/backend/seeds/services/demo_fixture_upgrade_service.py`
- Modify: `apps/backend/seeds/tests/test_demo_fixture_upgrade_service.py`

- [ ] **Step 1: Добавить параметризованные guard tests**

Проверить, что service выбрасывает `DemoFixtureUpgradeError` и не вызывает `update_geometry()` для каждого состояния:

| Состояние | Ожидаемый результат |
|---|---|
| feeder/work order/default state отсутствует | fail closed |
| feeder/default materialized copy либо copy существующего edit version отсутствует | fail closed |
| `EditVersion.default_state_id` не совпадает с `WO-001 DefaultState.id` | fail closed |
| geometry type не `LINESTRING` | fail closed |
| любая копия имеет 0, 1 или 4+ vertices | fail closed |
| двухвершинный edit имеет `created`, `updated` или `deleted` operation | fail closed |

Пример критичного regression test:

```python
def test_rejects_changed_two_vertex_edit_before_any_write() -> None:
    repository = FakeRepository(
        hierarchy=hierarchy(
            feeder=feature(FEEDER_ID, OLD_TWO_VERTEX_WKT, 2),
            default=feature(DEFAULT_STATE_ID, OLD_TWO_VERTEX_WKT, 2),
            edits=(
                edit_feature(
                    EDIT_VERSION_ID,
                    OLD_TWO_VERTEX_WKT,
                    2,
                    operation=EditVersionOperationState.UPDATED,
                ),
            ),
        )
    )

    with pytest.raises(DemoFixtureUpgradeError, match="operation"):
        asyncio.run(service_for(repository).upgrade_demo_fixture())

    assert repository.updates == ()
```

- [ ] **Step 2: Запустить guard tests и подтвердить red state**

```powershell
python -m pytest seeds/tests/test_demo_fixture_upgrade_service.py -q
```

Expected: новые guard tests FAIL.

- [ ] **Step 3: Реализовать явные validation helpers**

Разделить `_plan_updates()` на небольшие pure helpers:

```python
def _require_hierarchy(
    hierarchy: DemoFixtureHierarchy,
) -> tuple[
    DemoFixtureFeatureSnapshot,
    DemoFixtureFeatureSnapshot,
    tuple[DemoFixtureEditVersionSnapshot, ...],
]:
    ...


def _validate_copy(
    snapshot: DemoFixtureFeatureSnapshot,
    source: DemoFixtureCopySource,
) -> None:
    if snapshot.geometry_type.upper() != "LINESTRING":
        raise DemoFixtureUpgradeError(...)
    if snapshot.vertex_count not in {2, 3}:
        raise DemoFixtureUpgradeError(...)


def _target_wkt(
    snapshot: DemoFixtureFeatureSnapshot,
    fallback_wkt: str,
) -> str:
    return fallback_wkt if snapshot.vertex_count == 2 else snapshot.geometry_wkt
```

Дополнительные invariants:

- двухвершинный edit допустим только при `operation is EditVersionOperationState.UNCHANGED`;
- трёхвершинная копия всегда сохраняет собственную geometry, даже если она отличается от seed;
- при двух вершинах меняется только geometry текущей materialized copy;
- порядок planned updates детерминирован: feeder, default state, edit versions по `edit_version_id`;
- error message содержит asset code `L-003`, source и owner id, но не зависит от текста SQL exception.

- [ ] **Step 4: Проверить rollback при ошибке write**

Расширить fake session/repository так, чтобы второй `update_geometry()` выбрасывал исключение. Assert:

```python
with pytest.raises(RuntimeError, match="synthetic write failure"):
    await service.upgrade_demo_fixture()

assert fake_session.transaction_started is True
assert fake_session.transaction_committed is False
assert fake_session.transaction_rolled_back is True
```

Этот unit test доказывает orchestration. Фактическую атомарность PostgreSQL проверить отдельно в Task 5.

- [ ] **Step 5: Запустить весь service test module**

```powershell
python -m pytest seeds/tests/test_demo_fixture_upgrade_service.py -q
python -m ruff check seeds/services/demo_fixture_upgrade_service.py seeds/tests/test_demo_fixture_upgrade_service.py
python -m black --check seeds/services/demo_fixture_upgrade_service.py seeds/tests/test_demo_fixture_upgrade_service.py
git diff --check
```

Expected: happy-path, guard и transaction-orchestration tests PASS.

### Task 5: PostgreSQL/PostGIS Upgrade Repository

**Files:**

- Create: `apps/backend/seeds/repositories/demo_fixture_upgrade_repository.py`
- Create: `apps/backend/tests/integration_tests/test_demo_fixture_upgrade_integration.py`
- Reference: `apps/backend/tests/integration_tests/network_db_support.py`
- Reference: `apps/backend/tests/integration_tests/test_work_order_seed_chain_integration.py`

- [ ] **Step 1: Написать integration test для upgrade и idempotency**

Сначала добавить rollback-isolated fresh-start scenario: запустить user → utility
dataset → work order seed chain без создания edit version, затем запустить upgrade.
Ожидать zero-write result, трёхвершинные feeder/default copies и counts `19/9`.

Во втором rollback-isolated scenario:

1. удалить canonical seed chain существующим helper pattern;
2. запустить user → utility dataset → work order seed chain;
3. открыть edit version через `EditVersionService`;
4. заменить geometry `L-003` во всех трёх materialized copies на старый двухвершинный WKT;
5. сохранить snapshots feature ids, `properties`, `version/network_version`,
   `operation` и `NetworkState.current_revision`;
6. запустить `DemoFixtureUpgradeService` с реальным repository;
7. проверить `ST_NPoints = 3` для feeder/default/edit, cascade geometry и неизменность snapshots;
8. запустить service второй раз и проверить `updated_copy_count == 0`.

Запрос для проверки geometry должен использовать PostGIS на стороне DB:

```python
select(
    func.ST_AsText(EditVersionFeature.geometry),
    func.ST_NPoints(EditVersionFeature.geometry),
).where(
    EditVersionFeature.edit_version_id == edit_version_id,
    EditVersionFeature.asset_code == UTILITY_EDITABLE_LINE_ASSET_CODE,
)
```

Сравнивать geometry через `ST_Equals` или coordinate tuples, а не через буквальный
формат `ST_AsText`: PostGIS вправе убрать незначащие нули из WKT.

- [ ] **Step 2: Написать integration tests для validate-first и реального rollback**

Первый test после создания той же цепочки выставляет:

- feeder `L-003`: 2 vertices;
- default `L-003`: 2 vertices;
- edit `L-003`: 2 vertices и `operation=updated`.

Service должен поднять `DemoFixtureUpgradeError` до первого write. После rollback все три WKT остаются двухвершинными, operation остаётся `updated`. Дополнительно проверить counts `19 features / 9 associations` в feeder, default state и edit version slices.

Второй test использует `FailOnSecondUpdateRepository` — тонкий wrapper над реальным
repository. Первый geometry update делегируется в PostgreSQL, перед вторым wrapper
выбрасывает `RuntimeError("synthetic write failure")`. После выхода service transaction
первый update обязан быть откачен: `ST_NPoints` остаётся `2/2/2`. Так проверяется
не только validate-first, но и атомарность при технической ошибке посередине writes.

- [ ] **Step 3: Запустить DB tests и подтвердить red state**

```powershell
$env:RUN_DB_TESTS = "1"
$env:DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/geo"
python -m pytest tests/integration_tests/test_demo_fixture_upgrade_integration.py -q
```

Expected: FAIL, repository ещё не существует. Если локальная PostGIS DB не запущена, зафиксировать infrastructure blocker и всё равно выполнить unit/static verification.

- [ ] **Step 4: Реализовать deterministic locked reads**

`DemoFixtureUpgradeRepository` импортирует `DemoFixtureUpgradeError` только из
`seeds.contracts`. `load_hierarchy_for_update()` выполняет отдельные ordered
`select(...).with_for_update()`:

1. `Feeder` по `UTILITY_FEEDER_CODE`;
2. `NetworkFeature` по `feeder_id + L-003`;
3. `WorkOrder` по `SEED_WORK_ORDER_SPEC.code`;
4. `DefaultState` по `work_order_id`;
5. `DefaultStateFeature` по `default_state_id + L-003`;
6. все `EditVersion.id + EditVersion.default_state_id` по `work_order_id` с `order_by(EditVersion.id)`;
7. `EditVersionFeature` для каждого edit version по `edit_version_id + L-003`.

Для feature snapshot выбирать SQL expressions:

```python
func.ST_AsText(Model.geometry).label("geometry_wkt"),
func.GeometryType(Model.geometry).label("geometry_type"),
func.ST_NPoints(Model.geometry).label("vertex_count"),
```

Для `NetworkFeature.version` вернуть generic поле `network_version`; для default/edit
использовать одноимённую колонку. В edit snapshot дополнительно выбрать
`EditVersionFeature.operation`. Отсутствующие hierarchy nodes и materialized copies
вернуть как `None`, чтобы service сформировал единообразную domain error. Repository
не выполняет commit и не подменяет missing rows.

- [ ] **Step 5: Реализовать geometry-only updates**

Маппинг target table:

| Source | Model | Owner predicate |
|---|---|---|
| `FEEDER` | `NetworkFeature` | `feeder_id == owner_id` |
| `DEFAULT_STATE` | `DefaultStateFeature` | `default_state_id == owner_id` |
| `EDIT_VERSION` | `EditVersionFeature` | `edit_version_id == owner_id` |

Каждый `update_geometry()`:

```python
statement = (
    update(model)
    .where(
        owner_column == update_request.owner_id,
        model.asset_code == UTILITY_EDITABLE_LINE_ASSET_CODE,
    )
    .values(geometry=WKTElement(update_request.geometry_wkt, srid=4326))
)
result = await self._session.execute(statement)
if result.rowcount != 1:
    raise DemoFixtureUpgradeError(...)
```

Не передавать в `values()` `properties`, `version`, `network_version` или `operation`. `updated_at` у `NetworkFeature` может измениться как технический timestamp; это не semantic version bump.

- [ ] **Step 6: Запустить integration и static tests**

```powershell
$env:RUN_DB_TESTS = "1"
python -m pytest tests/integration_tests/test_demo_fixture_upgrade_integration.py -q
python -m pytest seeds/tests/test_demo_fixture_upgrade_service.py -q
python -m ruff check seeds/repositories/demo_fixture_upgrade_repository.py tests/integration_tests/test_demo_fixture_upgrade_integration.py
python -m black --check seeds/repositories/demo_fixture_upgrade_repository.py tests/integration_tests/test_demo_fixture_upgrade_integration.py
git diff --check
git status --short
```

Expected: idempotency, preservation и real rollback PASS; counts остаются `19/9`.

### Task 6: Runner and Demo Startup Wiring

**Files:**

- Create: `apps/backend/seeds/runners/upgrade_demo_fixture.py`
- Modify: `apps/backend/seeds/services/demo_fixture_upgrade_service.py`
- Modify: `apps/backend/scripts/start_utility_service.sh`
- Modify: `apps/backend/tests/test_compose_startup_contract.py`
- Verify unchanged: `apps/backend/scripts/start_api.sh`
- Verify unchanged: `infra/dev-up.cmd`

- [ ] **Step 1: Расширить startup contract test**

Переименовать seed-only constant в `DEMO_STARTUP_STEPS` и включить upgrade:

```python
DEMO_STARTUP_STEPS = (
    "alembic upgrade head",
    "python -m seeds.runners.seed_demo_users",
    "python -m seeds.runners.seed_utility_dataset",
    "python -m seeds.runners.seed_work_orders",
    "python -m seeds.runners.upgrade_demo_fixture",
)
```

Assertions:

- позиции строго возрастают;
- upgrade находится после work-order seed и до uvicorn;
- `scripts/start_api.sh` не содержит ни один demo startup step;
- `infra/dev-up.cmd` не содержит `python` и `down -v`/`down --volumes`.

Для CMD contract определить `REPO_ROOT = BACKEND_ROOT.parents[1]` и читать
`REPO_ROOT / "infra" / "dev-up.cmd"` в UTF-8; assertions выполнять на
`text.lower()`, чтобы не зависеть от регистра command.

- [ ] **Step 2: Запустить contract test и подтвердить red state**

```powershell
python -m pytest tests/test_compose_startup_contract.py -q
```

Expected: demo startup ordering test FAIL.

- [ ] **Step 3: Добавить application runner**

В `demo_fixture_upgrade_service.py` определить module logger через
`logging.getLogger(__name__)`, затем добавить production wiring, повторяя существующий
seed pattern. Repository импортировать локально, чтобы contracts, service и repository
не образовали import cycle:

```python
async def run_upgrade_demo_fixture() -> DemoFixtureUpgradeResult:
    from seeds.repositories.demo_fixture_upgrade_repository import (
        DemoFixtureUpgradeRepository,
    )
    from utility_service.infrastructure.postgresql.session import SessionFactory

    async with SessionFactory() as session:
        service = DemoFixtureUpgradeService(
            session,
            DemoFixtureUpgradeRepository(session),
        )
        result = await service.upgrade_demo_fixture()
        logger.info(
            "Demo fixture upgrade завершён.",
            extra={
                "updated_copy_count": result.updated_copy_count,
                "updated_sources": [
                    source.value for source in result.updated_sources
                ],
            },
        )
        return result
```

Runner остаётся Python-module entry point внутри container:

```python
import asyncio

from seeds.services.demo_fixture_upgrade_service import run_upgrade_demo_fixture


if __name__ == "__main__":
    asyncio.run(run_upgrade_demo_fixture())
```

`run_upgrade_demo_fixture()` пишет один `INFO` log с `updated_copy_count` и
`updated_sources`; error не проглатывается и сохраняет non-zero process exit.

Это не добавляет зависимости от host Python: `dev-up.cmd` продолжает только управлять Docker Compose.

- [ ] **Step 4: Встроить upgrade только в demo startup**

В `start_utility_service.sh` получить порядок:

```bash
set -euo pipefail

alembic upgrade head
python -m seeds.runners.seed_demo_users
python -m seeds.runners.seed_utility_dataset
python -m seeds.runners.seed_work_orders
python -m seeds.runners.upgrade_demo_fixture
uvicorn utility_service.web_api.main:app --host 0.0.0.0 --port 8000
```

Не менять `start_api.sh` и production Compose command. Ошибка upgrade должна остановить demo container до запуска API благодаря `set -e`.

- [ ] **Step 5: Запустить startup и import verification**

```powershell
python -m pytest tests/test_compose_startup_contract.py tests/test_compose_security_contract.py -q
python -c "from seeds.runners import upgrade_demo_fixture; from seeds.services.demo_fixture_upgrade_service import run_upgrade_demo_fixture"
python -m ruff check seeds/runners/upgrade_demo_fixture.py seeds/services/demo_fixture_upgrade_service.py tests/test_compose_startup_contract.py
python -m black --check seeds/runners/upgrade_demo_fixture.py seeds/services/demo_fixture_upgrade_service.py tests/test_compose_startup_contract.py
git diff --check
git status --short
```

Expected: startup contracts PASS; production path не запускает demo mutation; no host-Python command добавлен в CMD.

### Task 7: Synchronize Sprint and Demo Documentation

**Files:**

- Modify: `README.md`
- Modify: `docs/sprint_2/2026-07-31-sprint-2-calendar-plan.md`
- Modify: `docs/sprint_2/2026-07-31-sprint-2-technical-requirements.md`
- Reference: `docs/superpowers/specs/2026-08-03-sprint-2-day-1-coordinate-grid-demo-fixture-design.md`

- [ ] **Step 1: Обновить README без смешения двух видов cleanup**

После demo startup command описать нормальный путь:

- fresh volume получает трёхвершинную `L-003` из create-once seed;
- существующий совместимый volume проходит автоматический transactional in-place upgrade;
- уже трёхвершинные geometry сохраняются;
- unsafe state блокирует demo API startup с ошибкой;
- manual `down -v` — fallback для disposable demo data, а не обязательный штатный шаг.

Существующее предупреждение о несовместимом Alembic baseline и volume с другим Postgres password оставить: это отдельные инфраструктурные случаи, где destructive cleanup по-прежнему может требоваться.

- [ ] **Step 2: Исправить Day 1 и условия старта календаря**

В Day 1 заменить обязательный full-clean на:

```markdown
- После create-once seed chain атомарно обновлять только безопасные
  двухвершинные materialized-копии `L-003`; unsafe state блокирует demo startup.
```

В `Условия старта` сделать automatic in-place upgrade основным путём, а exact `docker compose ... down -v` перенести в явно ручной fallback для disposable demo volume. Проверку дня расширить: settings tests, seed specification tests, service tests, startup contract и DB integration.

- [ ] **Step 3: Синхронизировать технические требования**

Обновить четыре участка:

1. `Demo data` — описать feeder/default/edit propagation matrix и validate-first transaction;
2. `AC-02` — fresh и существующий совместимый volume приводят materialized copies к пригодной линии без изменения `19/9`;
3. `Definition of Done` — добавить upgrade idempotency/rollback/startup-order tests;
4. risk `Старый volume скрывает новую fixture` — основная защита atomic fixture upgrade, manual full-clean только fallback.

Явно записать fail-closed cases: missing copy, wrong geometry type, 4+ vertices, changed two-vertex edit. Не обещать восстановление пользовательской двухвершинной edit geometry: такая запись считается ambiguous и не перезаписывается.

В правилах координатной сетки сохранить distinction между configuration этого дня и
будущим canonicalizer. Добавить midpoint examples для resolution `0.0000001`:
`+0.00000015 → +0.0000002` и `-0.00000015 → -0.0000002`. Это иллюстрирует
`ROUND_HALF_AWAY_FROM_ZERO`: точная половина всегда округляется от нуля; сам
canonicalization algorithm остаётся вне Day 1.

- [ ] **Step 4: Проверить согласованность терминов и команд**

```powershell
rg -n "обязательный.*full-clean|После fresh .*full-clean|требуется destructive" README.md docs/sprint_2
rg -n "ROUND_HALF_AWAY_FROM_ZERO|0\\.0000001|19 features|9 associations|L-003|upgrade_demo_fixture" README.md docs/sprint_2
git diff --check
git status --short
```

Expected: обязательный fixture full-clean больше нигде не заявлен; инфраструктурный/manual fallback остаётся явно помеченным.

- [ ] **Step 5: Решить вопрос durable knowledge**

Сверить итоговые изменения с design spec и sprint docs. Не запускать `/ingest repository-change` и не обновлять agent memory, если новое устойчивое знание уже полностью сохранено в этих документах. Если в ходе реализации обнаружен отдельный неочевидный architectural fact, сначала проверить существующий `Code_wiki` node и только затем решить, нужен ли отдельный ingest.

### Task 8: Full Verification and Unstaged Handoff

**Files:**

- Verify: все файлы из `File Structure`
- Do not modify: `apps/backend/scripts/start_api.sh`
- Do not modify: `infra/dev-up.cmd`

- [ ] **Step 1: Запустить обязательный focused suite**

Из `apps/backend`:

```powershell
python -m pytest utility_service/utils/tests/test_settings.py -q
python -m pytest seeds/tests/test_seed_utility_dataset_specs.py seeds/tests/test_seed_utility_dataset_service.py -q
python -m pytest seeds/tests/test_demo_fixture_upgrade_service.py -q
python -m pytest tests/test_compose_security_contract.py tests/test_compose_startup_contract.py -q
```

Expected: все settings/seed/service/startup contracts PASS.

- [ ] **Step 2: Запустить PostgreSQL/PostGIS proof**

При поднятом local PostGIS:

```powershell
$env:RUN_DB_TESTS = "1"
$env:DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/geo"
python -m pytest tests/integration_tests/test_demo_fixture_upgrade_integration.py tests/integration_tests/test_seed_utility_dataset_integration.py tests/integration_tests/test_work_order_seed_chain_integration.py -q
```

Expected: fresh seed, in-place upgrade, idempotency, preservation и unsafe rollback PASS. В отчёте отдельно указать, если test не был выполнен из-за недоступной DB; skipped test не считать доказательством.

- [ ] **Step 3: Запустить полный backend suite и static checks**

```powershell
Remove-Item Env:RUN_DB_TESTS -ErrorAction SilentlyContinue
python -m pytest
python -m ruff check .
python -m black --check .
```

Expected: PASS без новых warnings/errors.

- [ ] **Step 4: Проверить Compose resolution без удаления volume**

Из repository root:

```powershell
docker compose --env-file infra/demo.env -f infra/docker-compose.yml -f infra/docker-compose.demo.yml --profile dev config
```

Проверить в resolved environment defaults:

- `UTILITY_GEOMETRY_XY_RESOLUTION=0.0000001`;
- `UTILITY_GEOMETRY_ROUNDING_MODE=ROUND_HALF_AWAY_FROM_ZERO`;
- demo command использует `start_utility_service.sh`;
- production command остаётся `start_api.sh`.

Не выполнять `down -v` как часть штатной проверки.

- [ ] **Step 5: Выполнить финальный acceptance audit**

```powershell
rg -n "UTILITY_GEOMETRY_XY_RESOLUTION|UTILITY_GEOMETRY_ROUNDING_MODE|ROUND_HALF_AWAY_FROM_ZERO" apps/backend infra
rg -n "LINESTRING \(65\.520 44\.820, 65\.525 44\.8205, 65\.530 44\.820\)" apps/backend/seeds docs
rg -n "upgrade_demo_fixture" apps/backend/scripts apps/backend/tests
git diff --check
git diff --stat
git status --short
```

Подтвердить по diff и test evidence:

- fresh counts остаются ровно `19 features / 9 associations`;
- ровно одна seed line структурно eligible;
- midpoint L-003 редактируема и не совпадает с junction/device;
- safe двухвершинные feeder/default/unchanged-edit copies обновляются in place;
- трёхвершинные copies и semantic metadata сохраняются;
- unsafe state не оставляет partial writes и блокирует demo startup;
- CMD не зависит от host Python и не удаляет volume;
- production startup не выполняет demo upgrade.

- [ ] **Step 6: Передать изменения пользователю unstaged**

В итоговом сообщении перечислить:

- реализованные contracts и startup behavior;
- фактически выполненные команды и их результаты;
- DB/Compose проверки, которые не удалось выполнить, если такие есть;
- все изменённые/новые файлы для review;
- отсутствие staging/commit/push согласно `AGENTS.md`.

Не выполнять `git add`, `git commit` или `git push`.
