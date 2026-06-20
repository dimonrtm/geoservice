from dataclasses import dataclass
from uuid import UUID

from utility_service.infrastructure.postgresql.models.work_order import WorkOrderStatus
from seeds.specs.seed_utility_dataset_specs import UTILITY_FEEDER_CODE


@dataclass(frozen=True)
class SeedWorkOrderSpec:
    id: UUID
    code: str
    title: str
    description: str
    status: WorkOrderStatus
    assignee_email: str
    feeder_code: str


SEED_WORK_ORDER_SPEC = SeedWorkOrderSpec(
    id=UUID("6c13a4d8-8d67-4fb3-a1f9-4ea5ab7f0401"),
    code="WO-001",
    title="Проверка участка фидера",
    description="Открыть рабочий участок для последующего редактирования.",
    status=WorkOrderStatus.ASSIGNED,
    assignee_email="alexey.editor@example.local",
    feeder_code=UTILITY_FEEDER_CODE,
)
