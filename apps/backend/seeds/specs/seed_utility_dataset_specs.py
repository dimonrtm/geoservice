from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from utility_service.infrastructure.postgresql.models.utility_network import (
    AssociationType,
    FeatureType,
)


UTILITY_FEEDER_ID = UUID("6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0101")
UTILITY_FEEDER_CODE = "synthetic_utility_feeder_01"


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
    feeder: SeedFeederSpec
    features: tuple[SeedNetworkFeatureSpec, ...]
    associations: tuple[SeedNetworkAssociationSpec, ...]


def stable_uuid(suffix: str) -> UUID:
    return UUID(f"6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f{suffix}")


UTILITY_FEATURE_SPECS: tuple[SeedNetworkFeatureSpec, ...] = (
    SeedNetworkFeatureSpec(
        id=stable_uuid("0201"),
        asset_code="J-001",
        feature_type=FeatureType.JUNCTION,
        geometry_wkt="POINT (65.500 44.820)",
        name="Шина подстанции",
        description="Начальная точка демонстрационного фидера.",
        properties={"junctionType": "busbar"},
    ),
    SeedNetworkFeatureSpec(
        id=stable_uuid("0202"),
        asset_code="J-002",
        feature_type=FeatureType.JUNCTION,
        geometry_wkt="POINT (65.510 44.820)",
        name="Промежуточный узел 1",
        description="Узел основного участка фидера.",
        properties={"junctionType": "junction"},
    ),
    SeedNetworkFeatureSpec(
        id=stable_uuid("0203"),
        asset_code="J-003",
        feature_type=FeatureType.JUNCTION,
        geometry_wkt="POINT (65.520 44.820)",
        name="Узел секционного выключателя",
        description="Точка установки SW-01 и начала tie branch.",
        properties={"junctionType": "switch_node"},
    ),
    SeedNetworkFeatureSpec(
        id=stable_uuid("0204"),
        asset_code="J-004",
        feature_type=FeatureType.JUNCTION,
        geometry_wkt="POINT (65.530 44.820)",
        name="Узел ответвления",
        description="Ответвление к трансформаторному участку.",
        properties={"junctionType": "branch"},
    ),
    SeedNetworkFeatureSpec(
        id=stable_uuid("0205"),
        asset_code="J-005",
        feature_type=FeatureType.JUNCTION,
        geometry_wkt="POINT (65.535 44.812)",
        name="Отвод трансформатора",
        description="Точка подключения TX-01.",
        properties={"junctionType": "transformer_tap"},
    ),
    SeedNetworkFeatureSpec(
        id=stable_uuid("0206"),
        asset_code="J-006",
        feature_type=FeatureType.JUNCTION,
        geometry_wkt="POINT (65.540 44.805)",
        name="Точка потребителя",
        description="Конечная точка низковольтного участка.",
        properties={"junctionType": "service_point"},
    ),
    SeedNetworkFeatureSpec(
        id=stable_uuid("0207"),
        asset_code="J-007",
        feature_type=FeatureType.JUNCTION,
        geometry_wkt="POINT (65.525 44.830)",
        name="Точка tie switch",
        description="Точка normally-open связи.",
        properties={"junctionType": "tie_point"},
    ),
    SeedNetworkFeatureSpec(
        id=stable_uuid("0211"),
        asset_code="L-001",
        feature_type=FeatureType.LINE,
        geometry_wkt="LINESTRING (65.500 44.820, 65.510 44.820)",
        name="Основная линия 1",
        description="Участок J-001 -> J-002.",
        properties={"status": "in_service", "voltageKv": 10.0},
    ),
    SeedNetworkFeatureSpec(
        id=stable_uuid("0212"),
        asset_code="L-002",
        feature_type=FeatureType.LINE,
        geometry_wkt="LINESTRING (65.510 44.820, 65.520 44.820)",
        name="Основная линия 2",
        description="Участок J-002 -> J-003.",
        properties={"status": "in_service", "voltageKv": 10.0},
    ),
    SeedNetworkFeatureSpec(
        id=stable_uuid("0213"),
        asset_code="L-003",
        feature_type=FeatureType.LINE,
        geometry_wkt="LINESTRING (65.520 44.820, 65.530 44.820)",
        name="Основная линия 3",
        description="Участок J-003 -> J-004.",
        properties={"status": "in_service", "voltageKv": 10.0},
    ),
    SeedNetworkFeatureSpec(
        id=stable_uuid("0214"),
        asset_code="L-004",
        feature_type=FeatureType.LINE,
        geometry_wkt="LINESTRING (65.530 44.820, 65.535 44.812)",
        name="Отвод к трансформатору",
        description="Участок J-004 -> J-005.",
        properties={"status": "in_service", "voltageKv": 10.0},
    ),
    SeedNetworkFeatureSpec(
        id=stable_uuid("0215"),
        asset_code="L-005",
        feature_type=FeatureType.LINE,
        geometry_wkt="LINESTRING (65.535 44.812, 65.540 44.805)",
        name="Линия к потребителю",
        description="Низковольтный участок J-005 -> J-006.",
        properties={"status": "in_service", "voltageKv": 0.4},
    ),
    SeedNetworkFeatureSpec(
        id=stable_uuid("0216"),
        asset_code="L-006",
        feature_type=FeatureType.LINE,
        geometry_wkt="LINESTRING (65.520 44.820, 65.525 44.830)",
        name="Tie line",
        description="Normally-open ветвь J-003 -> J-007.",
        properties={"status": "in_service", "voltageKv": 10.0},
    ),
    SeedNetworkFeatureSpec(
        id=stable_uuid("0221"),
        asset_code="D-001",
        feature_type=FeatureType.DEVICE,
        geometry_wkt="POINT (65.500 44.820)",
        name="Выключатель BR-01",
        description="Головной выключатель фидера.",
        properties={
            "deviceType": "breaker",
            "status": "closed",
            "normalState": "closed",
        },
    ),
    SeedNetworkFeatureSpec(
        id=stable_uuid("0222"),
        asset_code="D-002",
        feature_type=FeatureType.DEVICE,
        geometry_wkt="POINT (65.520 44.820)",
        name="Секционный выключатель SW-01",
        description="Устройство будущего work order WO-001.",
        properties={
            "deviceType": "switch",
            "status": "closed",
            "normalState": "closed",
        },
    ),
    SeedNetworkFeatureSpec(
        id=stable_uuid("0223"),
        asset_code="D-003",
        feature_type=FeatureType.DEVICE,
        geometry_wkt="POINT (65.530 44.820)",
        name="Предохранитель FU-01",
        description="Защита трансформаторного ответвления.",
        properties={
            "deviceType": "fuse",
            "status": "closed",
            "normalState": "closed",
        },
    ),
    SeedNetworkFeatureSpec(
        id=stable_uuid("0224"),
        asset_code="D-004",
        feature_type=FeatureType.DEVICE,
        geometry_wkt="POINT (65.535 44.812)",
        name="Трансформатор TX-01",
        description="Переход с 10 кВ на 0.4 кВ.",
        properties={
            "deviceType": "transformer",
            "status": "in_service",
            "normalState": "in_service",
        },
    ),
    SeedNetworkFeatureSpec(
        id=stable_uuid("0225"),
        asset_code="D-005",
        feature_type=FeatureType.DEVICE,
        geometry_wkt="POINT (65.525 44.830)",
        name="Tie switch SW-TIE-01",
        description="Normally-open tie switch.",
        properties={
            "deviceType": "switch",
            "status": "open",
            "normalState": "open",
        },
    ),
    SeedNetworkFeatureSpec(
        id=stable_uuid("0226"),
        asset_code="D-006",
        feature_type=FeatureType.DEVICE,
        geometry_wkt="POINT (65.540 44.805)",
        name="Счетчик M-01",
        description="Учетная точка потребителя.",
        properties={
            "deviceType": "meter",
            "status": "active",
            "normalState": "active",
        },
    ),
)


ASSOCIATION_EDGES = (
    ("0301", "0221", "0211"),
    ("0302", "0222", "0212"),
    ("0303", "0222", "0213"),
    ("0304", "0223", "0213"),
    ("0305", "0223", "0214"),
    ("0306", "0224", "0214"),
    ("0307", "0224", "0215"),
    ("0308", "0225", "0216"),
    ("0309", "0224", "0226"),
)


UTILITY_DATASET_SPEC = SeedUtilityDatasetSpec(
    feeder=SeedFeederSpec(
        id=UTILITY_FEEDER_ID,
        code=UTILITY_FEEDER_CODE,
        name="Демонстрационный фидер 10 кВ",
        description="Малый synthetic feeder для Utility GIS workflow.",
    ),
    features=UTILITY_FEATURE_SPECS,
    associations=tuple(
        SeedNetworkAssociationSpec(
            id=stable_uuid(association_id),
            from_feature_id=stable_uuid(from_feature_id),
            to_feature_id=stable_uuid(to_feature_id),
        )
        for association_id, from_feature_id, to_feature_id in ASSOCIATION_EDGES
    ),
)
