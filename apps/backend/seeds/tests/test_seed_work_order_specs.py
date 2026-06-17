from uuid import UUID

from utility_service.infrastructure.postgresql.models.utility_network import WorkOrderStatus
from seeds.specs.seed_utility_dataset_specs import UTILITY_FEEDER_CODE
from seeds.specs.seed_work_order_specs import SEED_WORK_ORDER_SPEC


def test_seed_work_order_spec_defines_stable_wo_001_assignment() -> None:
    assert SEED_WORK_ORDER_SPEC.id == UUID("6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0401")
    assert SEED_WORK_ORDER_SPEC.code == "WO-001"
    assert SEED_WORK_ORDER_SPEC.status is WorkOrderStatus.ASSIGNED
    assert SEED_WORK_ORDER_SPEC.assignee_email == "alexey.editor@example.local"
    assert SEED_WORK_ORDER_SPEC.feeder_code == UTILITY_FEEDER_CODE
    assert SEED_WORK_ORDER_SPEC.title == "Проверка участка фидера"
    assert SEED_WORK_ORDER_SPEC.description
