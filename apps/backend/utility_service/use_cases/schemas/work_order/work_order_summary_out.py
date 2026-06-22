from uuid import UUID

from pydantic import BaseModel, ConfigDict


class WorkOrderSummaryOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    code: str
    title: str
    description: str | None
    status: str
