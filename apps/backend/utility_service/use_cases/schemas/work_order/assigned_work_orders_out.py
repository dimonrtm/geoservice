from pydantic import BaseModel, ConfigDict, Field

from utility_service.use_cases.schemas.work_order.work_order_summary_out import (
    WorkOrderSummaryOut,
)


class AssignedWorkOrdersOut(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    work_orders: list[WorkOrderSummaryOut] = Field(serialization_alias="workOrders")
